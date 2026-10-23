"""Contract tests for FrameSource implementations (no camera required)."""
import numpy as np
import pytest

from vision.framesource import FrameSource, VideoFileSource, USBCamSource


class _Dummy(FrameSource):
    def __init__(self, n=3, fps=20.0):
        super().__init__("dummy")
        self._n, self._fps = n, fps
        self._i = 0

    @property
    def fps(self):
        return self._fps

    def read(self):
        if self._i >= self._n:
            return None
        i = self._i
        self._i += 1
        return np.zeros((4, 4, 3), np.uint8), i, i / self._fps

    def release(self):
        pass


def test_base_iterates_and_stops():
    src = _Dummy(n=3)
    seen = list(src)
    assert [item[1] for item in seen] == [0, 1, 2]
    assert seen[-1][2] == pytest.approx(0.1)
    assert src.read() is None


def test_video_file_source_reads_all_frames(tmp_path):
    import cv2
    path = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (64, 48))
    for _ in range(10):
        writer.write(np.zeros((48, 64, 3), np.uint8))
    writer.release()
    with VideoFileSource(path) as src:
        frames = list(src)
    assert len(frames) == 10
    assert [f[0].shape for f in frames] == [(48, 64, 3)] * 10
    assert [f[1] for f in frames] == list(range(10))
    assert frames[5][2] == pytest.approx(5 / 20.0)
    assert src.fps == pytest.approx(20.0)


def test_video_file_source_max_fps_drops_frames(tmp_path):
    import cv2
    path = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (64, 48))
    for _ in range(20):
        writer.write(np.zeros((48, 64, 3), np.uint8))
    writer.release()
    with VideoFileSource(path, max_fps=10) as src:
        frames = list(src)
    assert len(frames) == 10
    assert src.fps == 10.0
    assert np.all(np.diff([f[2] for f in frames]) > 0)


def test_video_file_source_missing_file_raises():
    with pytest.raises(ValueError):
        VideoFileSource("no_such_file.mp4")


def test_usb_cam_source_rejects_bad_fps():
    with pytest.raises(ValueError):
        USBCamSource(0, max_fps=0.0)
