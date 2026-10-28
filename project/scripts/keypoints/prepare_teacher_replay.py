"""Extract diagnostic CPU replays of original blocks, never a deployment model."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from freeze_teacher_partition import MODEL_SHA, ROOT


def prepare(output):
    if output.exists() or not output.resolve().is_relative_to(ROOT/'project/_tmp'):
        raise ValueError('New workspace scratch output required')
    path = ROOT/'project/board/teacher_hands/hand_landmark_full.tflite'
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != MODEL_SHA:
        raise ValueError('Teacher SHA changed')
    import flatbuffers
    from tensorflow.lite.python import schema_py_generated as s
    source = s.ModelT.InitFromObj(s.Model.GetRootAsModel(data,0))
    graph = source.subgraphs[0]
    producer = {int(t):i for i,op in enumerate(graph.operators) for t in op.outputs}
    def opcode(op):
        c = source.operatorCodes[op.opcodeIndex]
        return max(c.builtinCode,c.deprecatedBuiltinCode)
    candidates = {
        'block_87_94': ([87,90,93,94],134,138),
        'blocks_87_104': ([87,90,93,94,97,100,103,104],134,142),
    }
    output.mkdir(parents=True)
    report = dict(scope='diagnostic_CPU_subgraph_replay_only_not_teacher_replacement',
                  teacher_sha256=MODEL_SHA, training=False, quantization=False, candidates=[])
    for name,(nodes,entry,exit_id) in candidates.items():
        produced = {int(t) for i in nodes for t in graph.operators[i].outputs}
        external = {int(t) for i in nodes for t in graph.operators[i].inputs if t>=0 and t not in produced}
        constants = external-{entry}
        parameters = []
        model = copy.deepcopy(source)
        g = model.subgraphs[0]
        # Preserve original tensor IDs, op options, layout and constants. Only
        # diagnostic execution plan/I/O changes. Exact FP16 -> FP32 expansion
        # makes immutable parameters available without external DEQUANTIZE.
        for t in sorted(constants):
            deq = graph.operators[producer[t]]
            if opcode(deq) != s.BuiltinOperator.DEQUANTIZE or len(deq.inputs)!=1:
                raise ValueError('Unexpected nonconstant external dependency')
            src_id = int(deq.inputs[0]); tensor = graph.tensors[src_id]
            if tensor.type != s.TensorType.FLOAT16:
                raise ValueError('Expected original FP16 constant')
            raw = source.buffers[tensor.buffer].data.tobytes()
            expanded = np.frombuffer(raw,dtype='<f2').astype('<f4')
            if not np.isfinite(expanded).all():
                raise ValueError('Nonfinite teacher weights')
            buffer = s.BufferT(); buffer.data = np.frombuffer(expanded.tobytes(),dtype=np.uint8)
            g.tensors[t].buffer = len(model.buffers); model.buffers.append(buffer)
            parameters.append(dict(tensor=t,source_tensor=src_id,shape=list(map(int,tensor.shape)),
                fp32_bytes=expanded.nbytes,fp32_sha256=hashlib.sha256(expanded.tobytes()).hexdigest()))
        # Reject hidden external consumers except the requested exit.
        external_outputs = {int(t) for t in produced if any(
            t in op.inputs for i,op in enumerate(graph.operators) if i not in nodes)}
        if external_outputs != {exit_id}:
            raise ValueError('Unexpected side output')
        g.operators = [g.operators[i] for i in nodes]
        g.inputs = np.asarray([entry],np.int32); g.outputs = np.asarray([exit_id],np.int32)
        used = {int(t) for op in g.operators for t in list(op.inputs)+list(op.outputs) if t>=0}
        used_buffers = {g.tensors[t].buffer for t in used}
        for t,tensor in enumerate(g.tensors):
            if t not in used:
                tensor.buffer=0
        for index,buffer in enumerate(model.buffers):
            if index not in used_buffers:
                buffer.data=None
        model.signatureDefs = []; model.metadata = []; model.metadataBuffer = []
        model.description = b'DIAGNOSTIC CPU REPLAY ONLY; original teacher unchanged'
        builder = flatbuffers.Builder(1024); root=model.Pack(builder)
        builder.Finish(root,file_identifier=b'TFL3'); artifact=bytes(builder.Output())
        target=output/(name+'.tflite'); target.write_bytes(artifact)
        rebuilt=s.Model.GetRootAsModel(artifact,0).Subgraphs(0)
        if rebuilt.OperatorsLength()!=len(nodes) or rebuilt.Inputs(0)!=entry or rebuilt.Outputs(0)!=exit_id:
            raise RuntimeError('Diagnostic graph roundtrip mismatch')
        report['candidates'].append(dict(name=name,file=target.name,sha256=hashlib.sha256(artifact).hexdigest(),
            selected_nodes=nodes,input_tensor=entry,output_tensor=exit_id,
            shape=list(map(int,graph.tensors[entry].shape)),boundary_bytes=175616,
            parameters=parameters,parameter_bytes=sum(p['fp32_bytes'] for p in parameters)))
    (output/'replay_manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(output),candidates=[c['name'] for c in report['candidates']])))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    prepare(p.parse_args().output.resolve())
