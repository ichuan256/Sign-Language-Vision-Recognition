# 移除 PL 坏帧几何检测与板端部署

日期：2026-10-28。目标是去掉 DVP 行宽、行数和奇数字节等几何坏帧判定，同时保留 AXI/FIFO/DMA 传输错误和帧缓冲边界保护。

## RTL 与 PS 行为

- `project/fpga/rtl/ov5640_stereo/ov5640_dvp_capture.v` 不再报告几何错误；像素仍限制在配置的帧尺寸内，短帧按实际像素输出。`frame_error` 为旧接口兼容保留并恒低。
- 快照路径移除 DVP 诊断 CDC 与诊断页。packet 层对短帧正常发出 TLAST，奇数个 RGB565 像素时最后一拍用低 2 字节 TKEEP；FIFO 溢出与 packet 协议错误继续保留。
- PS 按 DMA 完成后的实际字节数计算丢失像素，超过现有门限的帧仍拒绝；capture.py 和 continuous_capture.py 不再依赖 PL 几何诊断。部分帧只保留实际接收的 RAW，不补齐为完整 PNG。

## 验证

- Python `unittest discover -s project/board/ov5640_snapshot -v`：32 项通过，1 项跳过（Windows 上的 Linux `fcntl` 锁测试）。覆盖完整/部分 DMA 长度、严格 5% 门限、RGB565 字节数、DMA 停机与失败恢复、连续采集限制和 manifest/HWH 地址/hash。
- Vivado 2024.1 XSim：独立 8 个顶层全部通过，覆盖 RGB565/SOF/EOL、宽高限幅与 malformed-frame 后恢复、packet TLAST/TKEEP、背压、双路采集、启动与 720p 行为。证据汇总：`project/_tmp/remove_pl_bad_frame_20261028/snapshot_regression.txt`。
- 扩展的 `tb_snapshot_system` 正常帧、重捕获、短帧字节/TKEEP 与 reset/重启采集断言均执行通过；该 bench 随后在既有手动 SCCB 场景等待未实现的 `status[9]`，20 ms watchdog 结束。此项未记为全通过。
- 合成、路由与项目门禁通过：WNS 2.211 ns、WHS 0.046 ns，DRC/CDC/布线/SCCB 检查通过；完整证据位于 `project/_tmp/remove_pl_bad_frame_build_20261028/`，`snapshot_provenance.py verify` 通过。
- 外部 DVP I/O 延迟约束不完整（input/output delay 与 clock uncertainty 缺项）；候选仍未完成真实摄像头采图或板级 I/O 时序验收。

## 候选与板端状态

- 新候选包：`project/board/ov5640_snapshot/release_remove_pl_bad_frame_20261028/`。
- bit SHA256：`8a7492c4a8736f17a0e448e5160e2a47056924ea8c1bdad520a02d4916fc87f7`
- HWH SHA256：`7989ea15b07f1a47c5f92677cf963b3c81f0fb915faf69901483666d4e9985f2`
- 2026-10-28 已把新 bit/HWH/manifest 与匹配的 capture/helper/notebook 写入板端 bootpy 固定目录 `/home/xilinx/jupyter_notebooks/ov5640_snapshot/`，随后冷启动。旧板端 release 与软件备份在 `.backup_remove_pl_bad_frame_20261028/`。
- bootpy 日志确认本次启动仅下载一次新候选，FCLK0=100 MHz；新 boot ID 与 download marker 匹配。板端重新计算的 bit/HWH SHA 与 manifest 一致，PYNQ `capture.py --verify-only` 显示 `PASS: paired hashes, HWH IP configuration and addresses`；continuous helper/notebook SHA 绑定检查通过。
- 本次没有执行真实相机抓图。当前候选虽已在板上加载，不能据此声称传感器、DDR/DMA 图像质量或外部 I/O 时序通过。
