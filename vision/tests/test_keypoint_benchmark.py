"""No camera, GUI, model inference or gesture classifier required."""
import json
from types import SimpleNamespace

import numpy as np
import pytest

from vision.keypoints.metrics import KeypointMetrics
from vision.keypoints import live_demo
from vision.framesource import FrameSource, USBCamSource


def update(metrics, timestamp, left=True, right=True, **timing):
    metrics.update(timestamp, pose=True, left_hand=left, right_hand=right,
                   read_ms=1, inference_ms=3, host_result_ms=4, **timing)


def test_rates_and_percentiles():
    metrics = KeypointMetrics()
    update(metrics, 0, right=False)
    update(metrics, .1)
    report = metrics.summary(.2)
    assert report['processed_fps'] == 10
    assert report['availability']['both_hands']['detected_rate'] == .5
    assert report['availability']['pose']['detected_rate'] == 1
    assert report['timing_ms']['host_result_ms']['p95'] == 4
    assert report['timing_ms']['host_preview_submit_ms'] is None


def test_recovered_and_unfinished_missing_runs():
    metrics = KeypointMetrics()
    for t, detected in enumerate([False, False, True, False]):
        update(metrics, t*.1, left=detected)
    hand = metrics.summary(1)['availability']['left_hand']
    assert hand['longest_missing_frames'] == 2
    assert hand['missing_runs'][0] == dict(frames=2, observed_span_s=.2, recovered=True)
    assert hand['missing_runs'][1]['recovered'] is False
    assert hand['missing_runs'][1]['observed_span_s'] == 0  # no fabricated final-frame duration
    assert metrics.summary(1)['availability']['left_hand'] == hand  # summary does not mutate state


@pytest.mark.parametrize('timestamp', [0, -.1, float('nan')])
def test_rejects_nonincreasing_timestamps(timestamp):
    metrics = KeypointMetrics()
    update(metrics, 0)
    with pytest.raises(ValueError):
        update(metrics, timestamp)
    assert metrics.frames == 1


def test_rejects_invalid_timings_without_mutation():
    metrics = KeypointMetrics()
    with pytest.raises(ValueError):
        update(metrics, 0, host_preview_submit_ms=float('nan'))
    assert metrics.frames == 0
    assert metrics.summary(1)['availability']['both_hands']['detected_rate'] is None


def test_missing_coordinates_are_json_null():
    result = SimpleNamespace(pose_landmarks=None, left_hand_landmarks=None, right_hand_landmarks=None)
    arrays = live_demo.coordinates(result)
    assert np.shape(arrays['hands']) == (2, 21, 3)
    assert arrays['hands'][0][0] == [None, None, None]
    assert 'NaN' not in json.dumps(arrays, allow_nan=False)


def test_overlay_without_landmarks_does_not_open_gui():
    result = SimpleNamespace(pose_landmarks=None, left_hand_landmarks=None, right_hand_landmarks=None)
    frame = np.zeros((100, 640, 3), np.uint8)
    image = live_demo.draw_result(frame, result, 2, .1)
    assert image.shape == (100, 640, 3)
    assert image.any()  # status text rendered without imshow/camera


class FakeSource(FrameSource):
    def __init__(self):
        super().__init__('fake')
        self.index = 0
        self.closed = False

    @property
    def fps(self):
        return 30

    def read(self):
        if self.index == 2:
            return None
        i = self.index
        self.index += 1
        return np.zeros((48, 64, 3), np.uint8), i, i/30

    def release(self):
        self.closed = True


class FakeDetector:
    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def process(self, frame):
        return SimpleNamespace(pose_landmarks=None, left_hand_landmarks=None, right_hand_landmarks=None)


def test_headless_runner_outputs_and_refuses_overwrite(tmp_path, monkeypatch):
    source = FakeSource()
    monkeypatch.setattr(live_demo, 'ROOT', tmp_path)
    monkeypatch.setattr(live_demo, 'make_source', lambda *args: source)
    monkeypatch.setattr(live_demo.mp.solutions.holistic, 'Holistic', FakeDetector)
    output = tmp_path/'run'
    report = live_demo.main(['--source','file:fake','--output',str(output), '--headless','--save-landmarks'])
    assert report['frames'] == 2
    assert report['semantic_classifier'] is False
    assert report['valid_run'] is True
    assert report['measurement_mode'] == 'offline_file_throughput'
    assert source.closed
    rows = [json.loads(line) for line in (output/'frames.jsonl').read_text().splitlines()]
    assert rows[0]['landmarks']['hands'][0][0] == [None, None, None]
    with pytest.raises(FileExistsError):
        live_demo.main(['--source','file:fake','--output',str(output),'--headless'])
    assert (output/'report.json').exists()


def test_runner_saves_failure_and_releases_source(tmp_path, monkeypatch):
    source = FakeSource()
    class BrokenDetector(FakeDetector):
        def process(self, frame):
            raise RuntimeError('synthetic detector failure')
    monkeypatch.setattr(live_demo, 'ROOT', tmp_path)
    monkeypatch.setattr(live_demo, 'make_source', lambda *args: source)
    monkeypatch.setattr(live_demo.mp.solutions.holistic, 'Holistic', BrokenDetector)
    with pytest.raises(RuntimeError, match='synthetic'):
        live_demo.main(['--source','file:fake','--output',str(tmp_path/'failure'),'--headless'])
    report = json.loads((tmp_path/'failure/report.json').read_text())
    assert source.closed
    assert not report['valid_run']
    assert report['stop_reason'] == 'error'
    assert report['error'] == 'synthetic detector failure'


def test_runner_honors_frame_limit(tmp_path, monkeypatch):
    source = FakeSource()
    monkeypatch.setattr(live_demo, 'ROOT', tmp_path)
    monkeypatch.setattr(live_demo, 'make_source', lambda *args: source)
    monkeypatch.setattr(live_demo.mp.solutions.holistic, 'Holistic', FakeDetector)
    report = live_demo.main(['--source','file:fake','--output',str(tmp_path/'limited'),
                            '--headless','--max-frames','1'])
    assert report['frames'] == 1
    assert report['stop_reason'] == 'frame_limit'
    assert source.closed


@pytest.mark.parametrize('option,value', [('--fps','nan'),('--seconds','0'),('--width','0'),('--max-frames','-1')])
def test_invalid_cli_rejected_before_opening_source(tmp_path, option, value):
    with pytest.raises(SystemExit):
        live_demo.main(['--source','usb:0','--output',str(tmp_path/'invalid'),option,value])
    assert not (tmp_path/'invalid').exists()


def test_usb_rate_limit_drops_iteratively(monkeypatch):
    import vision.framesource.usb_cam as usb
    class Capture:
        def isOpened(self):
            return True
        def read(self):
            return True, np.zeros((2, 2, 3), np.uint8)
        def release(self):
            pass
    times = iter([0] + [0]*2000 + [1])
    monkeypatch.setattr(usb.cv2, 'VideoCapture', lambda index: Capture())
    monkeypatch.setattr(usb.time, 'perf_counter', lambda: next(times))
    with USBCamSource(0, max_fps=1) as source:
        assert source.read()[2] == 0
        assert source.read()[2] == 1  # previously exceeded Python's recursion depth


@pytest.mark.parametrize('source', ['usb:-1', 'file:', 'anything', 'usb:no'])
def test_rejects_bad_source_spec(source):
    with pytest.raises(ValueError):
        live_demo.make_source(source, 30, 640, 480)
