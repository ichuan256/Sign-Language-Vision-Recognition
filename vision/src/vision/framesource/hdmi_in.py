"""M2 占位：板端 HDMI 输入帧源。

实现要点（届时按此补全，勿在下游写死任何采集细节）：
- 板端 BD 新增 hdmi_in 子系统（dvi2rgb + VDMA 采集，PYNQ v3.0.1 base 结构）；
- 帧经网络回传电脑（与 hdmi_audio_receiver.py 相同的 socket 通路），
  本类负责收包、解码 BGR、按包内帧号/时间戳产出 (bgr, frame_id, timestamp_s)；
- 丢包按帧号跳变上报，不插值。
"""
from .base import FrameSource


class HDMIInSource(FrameSource):
    def __init__(self, endpoint: str = "", *, max_fps=30.0, name=None):
        super().__init__(name or "hdmi_in")
        self.endpoint = endpoint
        self._max_fps = max_fps

    @property
    def fps(self):
        raise NotImplementedError("M2 阶段实现：板端 hdmi_in 采集 + 网络回传")

    def read(self):
        raise NotImplementedError("M2 阶段实现：板端 hdmi_in 采集 + 网络回传")

    def release(self):
        pass
