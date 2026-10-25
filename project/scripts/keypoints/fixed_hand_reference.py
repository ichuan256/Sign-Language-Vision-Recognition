"""Calibrate and evaluate a per-channel integer hand-landmark graph.

Integer-valued convolutions use float64 as an exact arithmetic carrier only when
the conservative accumulation bound is below 2**52. Hardware parity is a separate gate.
"""
import argparse
import json
import math
import os
from pathlib import Path

import numpy as np

os.environ.setdefault('TF_USE_LEGACY_KERAS','1')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
ROOT = Path(__file__).resolve().parents[3]


def fractional_bits(peak, bits, guard=1):
    peak = np.asarray(peak,dtype=np.float64)*guard
    return np.floor(np.log2((2**(bits-1)-1)/np.maximum(peak,1e-12))).astype(int).clip(-24,30)


def quantize(values, fraction, bits):
    raw = np.rint(np.ldexp(np.asarray(values,dtype=np.float64),fraction))
    clipped = int(np.count_nonzero((raw<-(2**(bits-1))) | (raw>2**(bits-1)-1)))
    return np.clip(raw,-(2**(bits-1)),2**(bits-1)-1).astype(np.int64),clipped


def rescale(codes, input_fraction, output_fraction, bits=16):
    # Powers of two are exact. All intermediates are separately bounded below 2**52.
    raw = np.rint(np.ldexp(np.asarray(codes,dtype=np.float64),
                          np.asarray(output_fraction)-np.asarray(input_fraction)))
    clipped = int(np.count_nonzero((raw<-(2**(bits-1))) | (raw>2**(bits-1)-1)))
    return np.clip(raw,-(2**(bits-1)),2**(bits-1)-1).astype(np.int64),clipped


def tensor_key(tensor):
    return tensor.name


def calibrate(model, samples):
    import tf_keras as keras
    layers = [layer for layer in model.layers if layer.__class__.__name__!='Concatenate']
    probe = keras.Model(model.input,[layer.output for layer in layers])
    peaks = {layer.name:0.0 for layer in layers}
    for sample in samples:
        for layer,value in zip(layers,probe(sample[None],training=False)):
            peaks[layer.name] = max(peaks[layer.name],float(np.max(np.abs(value.numpy()))))
    return peaks


def make_spec(model, peaks, weight_bits):
    specs, arrays = [],{}
    for layer in model.layers:
        kind = layer.__class__.__name__
        inputs = layer.input if isinstance(layer.input,list) else [layer.input]
        spec = dict(name=layer.name,kind=kind,inputs=[tensor_key(t) for t in inputs],
                    output=tensor_key(layer.output),output_shape=[int(v) if v is not None else 1 for v in layer.output.shape])
        if kind!='Concatenate':
            spec['fraction'] = int(fractional_bits(peaks[layer.name],16,guard=1.25))
            spec['calibration_peak'] = peaks[layer.name]
        if kind in ('Conv2D','DepthwiseConv2D','Dense'):
            kernel,bias = layer.get_weights()
            axes = (0,1) if kind=='DepthwiseConv2D' else tuple(range(kernel.ndim-1))
            peak = np.max(np.abs(kernel),axis=axes)
            fraction = fractional_bits(peak,weight_bits)
            codes, clipped = quantize(kernel,fraction,weight_bits)
            if clipped:
                raise ValueError('Known weight clipping is not allowed')
            arrays[layer.name+'_kernel'] = codes.astype(np.int8 if weight_bits<=8 else np.int16)
            arrays[layer.name+'_bias_float'] = bias
            spec['weight_fraction'] = fraction.reshape(-1).tolist()
            spec['kernel_shape'] = list(kernel.shape)
            spec['bias_count'] = len(bias)
            if kind!='Dense':
                spec.update(strides=list(layer.strides),padding=layer.padding,
                            dilation=list(layer.dilation_rate))
            terms = (kernel.shape[0]*kernel.shape[1] if kind=='DepthwiseConv2D' else int(np.prod(kernel.shape[:-1])))
            spec['macs'] = int(np.prod(spec['output_shape']))*terms
        elif kind=='MaxPooling2D':
            spec.update(pool_size=list(layer.pool_size),strides=list(layer.strides),padding=layer.padding)
        elif kind=='ReLU':
            spec['max_value'] = float(layer.max_value) if layer.max_value is not None else None
        elif kind=='Activation':
            if layer.get_config()['activation']!='sigmoid':
                raise NotImplementedError('Only hand-presence sigmoid is supported')
            spec['activation'] = 'sigmoid_lut_q15_step_1_64_range_8'
        elif kind not in ('InputLayer','Add','GlobalAveragePooling2D','Flatten','Concatenate'):
            raise NotImplementedError(kind)
        specs.append(spec)
    return specs,arrays


