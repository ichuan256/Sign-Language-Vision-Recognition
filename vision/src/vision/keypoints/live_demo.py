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

from ..framesource import USBCamSource, VideoFileSource, ReplaySource, OV5640MonoSource
from .metrics import KeypointMetrics
from .holistic import _landmarks

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
WINDOW = 'Pose + hands | no semantics | Q/Esc: stop'


def make_source(spec, fps, width, height, loop=False):
    kind, sep, value = spec.partition(':')
    if sep and kind == 'file' and value:
        return VideoFileSource(value, max_fps=fps)
    if sep and kind == 'usb' and value.isdigit():
        return USBCamSource(int(value), max_fps=fps, width=width, height=height)
    if sep and kind == 'replay' and value:
        return ReplaySource(value, max_fps=fps, loop=loop)
    if sep and kind == 'ov5640':
        return OV5640MonoSource(value, max_fps=fps)
    raise ValueError('source must be file:<path>, replay:<path>, usb:<index> or ov5640:<endpoint>')


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
                    replay_loop=args.loop, hdmi_server_port=args.hdmi_port if args.serve_hdmi else None,
                    neural_backend='PC MediaPipe Holistic',display_layout='hand_rois' if args.hand_rois else 'full_frame',
                    versions=dict(mediapipe=mp.__version__, opencv=cv2.__version__,
                                  numpy=np.__version__, python=platform.python_version()),
                    host=platform.system()+' '+platform.machine(),
                    timestamp=datetime.now(timezone(timedelta(hours=8))).isoformat(),
                    limitations=[
                        'Availability is detector output presence, not landmark accuracy or recall against ground truth.',
                        'No sensor-exposure timestamp; camera/driver buffering and true capture-to-display latency are unknown.',
                        'host_result_ms: immediately before source.read() to detector completion, including read/rate-limit wait.',
                        'host_preview_submit_ms: read start to imshow/waitKey return; not physical display latency.',
                        'file: runs unpaced; replay: is clock-paced camera emulation, not real OV5640 capture.',
                        'Model/source initialization and final summary excluded from processed_fps; frame JSONL writes included.',
                        'No warmup frames excluded. Missing spans include hands outside view and cannot establish occlusion recovery latency.',
                        'No handedness accuracy, jitter accuracy, multi-person identity or metric 3D validation.',
                    ])
    stop_reason = 'end_of_stream'
    setup_start = time.perf_counter()
    started = None
    error = None
    frame_server = source = None
    try:
        with ExitStack() as stack:
            source = stack.enter_context(make_source(args.source, args.fps, args.width, args.height, args.loop))
            if args.serve_hdmi:
                from .frame_server import LatestFrameServer
                frame_server = stack.enter_context(LatestFrameServer(args.hdmi_port))
                metadata['hdmi_server_port'] = frame_server.port
                print(f'HDMI_FRAME_SERVER http://127.0.0.1:{frame_server.port}/frame.jpg', flush=True)
            metadata['source_nominal_fps'] = source.fps
            if isinstance(source, (VideoFileSource, ReplaySource)):
                with Path(source.path).open('rb') as media:
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
                roi_state = None
                if not args.headless or frame_server is not None:
                    if args.hand_rois:
                        from .hand_dashboard import render_hand_dashboard
                        preview,roi_state=render_hand_dashboard(bgr,result,frame_id,timestamp,
                            (metrics.frames+1)/max(result_end-started,1e-6),(result_end-read_end)*1000)
                    else:
                        preview = draw_result(bgr.copy(), result, metrics.frames+1, result_end-started)
                        cv2.putText(preview, f'FRAME {frame_id}  SOURCE {timestamp:.2f}s',
                                    (10, 52), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 255), 2)
                if frame_server is not None:
                    frame_server.publish(preview, frame_id, timestamp)
                if not args.headless:
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
                if roi_state is not None:row['hand_rois']=roi_state
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
        if frame_server is not None:
            metadata['hdmi_publish_state'] = frame_server.state()
        if isinstance(source, ReplaySource):
            metadata['replay_dropped_late_frames'] = source.dropped_late_frames
            metadata['replay_loops_completed'] = source.loops
        mode = dict(usb='live_host_pipeline', replay='paced_file_camera_emulation',
                    file='offline_file_throughput', ov5640='hardware_placeholder')
        report = dict(**metadata, stop_reason=stop_reason, error=error,
                      valid_run=metrics.frames > 0 and error is None,
                      measurement_mode=mode[metadata['input_kind']],
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
    parser.add_argument('--source', required=True, help='file: unpaced; replay: clock-paced; usb: real camera; ov5640: placeholder')
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
    parser.add_argument('--loop', action='store_true', help='Repeat replay: input while preserving monotonic timestamps')
    parser.add_argument('--serve-hdmi', action='store_true', help='Serve latest overlaid 1280x720 JPEG on loopback, for SSH forwarding')
    parser.add_argument('--hdmi-port', type=int, default=18780)
    parser.add_argument('--hand-rois',action='store_true',help='720p dashboard with current-frame hand crops and colored finger connections; PC inference')
    args = parser.parse_args(argv)
    if not np.isfinite([args.fps, args.seconds]).all() or min(args.fps, args.seconds) <= 0:
        parser.error('fps and seconds must be finite and positive')
    if min(args.width, args.height) <= 0 or args.max_frames < 0:
        parser.error('width/height must be positive; max-frames must be nonnegative')
    if args.loop and not args.source.startswith('replay:'):
        parser.error('--loop is only valid for replay: input')
    if not 1 <= args.hdmi_port <= 65535:
        parser.error('hdmi-port must be in [1,65535]')
    return run(args)


if __name__ == '__main__':
    main()
