"""Clock-paced file input emulating a camera; drops late frames, never catches up in a burst."""
import time
import math

import cv2

from .base import FrameSource
from .video_file import VideoFileSource


class ReplaySource(FrameSource):
    def __init__(self, path, *, max_fps=30, loop=False):
        super().__init__('replay:'+str(path))
        self.path, self.max_fps, self.loop = path, max_fps, loop
        self.source = VideoFileSource(path, max_fps=max_fps)
        self._fps = self.source.fps
        self._duration = self.source.cap.get(cv2.CAP_PROP_FRAME_COUNT)/self.source._fps
        if loop and (not math.isfinite(self._duration) or self._duration <= 0):
            self.source.release()
            raise ValueError('Loop replay requires a positive source frame count')
        self._start = None
        self._offset = 0.0
        self._returned = 0
        self.loops = 0
        self.dropped_late_frames = 0
        self._released = False

    @property
    def fps(self):
        return self._fps

    def read(self):
        if self._released:
            return None
        if self._start is None:
            self._start = time.perf_counter()
        while True:
            item = self.source.read()
            if item is None:
                if not self.loop or self.source._returned == 0:
                    return None
                self.source.release()
                self.source = VideoFileSource(self.path, max_fps=self.max_fps)
                self._offset += self._duration
                self.loops += 1
                continue
            frame, _, timestamp = item
            timestamp += self._offset
            elapsed = time.perf_counter()-self._start
            if timestamp < elapsed-1/self.fps:
                self.dropped_late_frames += 1
                continue
            if timestamp > elapsed:
                time.sleep(timestamp-elapsed)
            index = self._returned
            self._returned += 1
            return frame, index, timestamp

    def release(self):
        if not self._released:
            self._released = True
            self.source.release()
