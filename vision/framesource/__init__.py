"""Input abstraction layer: recognition code only ever sees a FrameSource."""
from .base import FrameSource
from .video_file import VideoFileSource
from .usb_cam import USBCamSource

__all__ = ["FrameSource", "VideoFileSource", "USBCamSource"]
