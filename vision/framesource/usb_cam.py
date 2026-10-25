"""USBCamSource: FrameSource over a local USB camera (cv2.VideoCapture).

Timestamps are wall-clock seconds from stream start, so dropped camera
frames cannot corrupt the time base. ``max_fps`` rate-limits capture for
pipelines that cannot keep up (recognition targets >= 30 fps; a slow
pipeline should drop input frames, never queue them).
"""
import time

import cv2
import numpy as np

from .base import FrameSource


class USBCamSource(FrameSource):
    def __init__(self, index=0, *, width=None, height=None, max_fps=30.0, name=None):
        super().__init__(name or f"usb_cam_{index}")
        if not np.isfinite(max_fps) or max_fps <= 0:
            raise ValueError("max_fps must be positive")
        self.cap = cv2.VideoCapture(int(index))
        if not self.cap.isOpened():
            self.cap.release()
            raise ValueError(f"cannot open camera index {index}")
        for prop, value in ((cv2.CAP_PROP_FRAME_WIDTH, width),
                            (cv2.CAP_PROP_FRAME_HEIGHT, height)):
            if value is not None:
                self.cap.set(prop, int(value))
        self._max_fps = float(max_fps)
        self._t0 = None
        self._next_emit = 0.0
        self._next_id = 0
        self._released = False

    @property
    def fps(self):
        return self._max_fps

    def read(self):
        if self._released:
            return None
        while True:
            ok, frame = self.cap.read()
            if not ok:
                return None
            now = time.perf_counter()
            if self._t0 is None:
                self._t0 = now
            t = now - self._t0
            if t >= self._next_emit:
                break  # iterative dropping: no recursive stack growth
        self._next_emit = t + 1.0 / self._max_fps
        frame_id = self._next_id
        self._next_id += 1
        return frame, frame_id, t

    def release(self):
        if not self._released:
            self._released = True
            self.cap.release()
