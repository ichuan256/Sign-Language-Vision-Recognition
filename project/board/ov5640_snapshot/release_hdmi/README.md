# OV5640 + HDMI 720p 本地候选

已完成 Vivado 2024.1 综合、布局布线、位流生成及配对校验。状态为 `candidate_board_unverified`：本轮板卡未开机，未部署或进行相机/屏幕验收。

本包的 `ov5640_snapshot.bit`、同名 `.hwh`、`release_manifest.json` 和 `build_provenance.json` 必须配套使用。相机通过 HP0 写 DDR，HDMI 通过 HP2 读取 PS 转换后的显示帧。内部时序 WNS 1.237 ns、WHS 0.033 ns；外部相机 I/O 时序仍未签核。

软件入口、冷启动要求和 60 秒预览命令见 [HDMI_PREVIEW.md](../HDMI_PREVIEW.md)。软件源 `capture.py`、`continuous_capture.py`、`hdmi_preview.py` 在本目录的上一级。只接管冷启动加载的固件，运行中禁止重新下载位流。

测试类别、资源、警告、SHA 和原始报告见 [本轮记录](../../../analysis/ov5640_hdmi_20261028/README.md)。
