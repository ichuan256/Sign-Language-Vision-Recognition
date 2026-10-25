"""Input abstraction layer: recognition code only ever sees a FrameSource."""
from .base import FrameSource
from .video_file import VideoFileSource
from .usb_cam import USBCamSource
from .replay import ReplaySource
from .ov5640 import OV5640MonoSource

__all__ = ["FrameSource", "VideoFileSource", "USBCamSource", "ReplaySource", "OV5640MonoSource"]
