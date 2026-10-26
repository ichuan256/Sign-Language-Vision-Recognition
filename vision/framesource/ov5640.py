"""Single OV5640 placeholder; hardware, voltage and pin mapping remain unverified.

The stereo class is retained only for historical API compatibility. Previous
dual-camera JA/JB wiring assumptions are obsolete and must not guide connection.
Current standalone-video design: docs/方案/03_Zynq7020独立实时关键点方案.md.
"""
from .base import FrameSource


class OV5640MonoSource(FrameSource):
    """Single OV5640 placeholder. No USB substitution, pins or capture logic assumed."""
    def __init__(self, endpoint="", *, max_fps=30.0, name=None):
        super().__init__(name or "ov5640_mono_pending_hardware")
        import math
        if not math.isfinite(max_fps) or max_fps <= 0:
            raise ValueError('max_fps must be positive')
        self.endpoint, self._fps = endpoint, float(max_fps)

    @property
    def fps(self):
        return self._fps

    def read(self):
        raise NotImplementedError('Single OV5640 hardware has not arrived; use replay:<video> temporarily')

    def release(self):
        pass


class OV5640StereoSource(FrameSource):
    def __init__(self, endpoint: str = "", *, max_fps=30.0, name=None):
        super().__init__(name or "ov5640_stereo")
        self.endpoint = endpoint
        self._max_fps = max_fps

    @property
    def fps(self):
        raise NotImplementedError("M3 阶段实现：OV5640 双目 PL 采集 + 回传")

    def read(self):
        raise NotImplementedError("M3 阶段实现：OV5640 双目 PL 采集 + 回传")

    def read_stereo(self):
        """返回 (左目帧, 右目帧, 同步偏差秒)；M3 实现。"""
        raise NotImplementedError

    def release(self):
        pass
