"""Isolated postprocess parity and paired CPU runs; no FPGA or original-file writes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest

import cv2
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stats(values):
    return dict(count=len(values), mean=float(np.mean(values)),
                p50=float(np.percentile(values, 50)), p95=float(np.percentile(values, 95)))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalized(value):
    if isinstance(value, np.ndarray):
        return dict(shape=list(value.shape), dtype=str(value.dtype), sha256=hashlib.sha256(value.tobytes()).hexdigest())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k: normalized(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalized(v) for v in value]
    return value


class Spy:
    def __init__(self, model):
        self.model = model
        self.calls = []

    def invoke(self, tensor):
        start = time.perf_counter()
        outputs = self.model.invoke(tensor)
        self.calls.append((tensor, outputs, (time.perf_counter()-start)*1000))
        return outputs

    def close(self):
        self.model.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--frames', type=int, default=120)
    p.add_argument('--rounds', type=int, default=2)
    p.add_argument('--cached-only', action='store_true')
    a = p.parse_args()
    if a.output.exists() or not 1 <= a.frames <= 300 or not 1 <= a.rounds <= 3:
        raise ValueError('New bounded output required')
    expected = {
        'palm_detection_full.tflite': '1b14e9422c6ad006cde6581a46c8b90dd573c07ab7f3934b5589e7cea3f89a54',
        'hand_landmark_full.tflite': '11c272b891e1a99ab034208e23937a8008388cf11ed2a9d776ed3d01d0ba00e3',
        'libhands_tflite.so': '18f9b3c16f84b1ea2e09f8cb5b85ffa204a90155639fe3d19940bb47a317107e',
        'teacher_geometry.py': '9e57ea594fd8b3051c76193d888ef44a1b5b01346c6f1cd93572e0c4a71ba2a3',
    }
    if {name: sha(a.work/name) for name in expected} != expected:
        raise RuntimeError('Original teacher changed; freeze a new baseline first')
    sys.path.insert(0, str(a.work))
    import run_teacher
    import teacher_geometry as original
    fast = load_module('geometry_candidate', Path(__file__).with_name('teacher_geometry_fast.py'))
    tests = load_module('postprocess_tests', Path(__file__).with_name('test_teacher_postprocess.py'))
    tests.geometry = fast
    suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError('Threshold/NMS equivalence tests failed on target NumPy')
    a.output.mkdir()
    report = dict(completed=False, scope='CPU_postprocess_optimization_not_PL', original_files=expected,
                  fast_geometry_sha256=sha(Path(fast.__file__)), numpy=np.__version__, threads=2,
                  display_enabled=False, training=False, labels=False, fpga_access=False,
                  video_sha256=sha(a.baseline/'frozen_input.mp4'), tests_run=result.testsRun,
                  caveat='Two alternating pairs of 120 frames by default; not the final 3x300 hybrid/display gate. Timers exclude record hashing and JSON writes; small symmetric Spy bookkeeping remains.',
                  cached=[], passes=[])
    def save():
        (a.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    save()
    try:
        inputs = json.loads((a.baseline/'result/probe_inputs.json').read_text())['palm']
        cap = cv2.VideoCapture(str(a.baseline/'frozen_input.mp4'))
        ok, bgr = cap.read(); cap.release()
        if not ok:
            raise RuntimeError('Cannot decode frozen video')
        _, padding = original.letterbox_rgb(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        for item in inputs:
            with np.load(a.baseline/'result'/item['file'], allow_pickle=False) as data:
                outputs = [data['output_0'], data['output_1']]
            row = dict(file=item['file'])
            for mode, function in [('original', original.decode_palms), ('fast', fast.decode_palms)]:
                times = []
                for _ in range(2):
                    start = time.perf_counter(); det = function(outputs, padding)
                    times.append((time.perf_counter()-start)*1000)
                row[mode+'_ms'] = times
                if mode == 'original':
                    reference = det
                else:
                    tests.assert_detections_equal(det, reference)
            scores = next(x for x in outputs if x.size == 2016).reshape(-1)
            row.update(exact=True, detections=len(reference),
                       original_candidates=int(np.count_nonzero(scores > -100.)),
                       fast_candidates=len(fast._palm_candidate_indices(scores, .5)))
            report['cached'].append(row)
        save()
        print('CACHED_PARITY', len(report['cached']), 'PASS', flush=True)
        if not a.cached_only:
            for round_id in range(a.rounds):
                order = ('original', 'fast') if round_id % 2 == 0 else ('fast', 'original')
                paired = {}
                for mode in order:
                    run_teacher.decode_palms = original.decode_palms if mode == 'original' else fast.decode_palms
                    pipeline = run_teacher.HandsPipeline(a.work, 2)
                    cap = cv2.VideoCapture(str(a.baseline/'frozen_input.mp4'))
                    rows = []
                    try:
                        pipeline.palm.invoke(np.zeros((1,192,192,3),np.float32))
                        pipeline.landmark.invoke(np.zeros((1,224,224,3),np.float32))
                        pipeline.palm = Spy(pipeline.palm); pipeline.landmark = Spy(pipeline.landmark)
                        for frame_id in range(a.frames):
                            pipeline.palm.calls.clear(); pipeline.landmark.calls.clear()
                            start = time.perf_counter(); ok, bgr = cap.read()
                            if not ok:
                                raise RuntimeError('Frozen video ended before requested frames')
                            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                            hands, metrics = pipeline.process(rgb)
                            original.draw_hands(rgb, hands)
                            elapsed = (time.perf_counter()-start)*1000
                            # Digest every NN input and every raw output, plus autonomous
                            # ROI state, NMS outputs and all accepted hand/world results.
                            behavior = dict(hands=hands, next_rois=pipeline.rois,
                                metrics={k:v for k,v in metrics.items() if k not in ('palm_ms','landmark_ms')},
                                palm=[(x,y) for x,y,_ in pipeline.palm.calls],
                                landmark=[(x,y) for x,y,_ in pipeline.landmark.calls])
                            blob = json.dumps(normalized(behavior), sort_keys=True, allow_nan=False).encode()
                            rows.append(dict(frame=frame_id, processing_ms=elapsed, hands=len(hands),
                                palm_ms=[t for _,_,t in pipeline.palm.calls],
                                landmark_ms=[t for _,_,t in pipeline.landmark.calls],
                                behavior_sha256=hashlib.sha256(blob).hexdigest()))
                            if (frame_id+1) % 20 == 0:
                                print('PAIR_PROGRESS', round_id, mode, frame_id+1, flush=True)
                    finally:
                        cap.release(); pipeline.close()
                    paired[mode] = rows
                    name = 'frames_%d_%s.json'%(round_id,mode)
                    (a.output/name).write_text(json.dumps(rows)+'\n')
                    report['passes'].append(dict(round=round_id, mode=mode, file=name,
                        processing_ms=stats([r['processing_ms'] for r in rows]),
                        palm_ms=stats([t for r in rows for t in r['palm_ms']]),
                        landmark_ms=stats([t for r in rows for t in r['landmark_ms']]),
                        hands_histogram={str(n):sum(r['hands']==n for r in rows) for n in range(3)},
                        palm_calls=sum(len(r['palm_ms']) for r in rows),
                        landmark_calls=sum(len(r['landmark_ms']) for r in rows)))
                    save()
                if any(x['behavior_sha256'] != y['behavior_sha256']
                       for x,y in zip(paired['original'], paired['fast'])):
                    raise RuntimeError('Autonomous pipeline behavior or raw NN values changed')
                report.setdefault('pairs', []).append(dict(round=round_id, frames=a.frames, exact=True))
                save()
        report['completed'] = True
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        run_teacher.decode_palms = original.decode_palms
        report['original_files_unchanged'] = all(sha(a.work/name)==value for name,value in expected.items())
        save()
    print('POSTPROCESS_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
