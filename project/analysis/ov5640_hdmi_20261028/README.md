# OV5640 相机接入 HDMI（2026-10-28）

本轮按仓库和现有硬件配置中的 OV5640 实施。用户确认板卡未开机，范围为完成本地代码、构建与发布候选；本轮不部署、不修改启动项。

## 数据路径与代码

`OV1 DVP → 现有 capture_dma → PS DDR → PS RGB565_LE/BGR888 转换 → HDMI MM2S VDMA → 720p HDMI OUT`。

相机使用 HP0，显示使用 HP2；AXI 和相机控制时钟 100MHz。相机仍由原有 arm/采集/恢复流程调度，新增预览入口不运行关键点网络，不需要 PC 按帧传图。该实现的实际预览速率需上板测量。

- FPGA 入口：[ov5640_snapshot_hdmi_prepare.tcl](../../fpga/scripts/ov5640_snapshot_hdmi_prepare.tcl)，接线在同目录 `ov5640_snapshot_hdmi_bd.tcl`。
- 构建步骤：[OV5640_HDMI_BUILD.md](../../fpga/scripts/OV5640_HDMI_BUILD.md)。最终独立工程位于 `project/_tmp/ov5640_snapshot_hdmi_20261028_v2/vivado/snapshot.xpr`。
- 预览入口：[hdmi_preview.py](../../board/ov5640_snapshot/hdmi_preview.py)，用法和板端启动命令在 [HDMI_PREVIEW.md](../../board/ov5640_snapshot/HDMI_PREVIEW.md)。
- 新发布目录：`project/board/ov5640_snapshot/release_hdmi/`。旧纯采集发布包保持原样；新包的 manifest 需要显式描述 HDMI 能力。

复用标准 `video/hdmi_out` 层级及已有 HDMI IP，保留 SOF TUSER=1、复位接线和 rgb2dvi 时钟约束修正。没有把旧 W6 中的传感器、KWS、音频或关键点网络加入新候选。相机控制/DMA 地址保持 `0x41200000`/`0x40400000`，HDMI 寄存器地址沿用已有 W6 映射。实际生成的 HWH 摘要见 [hardware_metadata.json](hardware_metadata.json)。

## 软件行为与验证

仅在采集 DMA 确认 Halted 且缓存 invalidate 完成后，把借用缓冲交给显示回调。预览仅显示完整帧；原采集模块接受小于 5% 丢失的政策没有改变，但此类部分帧会跳过显示。显示缓冲由预览进程持有，提交下一帧前只写非活动缓冲。

停止、帧切换和出错清理采用有界 DMA 轮询。任一路 DMA 停机未确认时保留缓冲和进程锁，CLI 等待断电。正常有界运行结束会停止 HDMI，不保留仍被读取的帧缓冲。显示失败单独记录，避免误把已经停机的相机 DMA 标为不安全。

测试证据：[software_tests.log](software_tests.log)、[software_tests.json](software_tests.json)。最终软件回归：板端模块运行 50 项（Windows 跳过 Linux 锁 1 项，其余通过），构建工具 28 项全部通过。测试类别：

- 颜色和帧边界：全部 65,536 种 RGB565 值与原 RGB 参考逐点对齐，显式核对红绿蓝通道；拒绝长度不完整或目标格式错误的输入。
- 采集集成：回调执行时 DMA 已停、缓存已失效；拒绝帧或不安全 DMA 不触发显示，部分帧继续按原门限计数，回调失败记录为显示错误并正常清理相机。
- 显示缓冲和异常：只更新非活动缓冲，部分帧保留上一帧；切换超时、DMA 错误、Ctrl-C、Halted 超时和缓冲保留。
- 接管与发布契约：不下载位流，旧固件能力缺失时拒绝预览；HWH 缺少 HDMI 模块、错误 MM2S 配置或关闭 HP2 时拒绝打包。Notebook/helper 哈希同步检查。
- 原有回归：连续采集的 arm 交替、单缓冲复用、严格 5% 门限、错误恢复、时长/次数/连续错误上限、PNG/RAW 边界、manifest 地址/hash，以及引脚映射、溯源漂移、缺少门禁和不完整 I/O 配置。

主要测试文件：[test_hdmi_preview.py](../../board/ov5640_snapshot/test_hdmi_preview.py)、[test_continuous_capture.py](../../board/ov5640_snapshot/test_continuous_capture.py)、[test_package_hdmi.py](../../scripts/ov5640/test_package_hdmi.py)。Windows 跳过 Linux `fcntl` 进程锁测试；新显示逻辑的本地测试均使用模拟硬件，不代替板端验收。

## FPGA 构建状态

Vivado 2024.1 的 BD 校验、target/HWH 生成、综合、布局布线和位流生成均已完成，综合/实现串行运行。setup WNS **1.237 ns**、hold WHS **0.033 ns**；LUT 6161/53200、寄存器 9958、BRAM Tile 7.5/140、DSP 9/220。无未约束内部端点、无无时钟寄存器；外部相机 I/O 不计作已签核。

门禁结果：DRC 无 Error、CDC 无 Critical、路由错误为 0、FIFO pointer bus skew 通过、SCCB 开漏/回读结构通过。DRC 仍有 IP 输入缓冲/流水线/BRAM 异步控制等 Warning；CDC 的一项 CDC-6 Warning 位于标准 VTC 的读回数据总线同步器，未修改或降低报告严重级别。原始报告见 [reports/](reports/)，机器可读汇总在 [build_summary.json](build_summary.json)。

最终发布包已生成，`snapshot_provenance.py verify` 通过；`capture.py --verify-only` 验证了成对 SHA、HWH 配置和地址，预览 manifest 的 HDMI 字段检查通过。

| 文件 | SHA256 |
|---|---|
| `ov5640_snapshot.bit` | `37189d24a396326dd849a55ed135dd3c97287ada3a2a0c562d2718cae7610beb` |
| `ov5640_snapshot.hwh` | `476283838eca44c73084032292357e0c44bc55a283cf69a5ee594ba4cb7f5942` |

完整构建证据与 routed DCP 保存在 `project/_tmp/ov5640_hdmi_build_20261028/`，发布包携带 `build_provenance.json`。最终 prepare 绑定了全部修正后的软件源；复用了 19 个匹配的 IP 综合缓存，其余 IP 与顶层重新综合，没有为旧产物补填源记录。

prepare 继承了原 PS DDR 配置的四项负 DQS-to-clock skew 警告（PSU-1..4）；本轮没有凭空修改板级 DDR 参数。

## 验收边界

本轮板卡未开机，没有真实相机采集、HDMI 屏幕目视、颜色顺序、运动连续性、画面撕裂、物理帧率或长期运行验证。软件提交帧率不是屏幕物理帧率；PS 逐帧调度和转换也不代表纯 PL 直通。

外部 DVP 输入/输出延迟及不确定度参数仍不完整。发布状态保留 `candidate_board_unverified`；内部时序、结构和哈希门禁不能替代相机外部时序或实际屏幕验收。

## 委派与成本记录

按项目规则使用两个 `gpt-6.1-sol/high` 子代理：一个完成 HDMI 复用调查与 Tcl 接入；另一个写出预览软件后因模型容量不足中断，其余软件检查、修正、测试与验收由主代理接手。没有改用其他模型。工具未返回逐次 token、缓存用量或可核算价格，任务合计 API 费用未知，不报告节省比例。