def execute(sample, specs, arrays):
    import tensorflow as tf
    values, fractions = {},{}
    clipping = {}
    max_accumulator = 0
    lut = np.rint(32768/(1+np.exp(-np.arange(-512,513,dtype=np.float64)/64))).astype(np.int64)
    for spec in specs:
        name,kind = spec['name'],spec['kind']
        if kind=='InputLayer':
            codes,clipped = quantize(sample[None],spec['fraction'],16)
        elif kind=='Concatenate':
            # Heterogeneous output ports: coordinates and presence keep their own scales.
            return np.concatenate([np.ldexp(values[key].astype(np.float64),-fractions[key])
                                   for key in spec['inputs']],axis=-1)[0],clipping,max_accumulator
        else:
            inputs = [values[key] for key in spec['inputs']]
            fs = [fractions[key] for key in spec['inputs']]
            x = inputs[0]
            if kind in ('Conv2D','DepthwiseConv2D','Dense'):
                if kind!='Dense' and spec['dilation'] != [1,1]:
                    raise NotImplementedError('Integer dilation has not been validated')
                weight = arrays[name+'_kernel'].astype(np.float64)
                fw = np.array(spec['weight_fraction'])
                bias, bias_clip = quantize(arrays[name+'_bias_float'],fs[0]+fw,48)
                if bias_clip:
                    raise OverflowError('Bias exceeds 48-bit accumulator')
                terms = (weight.shape[0]*weight.shape[1] if kind=='DepthwiseConv2D' else int(np.prod(weight.shape[:-1])))
                bound = 32768*int(np.max(np.abs(weight)))*terms+int(np.max(np.abs(bias)))
                if bound>=2**47 or bound>=2**52:
                    raise OverflowError('Unvalidated accumulation bound')
                if kind=='Conv2D':
                    acc = tf.nn.conv2d(tf.constant(x,dtype=tf.float64),tf.constant(weight),
                        strides=[1,*spec['strides'],1],padding=spec['padding'].upper()).numpy()
                elif kind=='DepthwiseConv2D':
                    acc = tf.nn.depthwise_conv2d(tf.constant(x,dtype=tf.float64),tf.constant(weight),
                        strides=[1,*spec['strides'],1],padding=spec['padding'].upper()).numpy()
                else:
                    acc = x.astype(np.int64)@weight.astype(np.int64)
                acc = acc.astype(np.int64)+bias
                max_accumulator = max(max_accumulator,int(np.max(np.abs(acc))))
                codes,clipped = rescale(acc,fs[0]+fw,spec['fraction'])
            elif kind=='Add':
                common = max(fs)
                bound = sum(int(np.max(np.abs(v)))*(1<<(common-f)) for v,f in zip(inputs,fs))
                if bound>=2**47:
                    raise OverflowError('Residual alignment exceeds 48-bit accumulator')
                acc = sum(np.left_shift(v,common-f) for v,f in zip(inputs,fs))
                codes,clipped = rescale(acc,common,spec['fraction'])
            elif kind=='ReLU':
                y = np.maximum(x,0)
                if spec['max_value'] is not None:
                    y = np.minimum(y,round(spec['max_value']*2**fs[0]))
                codes,clipped = rescale(y,fs[0],spec['fraction'])
            elif kind=='MaxPooling2D':
                y = tf.nn.max_pool2d(tf.constant(x,dtype=tf.float64),ksize=spec['pool_size'],
                    strides=spec['strides'],padding=spec['padding'].upper()).numpy()
                codes,clipped = rescale(y,fs[0],spec['fraction'])
            elif kind=='GlobalAveragePooling2D':
                y = x.astype(np.float64).mean(axis=(1,2))
                codes,clipped = rescale(y,fs[0],spec['fraction'])
            elif kind=='Flatten':
                codes,clipped = rescale(x.reshape(1,-1),fs[0],spec['fraction'])
            elif kind=='Activation':
                index = np.clip(np.rint(np.ldexp(x.astype(np.float64),6-fs[0])),-512,512).astype(int)+512
                codes,clipped = rescale(lut[index],15,spec['fraction'])
            else:
                raise NotImplementedError(kind)
        values[spec['output']] = codes
        fractions[spec['output']] = spec['fraction']
        clipping[name] = clipped
    raise RuntimeError('Missing output port packing')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--rois',type=Path,required=True)
    parser.add_argument('--weight-bits',type=int,choices=(8,12,16),default=8)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output==ROOT or output.exists():
        raise ValueError('Use a new workspace output directory')
    import tf_keras as keras
    model = keras.models.load_model(args.model,compile=False)
    with np.load(args.rois) as data:
        samples = data['roi_rgb']
        calibration, validation = data['calibration_indices'],data['validation_indices']
    peaks = calibrate(model,samples[calibration])
    specs,arrays = make_spec(model,peaks,args.weight_bits)
    reference = model(samples[validation],training=False).numpy()
    predictions,clipping,bounds = [],[],[]
    for index in validation:
        predicted,clipped,bound = execute(samples[index],specs,arrays)
        predictions.append(predicted)
        clipping.append(clipped)
        bounds.append(bound)
        print(f'Validated integer ROI {len(predictions)}/{len(validation)}',flush=True)
    predictions = np.stack(predictions)
    diff = np.abs(predictions-reference)
    weights = sum(arr.size for key,arr in arrays.items() if key.endswith('_kernel'))
    report = dict(status='integer_reference_evaluated_not_hardware_validated',
        weight_bits=args.weight_bits,activation_bits=16,accumulator_bits=48,
        calibration_rois=len(calibration),validation_rois=len(validation),
        coordinate_max_abs_error_roi_units=float(diff[:,:63].max()),
        coordinate_mean_abs_error_roi_units=float(diff[:,:63].mean()),
        presence_max_abs_error=float(diff[:,63].max()),
        coordinates_within_2_roi_units=bool(diff[:,:63].max()<=2),
        presence_within_002=bool(diff[:,63].max()<=.02),
        validation_clipped_elements=sum(sum(c.values()) for c in clipping),
        max_observed_accumulator_code=max(bounds),
        full_int16_input_accumulation_bound_checked=True,
        residual_alignment_bound_checked=True,
        kernel_values=weights,kernel_packed_bytes=math.ceil(weights*args.weight_bits/8),
        kernel_container_bytes=sum(arr.nbytes for key,arr in arrays.items() if key.endswith('_kernel')),
        macs_per_roi=sum(s.get('macs',0) for s in specs),
        max_activation_elements=max(int(np.prod(s['output_shape'])) for s in specs),
        limitations=['Numerical drift vs imported float model, not manually annotated landmark accuracy.',
            'Small source-held-out numerical ROI probes; no generalization or hardware latency claim.',
            'Float64 exact-integer convolution bound checked; averaging/rescaling and LUT still require independent C/RTL parity.',
            'No CSim, synthesis, bitstream or PL inference has been completed by this script.'])
    output.mkdir(parents=True)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (output/'graph.json').write_text(json.dumps(specs,indent=2)+'\n',encoding='utf-8')
    np.savez_compressed(output/'weights.npz',**arrays)
    np.savez_compressed(output/'validation.npz',inputs=samples[validation],reference=reference,integer=predictions)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
