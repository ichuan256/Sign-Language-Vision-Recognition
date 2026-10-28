"""Freeze an existing teacher subgraph and exact original constants; no fitting."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MODEL_SHA = '11c272b891e1a99ab034208e23937a8008388cf11ed2a9d776ed3d01d0ba00e3'
SELECTED = (87,90,93,94)


def freeze(model_path, output):
    if output.exists() or not output.resolve().is_relative_to(ROOT/'project/_tmp'):
        raise ValueError('Use a new project/_tmp directory')
    data = model_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != MODEL_SHA:
        raise ValueError('Teacher model SHA does not match the fixed graph')
    from tensorflow.lite.python import schema_py_generated as s
    model = s.Model.GetRootAsModel(data,0)
    graph = model.Subgraphs(0)
    names = {v:k for k,v in vars(s.BuiltinOperator).items() if k.isupper() and isinstance(v,int)}
    producer = {}
    consumers = {}

    def kind(op):
        code=model.OperatorCodes(op.OpcodeIndex())
        return names[max(code.BuiltinCode(),code.DeprecatedBuiltinCode())]

    def shape(index):
        t=graph.Tensors(index)
        return [int(t.Shape(j)) for j in range(t.ShapeLength())]

    def options(op):
        classes={'CONV_2D':s.Conv2DOptions,'DEPTHWISE_CONV_2D':s.DepthwiseConv2DOptions,'ADD':s.AddOptions}
        value=classes[kind(op)]();table=op.BuiltinOptions();value.Init(table.Bytes,table.Pos)
        result={'activation':int(value.FusedActivationFunction())}
        if kind(op)!='ADD':
            result.update(padding=int(value.Padding()),stride_h=value.StrideH(),stride_w=value.StrideW(),
                          dilation_h=value.DilationHFactor(),dilation_w=value.DilationWFactor())
        if kind(op)=='DEPTHWISE_CONV_2D':result['depth_multiplier']=value.DepthMultiplier()
        return result

    for i in range(graph.OperatorsLength()):
        op=graph.Operators(i)
        for j in range(op.OutputsLength()):producer[int(op.Outputs(j))]=i
        for j in range(op.InputsLength()):consumers.setdefault(int(op.Inputs(j)),[]).append(i)
    nodes=[]
    produced=set()
    for i in SELECTED:
        op=graph.Operators(i)
        ins=[int(op.Inputs(j)) for j in range(op.InputsLength())]
        outs=[int(op.Outputs(j)) for j in range(op.OutputsLength())]
        produced.update(outs)
        nodes.append(dict(node=i,op=kind(op),inputs=ins,outputs=outs,options=options(op)))
    if [n['op'] for n in nodes]!=['CONV_2D','DEPTHWISE_CONV_2D','CONV_2D','ADD']:
        raise ValueError('Unexpected subgraph topology')
    external_inputs={t for n in nodes for t in n['inputs'] if t not in produced}
    external_outputs={t for t in produced if set(consumers.get(t,[]))-set(SELECTED)}
    if external_outputs!={138} or external_inputs!={134,171,189,196,200,236,261}:
        raise ValueError('Partition dependency boundary changed')
    constants=[]
    arrays={}
    for tensor_id in sorted(external_inputs-{134}):
        op_index=producer[tensor_id]
        op=graph.Operators(op_index)
        if kind(op)!='DEQUANTIZE' or op.InputsLength()!=1:
            raise ValueError('Expected original immutable FP16 constant source')
        source_id=int(op.Inputs(0))
        source=graph.Tensors(source_id)
        raw=np.asarray(model.Buffers(source.Buffer()).DataAsNumpy(),dtype=np.uint8).tobytes()
        if source.Type()!=s.TensorType.FLOAT16 or len(raw)!=int(np.prod(shape(source_id)))*2:
            raise ValueError('Unexpected raw teacher constant type or size')
        expanded=np.frombuffer(raw,dtype='<f2').astype('<f4').reshape(shape(source_id))
        if not np.isfinite(expanded).all() or shape(source_id)!=shape(tensor_id):
            raise ValueError('Invalid exact teacher constant expansion')
        arrays[tensor_id]=expanded
        constants.append(dict(tensor=tensor_id,source_tensor=source_id,dequantize_node=op_index,
            source_buffer=int(source.Buffer()),shape=shape(tensor_id),source_dtype='FLOAT16',dtype='FLOAT32',
            raw_fp16_sha256=hashlib.sha256(raw).hexdigest(),fp32_bytes=expanded.nbytes,
            fp32_sha256=hashlib.sha256(expanded.tobytes()).hexdigest(),file='tensor_%d.npy'%tensor_id))
    if sum(x['fp32_bytes'] for x in constants)!=675136:
        raise ValueError('Teacher parameter footprint changed')
    if nodes[3]['options']['activation']!=0:
        raise ValueError('Residual add unexpectedly has a fused activation')
    output.mkdir(parents=True)
    for item in constants:
        np.save(output/item['file'],arrays[item['tensor']],allow_pickle=False)
        reloaded=np.load(output/item['file'],allow_pickle=False)
        if not np.array_equal(reloaded,arrays[item['tensor']]):
            raise RuntimeError('Constant file roundtrip mismatch')
        item['file_sha256']=hashlib.sha256((output/item['file']).read_bytes()).hexdigest()
    manifest=dict(status='static_partition_frozen_not_runtime_or_hardware_validated',
        source_model_sha256=MODEL_SHA,source_model=model_path.relative_to(ROOT).as_posix(),
        selected_nodes=nodes,dynamic_input=dict(tensor=134,shape=shape(134),dtype='FLOAT32',bytes=87808),
        dynamic_output=dict(tensor=138,shape=shape(138),dtype='FLOAT32',bytes=87808),
        external_consumers={str(t):consumers[t] for t in sorted(produced)},
        constants=constants,training_performed=False,calibration_performed=False,
        quantization_performed=False,labels_required=False,
        remaining=['runtime boundary capture','CPU subgraph equivalence','transfer microbenchmark','net benefit gate'])
    (output/'partition_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(output),nodes=list(SELECTED),constants=len(constants),
                          parameter_bytes=sum(x['fp32_bytes'] for x in constants),training=False)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',type=Path,default=ROOT/'project/board/teacher_hands/hand_landmark_full.tflite')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    freeze(a.model.resolve(),a.output.resolve())


if __name__=='__main__':main()
