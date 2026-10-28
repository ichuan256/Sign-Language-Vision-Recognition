"""Bounded PS teacher baseline and diagnostic profiles. No labels or FPGA access."""
import argparse
import ctypes as C
import gc
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import cv2
import numpy as np


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def statistics(values):
    values = list(values)
    if not values:
        return dict(count=0)
    return dict(count=len(values), mean=float(np.mean(values)),
                p50=float(np.percentile(values, 50)), p95=float(np.percentile(values, 95)),
                minimum=float(np.min(values)), maximum=float(np.max(values)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--video', type=Path, required=True)
    p.add_argument('--probe', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--frames', type=int, default=120)
    p.add_argument('--max-rois', type=int, default=100)
    p.add_argument('--profile-inputs', type=int, default=12)
    a = p.parse_args()
    if a.output.exists() or not 1 <= a.frames <= 300 or not 1 <= a.max_rois <= 100:
        raise ValueError('New bounded output required')
    if not 1 <= a.profile_inputs <= 24:
        raise ValueError('Bounded profile count required')
    expected = {'palm_detection_full.tflite':'1b14e9422c6ad006cde6581a46c8b90dd573c07ab7f3934b5589e7cea3f89a54',
                'hand_landmark_full.tflite':'11c272b891e1a99ab034208e23937a8008388cf11ed2a9d776ed3d01d0ba00e3',
                'libhands_tflite.so':'18f9b3c16f84b1ea2e09f8cb5b85ffa204a90155639fe3d19940bb47a317107e'}
    actual = {name:digest(a.work/name) for name in expected}
    if actual != expected:
        raise RuntimeError('Frozen model/runtime SHA mismatch')
    sys.path.insert(0, str(a.work))
    from teacher_runtime import TFLiteModel
    from run_teacher import HandsPipeline
    from teacher_geometry import draw_hands

    a.output.mkdir(parents=True)
    (a.output/'tensors').mkdir()
    report = dict(scope='PS_full_teacher_P0_no_training_no_PL',completed=False,
                  models_and_runtime=actual,threads=2,video_sha256=digest(a.video),
                  video=str(a.video),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  python=platform.python_version(),opencv=cv2.__version__,numpy=np.__version__,
                  display_enabled=False,profiler_during_baseline=False,
                  timing_notes='Per-frame processing includes ROI input copies and wrapper instrumentation; disk persistence occurs after frame timer. Total session wall includes persistence. Not final hybrid comparison.',
                  source_timestamp_note='Board-local file read start, not physical camera exposure time',
                  probe_sha256=digest(a.probe))
    records = []
    probes = {'palm':[], 'landmark':[]}

    class Timed:
        def __init__(self, model, name):
            self.model, self.name, self.calls = model, name, []
        def invoke(self, image):
            frozen = np.array(image, dtype=np.float32, copy=True)
            start = time.perf_counter()
            outputs = self.model.invoke(image)
            elapsed = (time.perf_counter()-start)*1000
            self.calls.append((frozen, outputs, elapsed))
            return outputs
        def close(self):
            self.model.close()

    pipeline = HandsPipeline(a.work, 2)
    pipeline.palm = Timed(pipeline.palm, 'palm')
    pipeline.landmark = Timed(pipeline.landmark, 'landmark')
    capture = None
    try:
        # Warm the original runtime independently; preserve initial empty tracking state.
        report['warmup_ms'] = {}
        for name, shape in [('palm',(1,192,192,3)),('landmark',(1,224,224,3))]:
            item = getattr(pipeline, name)
            start = time.perf_counter()
            item.model.invoke(np.zeros(shape, dtype=np.float32))
            report['warmup_ms'][name] = (time.perf_counter()-start)*1000
        capture = cv2.VideoCapture(str(a.video))
        if not capture.isOpened():
            raise RuntimeError('Cannot decode frozen board-local video')
        report['source'] = dict(width=capture.get(cv2.CAP_PROP_FRAME_WIDTH),
                                height=capture.get(cv2.CAP_PROP_FRAME_HEIGHT),
                                fps=capture.get(cv2.CAP_PROP_FPS))
        all_start = time.perf_counter()
        for frame_id in range(a.frames):
            begin_ns = time.monotonic_ns()
            start = time.perf_counter()
            ok, bgr = capture.read()
            if not ok:
                capture.release()
                capture = cv2.VideoCapture(str(a.video))
                ok, bgr = capture.read()
            if not ok:
                raise RuntimeError('No decodable frame on loop restart')
            decoded = time.perf_counter()
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            converted = time.perf_counter()
            pipeline.palm.calls.clear(); pipeline.landmark.calls.clear()
            hands, metrics = pipeline.process(rgb)
            inferred = time.perf_counter()
            draw_hands(rgb, hands)
            finished = time.perf_counter()
            row = dict(frame_id=frame_id,source_read_begin_monotonic_ns=begin_ns,
                       processing_ms=(finished-start)*1000,decode_ms=(decoded-start)*1000,
                       convert_ms=(converted-decoded)*1000,pipeline_ms=(inferred-converted)*1000,
                       draw_ms=(finished-inferred)*1000,hands=len(hands),
                       palm_abi_wall_ms=[c[2] for c in pipeline.palm.calls],
                       landmark_abi_wall_ms=[c[2] for c in pipeline.landmark.calls],
                       presence_scores=metrics['presence_scores'],palm_executed=bool(pipeline.palm.calls))
            persistence_start = time.perf_counter()
            for name in ('palm','landmark'):
                for image, outputs, elapsed in getattr(pipeline, name).calls:
                    limit = a.max_rois if name == 'landmark' else a.profile_inputs
                    if len(probes[name]) >= limit:
                        continue
                    relative = 'tensors/%s_%04d.npz' % (name,len(probes[name]))
                    path = a.output/relative
                    np.savez(path,input=image,**{'output_%d'%j:x for j,x in enumerate(outputs)})
                    probes[name].append(dict(file=relative,sha256=digest(path),frame_id=frame_id,
                                              abi_wall_ms=elapsed))
            row['tensor_persistence_ms'] = (time.perf_counter()-persistence_start)*1000
            records.append(row)
            if frame_id % 16 == 0:
                print('P0_FRAME',frame_id,'hands',len(hands),flush=True)
        report['baseline'] = dict(frames=len(records),session_wall_s=time.perf_counter()-all_start,
            processing_ms=statistics(r['processing_ms'] for r in records),
            pipeline_ms=statistics(r['pipeline_ms'] for r in records),
            decode_ms=statistics(r['decode_ms'] for r in records),
            draw_ms=statistics(r['draw_ms'] for r in records),
            palm_abi_wall_ms=statistics(v for r in records for v in r['palm_abi_wall_ms']),
            landmark_abi_wall_ms=statistics(v for r in records for v in r['landmark_abi_wall_ms']),
            palm_frames=sum(r['palm_executed'] for r in records),
            frames_with_hands=sum(r['hands']>0 for r in records),
            hand_count_histogram={str(i):sum(r['hands']==i for r in records) for i in (0,1,2)})
        pipeline.close()
        pipeline = None
        gc.collect()
        (a.output/'frames.json').write_text(json.dumps(records,indent=2)+'\n')
        (a.output/'probe_inputs.json').write_text(json.dumps(probes,indent=2)+'\n')
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        # Diagnostics use a separately linked extension; original shared library is untouched.
        report['diagnostics'] = []
        for name in ('palm','landmark'):
            for mode in ('default','builtin_only'):
                model_file = 'palm_detection_full.tflite' if name=='palm' else 'hand_landmark_full.tflite'
                model = TFLiteModel(a.probe, a.work/model_file, 2)
                lib = model.lib
                for symbol in ('hands_probe_execution_json','hands_probe_profile_end'):
                    getattr(lib,symbol).argtypes=[C.c_void_p]
                    getattr(lib,symbol).restype=C.c_char_p
                lib.hands_probe_profile_begin.argtypes=[C.c_void_p]
                lib.hands_probe_create_profiled.argtypes=[C.c_char_p,C.c_int,C.c_int]
                lib.hands_probe_create_profiled.restype=C.c_void_p
                lib.hands_probe_destroy.argtypes=[C.c_void_p]
                lib.hands_probe_destroy.restype=None
                if mode == 'builtin_only':
                    model.close()
                    model.handle=lib.hands_probe_create_profiled(str(a.work/model_file).encode(),2,1)
                    if not model.handle:
                        raise RuntimeError('Cannot create explicit builtin diagnostic')
                plans = json.loads(lib.hands_probe_execution_json(model.handle).decode())
                case_records = []
                try:
                    for item in probes[name][:a.profile_inputs]:
                        with np.load(a.output/item['file'],allow_pickle=False) as sample:
                            image=sample['input']; expected_outputs=[sample['output_%d'%j] for j in range(4 if name=='landmark' else 2)]
                        # Warm this interpreter, then measure an unprofiled call and compare all outputs.
                        model.invoke(image)
                        start=time.perf_counter(); actual_outputs=model.invoke(image)
                        unprofiled_ms=(time.perf_counter()-start)*1000
                        differences=[dict(max_abs=float(np.max(np.abs(x-y))),
                            exact=bool(np.array_equal(x,y)),allclose=bool(np.allclose(x,y,atol=1e-5,rtol=1e-4)))
                            for x,y in zip(actual_outputs,expected_outputs)]
                        if len(actual_outputs)!=len(expected_outputs):
                            raise RuntimeError('Output count changed')
                        if mode=='default' and not all(x['allclose'] for x in differences):
                            raise RuntimeError('Diagnostic extension changed default teacher outputs')
                        case_records.append(dict(input=item['file'],output_differences=differences,
                            unprofiled_abi_wall_ms=unprofiled_ms))
                    lib.hands_probe_destroy(model.handle)
                    model.handle=None
                    model.handle=lib.hands_probe_create_profiled(str(a.work/model_file).encode(),2,int(mode=='builtin_only'))
                    if not model.handle: raise RuntimeError('Cannot create profiled interpreter')
                    profile_plan=json.loads(lib.hands_probe_execution_json(model.handle).decode())
                    for case in case_records:
                        with np.load(a.output/case['input'],allow_pickle=False) as sample:
                            image=sample['input']
                            reference=[sample['output_%d'%j] for j in range(4 if name=='landmark' else 2)]
                        model.invoke(image)
                        if lib.hands_probe_profile_begin(model.handle):
                            raise RuntimeError('Cannot start diagnostic profiler')
                        try:
                            profiled_outputs=model.invoke(image)
                        finally:
                            raw=lib.hands_probe_profile_end(model.handle)
                        events=json.loads(raw.decode())
                        if not events or not all(e['ended'] for e in events):
                            raise RuntimeError('Incomplete operator events')
                        case['events']=events
                        case['profiled_outputs_allclose']=all(np.allclose(x,y,atol=1e-5,rtol=1e-4) for x,y in zip(profiled_outputs,reference))
                        if mode=='default' and not case['profiled_outputs_allclose']:
                            raise RuntimeError('Profiling changed optimized teacher outputs')
                    diagnostic=dict(model=name,mode=mode,plan=plans,profile_plan=profile_plan,cases=case_records,
                        performance_scope='diagnostic_only_not_replacement_for_original_library_baseline')
                    filename='diagnostic_%s_%s.json'%(name,mode)
                    (a.output/filename).write_text(json.dumps(diagnostic,indent=2)+'\n')
                    report['diagnostics'].append(dict(file=filename,model=name,mode=mode,
                        cases=len(case_records),nodes=len(plans['nodes']),
                        delegated_nodes=sum(n['delegated'] for n in plans['nodes'])))
                finally:
                    if model.handle:
                        lib.hands_probe_destroy(model.handle)
                        model.handle=None
                gc.collect()
        if a.frames >= 32 and len(probes['landmark']) < 6:
            raise RuntimeError('Insufficient landmark probes; do not accept P0 hotspot baseline')
        report.update(completed=True,landmark_probe_count=len(probes['landmark']),
                      palm_probe_count=len(probes['palm']),
                      landmark_equivalence_tested=bool(probes['landmark']))
    except Exception as e:
        report['error']=str(e)
        raise
    finally:
        if pipeline is not None: pipeline.close()
        if capture is not None: capture.release()
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('P0_COMPLETE',flush=True)


if __name__=='__main__':
    main()
