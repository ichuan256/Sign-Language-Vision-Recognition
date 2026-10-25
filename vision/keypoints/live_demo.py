"""Pure pose/hand landmark preview and benchmark. No gesture classifier."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import hashlib
import json
import platform
from pathlib import Path
import time

import cv2
import mediapipe as mp
import numpy as np

from ..framesource import USBCamSource, VideoFileSource
from .metrics import KeypointMetrics
from .holistic import _landmarks

ROOT = Path(__file__).resolve().parents[2]
WINDOW = 'Pose + hands | no semantics | Q/Esc: stop'


def make_source(spec, fps, width, height):
    kind, sep, value = spec.partition(':')
    if sep and kind == 'file' and value:
        return VideoFileSource(value, max_fps=fps)
    if sep and kind == 'usb' and value.isdigit():
        return USBCamSource(int(value), max_fps=fps, width=width, height=height)
    raise ValueError('source must be file:<path> or usb:<nonnegative index>')


def draw_result(frame, result, frames, elapsed):
    drawing = mp.solutions.drawing_utils
    holistic = mp.solutions.holistic
    drawing.draw_landmarks(frame, result.pose_landmarks, holistic.POSE_CONNECTIONS)
    drawing.draw_landmarks(frame, result.left_hand_landmarks, holistic.HAND_CONNECTIONS,
                           drawing.DrawingSpec(color=(0, 220, 0), thickness=2))
    drawing.draw_landmarks(frame, result.right_hand_landmarks, holistic.HAND_CONNECTIONS,
                           drawing.DrawingSpec(color=(0, 140, 255), thickness=2))
    text = (f'{frames/max(elapsed, 1e-6):.1f} processed FPS | '
            f'L:{int(result.left_hand_landmarks is not None)} '
            f'R:{int(result.right_hand_landmarks is not None)} | Q/Esc')
    cv2.putText(frame, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 255), 2)
    return frame


def coordinates(result):
    # Strict JSON nulls for missing data; these are model coordinates, not metric 3D.
    arrays = dict(pose=_landmarks(result.pose_landmarks, 33, visibility=True),
                  hands=np.stack([_landmarks(result.left_hand_landmarks, 21),
                                  _landmarks(result.right_hand_landmarks, 21)]))
    return {k: np.where(np.isfinite(v), v, None).tolist() for k, v in arrays.items()}


def run(args):
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output == ROOT:
        raise ValueError('Output must be a dedicated directory inside the workspace')
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite: {output}')
    output.mkdir(parents=True)
    options = dict(static_image_mode=False, model_complexity=args.model_complexity,
                   smooth_landmarks=True, enable_segmentation=False, refine_face_landmarks=False,
                   min_detection_confidence=.5, min_tracking_confidence=.5)
    metrics = KeypointMetrics()
    metadata = dict(schema_version='keypoint_benchmark_v1', semantic_classifier=False,
                    source=args.source, input_kind=args.source.partition(':')[0],
                    scenario=args.scenario, requested_max_fps=args.fps,
                    requested_camera_size=[args.width, args.height], headless=args.headless,
                    save_landmarks=args.save_landmarks, seconds_limit=args.seconds,
                    max_frames=args.max_frames, detector_options=options,
                    versions=dict(mediapipe=mp.__version__, opencv=cv2.__version__,
                                  numpy=np.__version__, python=platform.python_version()),
                    host=platform.system()+' '+platform.machine(),
                    timestamp=datetime.now(timezone(timedelta(hours=8))).isoformat(),
                    limitations=[
                        'Availability is detector output presence, not landmark accuracy or recall against ground truth.',
                        'No sensor-exposure timestamp; camera/driver buffering and true capture-to-display latency are unknown.',
                        'host_result_ms: immediately before source.read() to detector completion, including read/rate-limit wait.',
                        'host_preview_submit_ms: read start to imshow/waitKey return; not physical display latency.',
                        'File mode runs unpaced, not a live-camera or realtime-replay benchmark.',
                        'Model/source initialization and final summary excluded from processed_fps; frame JSONL writes included.',
                        'No warmup frames excluded. Missing spans include hands outside view and cannot establish occlusion recovery latency.',
                        'No handedness accuracy, jitter accuracy, multi-person identity or metric 3D validation.',
                    ])
    stop_reason = 'end_of_stream'
    setup_start = time.perf_counter()
    started = None
    error = None
    try:
        with ExitStack() as stack:
            source = stack.enter_context(make_source(args.source, args.fps, args.width, args.height))
            metadata['source_nominal_fps'] = source.fps
            if isinstance(source, VideoFileSource):
                with source.path.open('rb') as media:
                    metadata['source_sha256'] = hashlib.file_digest(media, 'sha256').hexdigest()
            detector = stack.enter_context(mp.solutions.holistic.Holistic(**options))
            stream = stack.enter_context((output/'frames.jsonl').open('x', encoding='utf-8'))
            metadata['setup_ms'] = (time.perf_counter()-setup_start)*1000
            started = time.perf_counter()
            while True:
                if time.perf_counter()-started >= args.seconds:
                    stop_reason = 'seconds_limit'
                    break
                if args.max_frames and metrics.frames >= args.max_frames:
                    stop_reason = 'frame_limit'
                    break
                read_start = time.perf_counter()
                item = source.read()
                read_end = time.perf_counter()
                if item is None:
                    break
                bgr, frame_id, timestamp = item
                metadata['actual_frame_size'] = [bgr.shape[1], bgr.shape[0]]
                result = detector.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
                result_end = time.perf_counter()
                key = -1
                preview_ms = None
                if not args.headless:
                    preview = draw_result(bgr.copy(), result, metrics.frames+1, result_end-started)
                    # Resize preview only; inference always receives the source frame.
                    if preview.shape[1] > 1280:
                        preview = cv2.resize(preview, (1280, round(preview.shape[0]*1280/preview.shape[1])))
                    cv2.imshow(WINDOW, preview)
                    key = cv2.waitKey(1) & 0xff
                    preview_ms = (time.perf_counter()-read_start)*1000
                present = dict(pose=result.pose_landmarks is not None,
                               left_hand=result.left_hand_landmarks is not None,
                               right_hand=result.right_hand_landmarks is not None)
                timing = dict(read_ms=(read_end-read_start)*1000,
                              inference_ms=(result_end-read_end)*1000,
                              host_result_ms=(result_end-read_start)*1000,
                              host_preview_submit_ms=preview_ms)
                metrics.update(timestamp, **present, **timing)
                row = dict(frame_id=frame_id, timestamp_s=timestamp, **present, **timing)
                if args.save_landmarks:
                    row['landmarks'] = coordinates(result)
                stream.write(json.dumps(row, allow_nan=False)+'\n')
                if key in (27, ord('q'), ord('Q')):
                    stop_reason = 'user_stop'
                    break
                if not args.headless and cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                    stop_reason = 'window_closed'
                    break
            elapsed = time.perf_counter()-started
    except KeyboardInterrupt:
        stop_reason = 'interrupted'
        elapsed = time.perf_counter()-(started or setup_start)
    except Exception as exc:
        stop_reason, error = 'error', str(exc)
        elapsed = time.perf_counter()-(started or setup_start)
        raise
    finally:
        if not args.headless:
            cv2.destroyAllWindows()
        report = dict(**metadata, stop_reason=stop_reason, error=error,
                      valid_run=metrics.frames > 0 and error is None,
                      measurement_mode=('live_host_pipeline' if metadata['input_kind']=='usb' else 'offline_file_throughput'),
                      **metrics.summary(max(elapsed if 'elapsed' in locals() else .000001, .000001)))
        (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    if not metrics.frames:
        raise RuntimeError('No frames processed; report is not a valid benchmark')
    print(json.dumps(dict(output=str(output), frames=report['frames'],
                         processed_fps=report['processed_fps'], timing_ms=report['timing_ms'],
                         both_hands_rate=report['availability']['both_hands']['detected_rate']), indent=2))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, help='Explicit file:<path> or usb:0; never opens a camera by default')
    parser.add_argument('--output', type=Path, required=True, help='New workspace directory; existing outputs refused')
    parser.add_argument('--fps', type=float, default=30)
    parser.add_argument('--seconds', type=float, default=60, help='Host loop time limit; cannot interrupt a blocked camera driver read')
    parser.add_argument('--max-frames', type=int, default=0)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--model-complexity', type=int, choices=(0, 1, 2), default=1)
    parser.add_argument('--scenario', choices=('general', 'static', 'fast_motion', 'crossing', 'occlusion'), default='general')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--save-landmarks', action='store_true')
    args = parser.parse_args(argv)
    if not np.isfinite([args.fps, args.seconds]).all() or min(args.fps, args.seconds) <= 0:
        parser.error('fps and seconds must be finite and positive')
    if min(args.width, args.height) <= 0 or args.max_frames < 0:
        parser.error('width/height must be positive; max-frames must be nonnegative')
    return run(args)


if __name__ == '__main__':
    main()
