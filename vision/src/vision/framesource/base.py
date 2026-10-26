"""FrameSource: the only input abstraction the recognition pipeline sees.

Contract (frozen for M1; later HdmiInSource / OV5640*Source only add
implementations, never change this interface):

- ``read()`` returns the next ``(bgr, frame_id, timestamp_s)`` or ``None``
  at end of stream. ``bgr`` is a H×W×3 uint8 BGR image (OpenCV order).
  ``frame_id`` is the zero-based ordinal of the *returned* frame.
  ``timestamp_s`` is seconds from stream start, monotonically increasing.
- ``fps`` is the nominal stream rate in frames/second (> 0).
- FrameSource instances are context managers; ``release()`` frees the
  underlying device/handle and is idempotent.

Pre-segmented training clips are just files: VideoFileSource covers them.
Live input (USB camera today, board HDMI/OV5640 later) goes through the
same interface, so classification code never branches on input kind.
"""
from abc import ABC, abstractmethod


class FrameSource(ABC):
    """Uniform video input: read() -> (bgr, frame_id, timestamp_s) | None."""

    def __init__(self, name):
        self.name = str(name)

    @property
    @abstractmethod
    def fps(self):
        """Nominal frames per second of this stream (> 0)."""

    @abstractmethod
    def read(self):
        """Return (bgr_uint8_HxWx3, frame_id, timestamp_s) or None at EOS."""

    def __iter__(self):
        while True:
            item = self.read()
            if item is None:
                return
            yield item

    @abstractmethod
    def release(self):
        """Free the underlying resource; must be safe to call twice."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False
