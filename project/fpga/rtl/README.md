# fpga/rtl · 冻结遗留版本说明

本目录 RTL 是**为复现 W6 合一固件（kws_hdmi.bit）而冻结的旧版本**，来源：
`F:\PLD\pld-sign-glove` git 提交 `77cd56f`（2026-10-18，W6 发布构建当日），
唯 `merge_stream.v` 取自 `492beb4`（W3 期）——BD 的 module_ref 实例化带
`CLK_FREQ_HZ` 参数覆盖，main 新版（`85b898e` 起）已删除该参数；
W6 当年靠 OOC 综合缓存掩盖了此差异，干净重建必须用旧版。

新系统不接传感器，这些模块在固件中闲置。M0b 重建时将随传感器 SPI/DMA
与旧 HLS KWS 一并从 BD 剥离，届时本目录大部分文件删除。
**不要在此目录做新开发**；新 RTL 请建独立目录并更新 BD。
## OV5640 RTL

- `ov5640_snapshot/` contains the single-camera snapshot top and AXI packetizer.
- `ov5640_stereo/` contains DVP, SCCB, startup, and sensor configuration blocks reused by the snapshot top.
- Both directories are registered as active sources in `project/fpga/project/glove/glove.xpr`. The project top remains `system_wrapper`; `system.bd` does not instantiate the camera yet.
