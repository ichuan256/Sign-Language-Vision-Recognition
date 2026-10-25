"""Reconstruct the installed hand-landmark TFLite graph in tf-keras, preserving weights.

No training or automatic model substitution. Outputs ROI pixel coordinates (63)
and hand presence (1), not word classes or world-coordinate landmarks.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path

import numpy as np

os.environ.setdefault('TF_USE_LEGACY_KERAS', '1')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
ROOT = Path(__file__).resolve().parents[3]


def conv_kernel(weights):
    """TFLite OHWI -> Keras HWIO."""
    if weights.ndim != 4:
        raise ValueError('Expected rank-4 convolution kernel')
    return weights.transpose(1, 2, 3, 0)


def depthwise_kernel(weights, channels, multiplier):
    """TFLite 1,H,W,(I*M) -> Keras H,W,I,M."""
    if weights.ndim != 4 or weights.shape[0] != 1 or weights.shape[-1] != channels*multiplier:
        raise ValueError('Invalid depthwise kernel shape')
    return weights[0].reshape(weights.shape[1], weights.shape[2], channels, multiplier)


def reconstruct(path):
    import tf_keras as keras
    from tensorflow.lite.python import schema_py_generated as schema
    model = schema.Model.GetRootAsModel(path.read_bytes(), 0)
    graph = model.Subgraphs(0)
    op_names = {v:k for k,v in vars(schema.BuiltinOperator).items() if k.isupper() and isinstance(v,int)}
    tensor_types = {schema.TensorType.FLOAT32:np.float32, schema.TensorType.FLOAT16:np.float16,
                    schema.TensorType.INT32:np.int32, schema.TensorType.INT64:np.int64}
    values = {}
    operators = Counter()
    def shape(index):
        return tuple(int(v) for v in graph.Tensors(index).ShapeAsNumpy())
    def const(index):
        if index in values:
            value = values[index]
            if not isinstance(value, np.ndarray):
                raise ValueError('Expected constant tensor')
            return value
        tensor = graph.Tensors(index)
        buffer = model.Buffers(tensor.Buffer())
        if buffer.DataLength() == 0:
            raise ValueError(f'Tensor {index} has no constant data')
        value = np.frombuffer(buffer.DataAsNumpy().tobytes(),dtype=tensor_types[tensor.Type()]).reshape(shape(index))
        values[index] = value
        return value
    def options(op, cls):
        result = cls()
        table = op.BuiltinOptions()
        result.Init(table.Bytes, table.Pos)
        return result
    def activate(x, code, name):
        if code == schema.ActivationFunctionType.NONE:
            return x
        if code == schema.ActivationFunctionType.RELU:
            return keras.layers.ReLU(name=name)(x)
        if code == schema.ActivationFunctionType.RELU6:
            return keras.layers.ReLU(max_value=6, name=name)(x)
        raise NotImplementedError('Unvalidated fused activation: '+str(code))
    input_index = int(graph.Inputs(0))
    inputs = keras.Input(shape=shape(input_index)[1:], name='roi_rgb')
    values[input_index] = inputs
    # Only dependencies of coordinates and presence; omit world/handedness heads.
    required = {int(graph.Outputs(i)) for i in (0,1)}
    selected = []
    for i in reversed(range(graph.OperatorsLength())):
        op = graph.Operators(i)
        if any(int(v) in required for v in op.OutputsAsNumpy()):
            required.update(int(v) for v in op.InputsAsNumpy() if v >= 0)
            selected.append(i)
    for i in reversed(selected):
        op = graph.Operators(i)
        code = model.OperatorCodes(op.OpcodeIndex())
        kind = op_names[max(code.BuiltinCode(),code.DeprecatedBuiltinCode())]
        indices = [int(v) for v in op.InputsAsNumpy()]
        out = int(op.Outputs(0))
        operators[kind] += 1
        name = f'op_{i:03d}'
        if kind == 'DEQUANTIZE':
            source_type = graph.Tensors(indices[0]).Type()
            if source_type != schema.TensorType.FLOAT16:
                raise NotImplementedError('Only validated FLOAT16 -> FLOAT32 constant dequantization is supported')
            values[out] = const(indices[0]).astype(np.float32)
            continue
        x = values[indices[0]]
        if kind in ('CONV_2D','DEPTHWISE_CONV_2D'):
            opt = options(op, schema.Conv2DOptions if kind=='CONV_2D' else schema.DepthwiseConv2DOptions)
            padding = {schema.Padding.SAME:'same',schema.Padding.VALID:'valid'}[opt.Padding()]
            kernel = const(indices[1])
            kwargs = dict(kernel_size=kernel.shape[1:3],strides=(opt.StrideH(),opt.StrideW()),
                          padding=padding,dilation_rate=(opt.DilationHFactor(),opt.DilationWFactor()),
                          use_bias=len(indices)>2 and indices[2]>=0,name=name)
            if kind == 'CONV_2D':
                layer = keras.layers.Conv2D(filters=kernel.shape[0],**kwargs)
                kernel = conv_kernel(kernel)
            else:
                layer = keras.layers.DepthwiseConv2D(depth_multiplier=opt.DepthMultiplier(),**kwargs)
                kernel = depthwise_kernel(kernel,int(x.shape[-1]),opt.DepthMultiplier())
            y = layer(x)
            weights = [kernel]
            if kwargs['use_bias']:
                weights.append(const(indices[2]))
            layer.set_weights(weights)
            y = activate(y,opt.FusedActivationFunction(),name+'_activation')
        elif kind == 'ADD':
            y = keras.layers.Add(name=name)([x,values[indices[1]]])
            y = activate(y,options(op,schema.AddOptions).FusedActivationFunction(),name+'_activation')
        elif kind == 'MAX_POOL_2D':
            opt = options(op,schema.Pool2DOptions)
            y = keras.layers.MaxPool2D(pool_size=(opt.FilterHeight(),opt.FilterWidth()),
                strides=(opt.StrideH(),opt.StrideW()),padding={schema.Padding.SAME:'same',schema.Padding.VALID:'valid'}[opt.Padding()],name=name)(x)
            y = activate(y,opt.FusedActivationFunction(),name+'_activation')
        elif kind == 'MEAN':
            if const(indices[1]).tolist() != [1,2]:
                raise NotImplementedError('Only spatial global average is supported')
            y = keras.layers.GlobalAveragePooling2D(keepdims=options(op,schema.ReducerOptions).KeepDims(),name=name)(x)
        elif kind == 'FULLY_CONNECTED':
            opt = options(op,schema.FullyConnectedOptions)
            if opt.KeepNumDims() or opt.WeightsFormat() != schema.FullyConnectedOptionsWeightsFormat.DEFAULT:
                raise NotImplementedError('Unvalidated fully-connected layout')
            if len(x.shape)>2:
                x = keras.layers.Flatten(name=name+'_flatten')(x)
            weights = const(indices[1])
            layer = keras.layers.Dense(weights.shape[0],use_bias=len(indices)>2 and indices[2]>=0,name=name)
            y = layer(x)
            layer.set_weights([weights.T]+([const(indices[2])] if layer.use_bias else []))
            y = activate(y,opt.FusedActivationFunction(),name+'_activation')
        elif kind == 'LOGISTIC':
            y = keras.layers.Activation('sigmoid',name=name)(x)
        else:
            raise NotImplementedError('Unvalidated operator: '+kind)
        if tuple(y.shape)[1:] != shape(out)[1:]:
            raise ValueError(f'Output shape mismatch at {name}: {y.shape} vs {shape(out)}')
        values[out] = y
    output = keras.layers.Concatenate(name='landmarks_and_presence')([values[int(graph.Outputs(0))],values[int(graph.Outputs(1))]])
    return keras.Model(inputs,output,name='hand_landmark_lite_roi'), dict(operators)


def reference(path, samples):
    import tensorflow as tf
    interpreter = tf.lite.Interpreter(model_path=str(path),num_threads=1,
        experimental_op_resolver_type=tf.lite.experimental.OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES)
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()[0]['index']
    outputs = interpreter.get_output_details()
    predictions = []
    for sample in samples:
        interpreter.set_tensor(inp,sample[None].astype(np.float32))
        interpreter.invoke()
        predictions.append(np.concatenate([interpreter.get_tensor(outputs[i]['index'])[0] for i in (0,1)]))
    return np.asarray(predictions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--rois',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output==ROOT or output.exists():
        raise ValueError('Use a new workspace output directory')
    model, operators = reconstruct(args.model)
    rng = np.random.default_rng(20261025)
    synthetic = np.stack([np.zeros((224,224,3),np.float32),np.ones((224,224,3),np.float32)*.5,
                          rng.uniform(0,1,(224,224,3)).astype(np.float32)])
    samples = synthetic if args.rois is None else np.concatenate([synthetic,np.load(args.rois)['roi_rgb']])
    expected = reference(args.model,samples)
    actual = model(samples,training=False).numpy()
    diff = np.abs(actual-expected)
    passed = bool(np.isfinite(diff).all() and diff[:,:63].max()<.01 and diff[:,63].max()<1e-4)
    report = dict(status='float_conversion_passed' if passed else 'float_conversion_failed',
        model_sha256=hashlib.sha256(args.model.read_bytes()).hexdigest(),
        samples=len(samples),synthetic_samples=3,real_roi_samples=len(samples)-3,
        coordinate_max_abs_error_roi_units=float(diff[:,:63].max()),
        presence_max_abs_error=float(diff[:,63].max()),parameters=model.count_params(),
        operators=operators,input_contract='224x224 RGB float32 [0,1], externally cropped hand ROI',
        output_contract='63 raw ROI x/y/z values followed by hand presence; not word classes or metric world coordinates',
        limitations=['Float conversion only; no fixed-point, HLS, resource or PL deployment validation.',
                     'Synthetic conversion checks are not hand-detection accuracy evaluation.'])
    output.mkdir(parents=True)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    np.savez_compressed(output/'parity.npz',inputs=samples,tflite=expected,keras=actual)
    print(json.dumps(report,indent=2))
    if not passed:
        raise RuntimeError('Float conversion parity failed; do not proceed to hardware')
    model.save(output/'hand_landmark_lite_roi.keras')


if __name__=='__main__':
    main()
