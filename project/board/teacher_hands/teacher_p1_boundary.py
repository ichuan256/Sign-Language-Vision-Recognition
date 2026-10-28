"""Capture XNNPACK block boundaries and replay exact teacher ops on CPU only."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def diff(x, y):
    delta = np.abs(x.astype(np.float64)-y.astype(np.float64))
    return dict(exact=bool(np.array_equal(x,y)),
                allclose=bool(np.isfinite(x).all() and np.isfinite(y).all() and
                              np.allclose(x,y,atol=1e-5,rtol=1e-4)),
                max_abs=float(delta.max()),p99_abs=float(np.percentile(delta,99)))


def stats(values):
    return dict(count=len(values),mean=float(np.mean(values)),
                p50=float(np.percentile(values,50)),p95=float(np.percentile(values,95)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--probe',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',type=int,default=100)
    a=p.parse_args()
    if a.output.exists() or not 1<=a.cases<=100:
        raise ValueError('New bounded output required')
    stage=Path(__file__).parent
    manifest=json.loads((stage/'replay_manifest.json').read_text())
    if sha(a.work/'hand_landmark_full.tflite')!=manifest['teacher_sha256']:
        raise RuntimeError('Original full teacher changed')
    for candidate in manifest['candidates']:
        if sha(stage/candidate['file'])!=candidate['sha256']:
            raise RuntimeError('Replay artifact changed')
    sys.path.insert(0,str(a.work))
    from teacher_runtime import TFLiteModel
    a.output.mkdir(); (a.output/'boundaries').mkdir()
    report=dict(completed=False,scope='diagnostic_runtime_boundaries_and_CPU_replay_not_PL',
                manifest=manifest,probe_sha256=sha(a.probe),threads=2,training=False,
                fpga_access=False,cases=[],
                caveat='Additional interpreter outputs force boundary retention and may change allocation/fusion. Timing is diagnostic; production teacher file is not rewritten. Cached ROIs do not prove motion/occlusion coverage or generic accuracy.')
    def save():
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    full=None; replays={}
    try:
        full=TFLiteModel(a.probe,a.work/'hand_landmark_full.tflite',2)
        lib=full.lib
        lib.hands_probe_create_boundaries.argtypes=[C.c_char_p,C.c_int]
        lib.hands_probe_create_boundaries.restype=C.c_void_p
        lib.hands_probe_execution_json.argtypes=[C.c_void_p]
        lib.hands_probe_execution_json.restype=C.c_char_p
        full.close()
        full.handle=lib.hands_probe_create_boundaries(str(a.work/'hand_landmark_full.tflite').encode(),2)
        if not full.handle:
            raise RuntimeError('Boundary interpreter creation failed')
        full.output_counts=[lib.hands_tflite_output_count(full.handle,i) for i in range(7)]
        full.output_shapes=[full._dims(lib.hands_tflite_output_dims,i) for i in range(7)]
        if full.output_counts != [63,1,1,63,21952,21952,21952]:
            raise RuntimeError('Boundary output contract changed')
        report['full_boundary_execution']=json.loads(lib.hands_probe_execution_json(full.handle))
        for candidate in manifest['candidates']:
            model=TFLiteModel(a.probe,stage/candidate['file'],2)
            replays[candidate['name']]=model
            candidate['execution']=json.loads(lib.hands_probe_execution_json(model.handle))
        inputs=json.loads((a.baseline/'result/probe_inputs.json').read_text())['landmark'][:a.cases]
        if len(inputs)!=a.cases:
            raise RuntimeError('Insufficient frozen inputs')
        full.invoke(np.zeros(full.input_shape,np.float32))
        for model in replays.values():
            model.invoke(np.zeros(model.input_shape,np.float32))
        durations={c['name']:[] for c in manifest['candidates']}
        for index,item in enumerate(inputs):
            source=a.baseline/'result'/item['file']
            if sha(source)!=item['sha256']:
                raise RuntimeError('Frozen input archive changed')
            with np.load(source,allow_pickle=False) as sample:
                image=sample['input']; golden=[sample['output_%d'%i] for i in range(4)]
            outputs=full.invoke(image)
            row=dict(input=item['file'],input_archive_sha256=item['sha256'],
                     original_output_differences=[diff(x,y) for x,y in zip(outputs[:4],golden)],replays={})
            if not all(d['allclose'] for d in row['original_output_differences']):
                raise RuntimeError('Boundary capture changed original final outputs')
            boundaries=dict(zip((134,138,142),outputs[4:]))
            for candidate in manifest['candidates']:
                model=replays[candidate['name']]
                start=time.perf_counter(); actual=model.invoke(boundaries[candidate['input_tensor']])[0]
                elapsed=(time.perf_counter()-start)*1000
                difference=diff(actual,boundaries[candidate['output_tensor']])
                if not difference['allclose']:
                    raise RuntimeError('Standalone CPU block differs from full teacher boundary')
                row['replays'][candidate['name']]=dict(difference=difference,abi_wall_ms=elapsed)
                durations[candidate['name']].append(elapsed)
            relative='boundaries/roi_%04d.npz'%index
            np.savez(a.output/relative,**{'tensor_%d'%k:v for k,v in boundaries.items()})
            row.update(boundary_file=relative,boundary_file_sha256=sha(a.output/relative))
            report['cases'].append(row)
            if (index+1)%10==0:
                save();print('BOUNDARY_PROGRESS',index+1,flush=True)
        report['cpu_replay_abi_ms']={name:stats(values) for name,values in durations.items()}
        report['completed']=True
    except Exception as error:
        report['error']=str(error)
        raise
    finally:
        if full: full.close()
        for model in replays.values(): model.close()
        save()
    print('BOUNDARY_COMPLETE',json.dumps(report['cpu_replay_abi_ms']),flush=True)


if __name__=='__main__':
    main()
