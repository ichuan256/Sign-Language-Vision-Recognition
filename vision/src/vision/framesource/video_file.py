"""VideoFileSource: FrameSource over a video file on disk.

Timestamps come from ``frame_index / reported_fps`` (CFR assumption), the
same basis documented in vision/src/vision/sign_video — VFR precise PTS is not claimed.
``max_fps`` optionally downsamples by dropping frames without re-encoding,
identical to the extract.py sampling rule.
"""
from pathlib import Path

import cv2
import numpy as np

from .base import FrameSource


class VideoFileSource(FrameSource):
    def __init__(self, path, *, max_fps=None, name=None):
        super().__init__(name or Path(path).name)
        self.path = Path(path)
        self.cap = cv2.VideoCapture(str(self.path))
        if not self.cap.isOpened():
            self.cap.release()
            raise ValueError(f"cannot decode: {self.path}")
        fps = float(self.cap.get(cv2.CAP_PROP_FPS))
        if not np.isfinite(fps) or fps <= 0:
            self.cap.release()
            raise ValueError(f"invalid source fps: {self.path}")
        if max_fps is not None and (not np.isfinite(max_fps) or max_fps <= 0):
            self.cap.release()
            raise ValueError("max_fps must be positive")
        self._fps = fps
        self._max_fps = max_fps
        self._next_id = 0
        self._next_time = 0.0
        self._returned = 0
        self._released = False

    @property
    def fps(self):
        # Downsampled streams keep a constant nominal spacing of 1/max_fps;
        # classification only needs a strictly increasing time base.
        return min(self._fps, self._max_fps) if self._max_fps else self._fps

    def read(self):
        if self._released:
            return None
        while True:
            ok, frame = self.cap.read()
            if not ok:
                return None
            timestamp = self._next_id / self._fps
            self._next_id += 1
            if timestamp + 1e-8 < self._next_time:
                continue
            step = 1.0 / min(self._fps, self._max_fps) if self._max_fps else 0.0
            self._next_time += step
            frame_id = self._returned
            self._returned += 1
            return frame, frame_id, timestamp

    def release(self):
        if not self._released:
            self._released = True
            self.cap.release()
