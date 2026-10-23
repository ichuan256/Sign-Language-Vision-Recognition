"""M3 占位：OV5640 双目帧源。

硬件规划（docs/方案 §3，移植传感器后接口已释放）：
- Pmod JA = 左目 8bit 数据，Pmod JB = 右目 8bit 数据；
- SCCB（双目共总线分地址）、复位、电源使能走 Arduino D0–D5；
- PL 采集控制器 + VDMA 写 DDR，双目帧打同步时间戳；
- 首选 640×480 起步降 PCLK，Pmod 排线信号完整性是主要风险。

识别接入策略：左目为主识别帧（read() 产出左目 BGR），右目帧经
read_stereo() 供后续立体评估；下游特征/分类代码不变。
"""
from .base import FrameSource


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
