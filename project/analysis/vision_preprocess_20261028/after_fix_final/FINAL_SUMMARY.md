# PL 预处理 RTL 修复与复验

## 结果

修复后的独立 `vision_preprocess` 模块在 Vivado 2024.1 下通过 RTL lint、三组 XSim 自检和 10 ns OOC 综合/布局布线时序检查。修复前的 OOC 最差 slack 为 −10.558 ns、330 个 setup 端点失败；当前最终 RTL 的 OOC setup/hold 失败端点均为 0，路由错误为 0。

本次只改独立预处理模块及其构建/验证说明；未接入 W6 BD、未生成部署位流、未改相机发布包、未操作板卡。

## RTL 改动

- 在 `vision_rgb565_affine` 中将帧跨度验证、源地址行偏移/基址/像素偏移、缓存查找、RGB 乘法和通道累加拆成寄存阶段。地址始终按 byte address 计算，保留完整加法进位后再检查 32 位边界；RGB565 半字 lane 使用原始地址 bit 1。此举修复了原有 64 位地址/乘加与乘加权累加组合路径过长的问题。
- 明确使用 `sample_address_full[0]` 检查半字对齐，并把舍入逻辑收窄到实际输出位，消除 lint 的未使用位/算术精度告警。帧跨度计算依旧允许末端恰好等于 `0x1_0000_0000`。
- 在 AXI wrapper 移除未使用的 `core_busy` 连接；用完整 TKEEP popcount 计算 `bytes_this_beat`，覆盖 0 至 4 字节且不触发加法截位 lint 告警。
- `vision_preprocess_prepare.tcl` 与 `vision_preprocess_ooc.tcl` 使用固定的 3 个 RTL / 3 个 testbench 源清单，并允许通过变量指定全新的输出目录。OOC 的 `result.tcl` 现在显式记录 `timing_pass`，避免把“有 routed.dcp”误读成时序通过。
- 新增 `project/board/vision_preprocess/README.md`，记录依赖、干净目录重建、lint、仿真和 OOC 命令。最终验证源及向量清单 SHA-256 见 `source_sha256.txt`。

## 验证

| 检查 | 结果 | 验证内容与证据 |
|---|---|---|
| Vivado RTL lint | **0 条 lint 消息** | Vivado 2024.1 `synth_design -lint`；见 [`linter_final2.rpt`](../after_fix/linter_final2.rpt)。零消息报告没有 Expanded violation 表，因此 lint CSV 为空。 |
| RGB888 AXIS packer | **PASS**，49 帧、2,821 个背压周期 | 覆盖 1/2/3/4 字节尾拍、像素字节序、TKEEP/TUSER/TLAST、输入气泡及输出背压稳定；摘要见 [`regression.txt`](xsim/regression.txt)，测试代码见 [tb_rgb888_axis_pack32.sv](../../../fpga/tb/vision_preprocess/tb_rgb888_axis_pack32.sv)。 |
| RGB565 affine sampler | **PASS**，16 个向量 fixture、19 帧、15 个非法配置、135,085 个输出背压周期 | 覆盖负坐标/半相位舍入、黑边邻居、无符号地址回绕、4096 边界、720p letterbox/旋转 ROI、读错误后清零及后续任务恢复；摘要见 [`regression.txt`](xsim/regression.txt)，测试代码见 [tb_vision_rgb565_affine.sv](../../../fpga/tb/vision_preprocess/tb_vision_rgb565_affine.sv)，向量清单见 [vectors.json](vectors.json)。 |
| AXI wrapper 集成 | **PASS** | 覆盖 AXI-Lite AW/W 独立握手、WSTRB、响应背压、shadow/start、AXI 读等待/错误 drain、输出打包、完成和 reset；摘要见 [`regression.txt`](xsim/regression.txt)，测试代码见 [tb_vision_preprocess_axi.sv](../../../fpga/tb/vision_preprocess/tb_vision_preprocess_axi.sv)。 |
| Python 参考与驱动 | **14 项通过** | 包括几何/像素参考、32 位帧尾边界、signed 系数、RGB565 全码值、张量布局，以及 MMIO 超时/错误/短帧保护；运行 `python project/board/vision_preprocess/test_preprocess.py -v`。 |
| OOC route / timing | **PASS**，100 MHz，10.000 ns | WNS **+0.188 ns**，TNS 0；WHS **+0.096 ns**，THS 0；4,231 个 setup/hold 端点均无失败；3,513/3,513 可路由 nets 完成路由，无 routing error。见 [`result.tcl`](ooc/result.tcl)、[`timing_routed.rpt`](ooc/timing_routed.rpt)、[`route_status.rpt`](ooc/route_status.rpt)。 |

Vivado XSim 启动时提示无法自动发现 GCC，但 compile、elaborate 和 run 均完成，三个 testbench 都产生 `TEST_PASS`。

最终 OOC 资源为 1,366 LUT、1,990 FF、7 DSP、0 BRAM；见 [`utilization_routed.rpt`](ooc/utilization_routed.rpt)。最差路径为 `sampler/neighbor_reg[1]` 到 `sampler/sum_r0` 的 DSP 输入，数据路径 9.231 ns、12 级逻辑。时序有正 slack，但余量较窄。

OOC DRC 仍报告 10 条 Warning：5 条 DPOP-1、4 条 DPOP-2 是 DSP 内部流水寄存器使用建议，另 1 条 ZPS7-1 来自该独立 OOC 设计未实例化 PS7。它们不是 route/timing 失败；原 DRC 的 39 条警告已降为 10 条。详情见 [`drc.rpt`](ooc/drc.rpt)。

流水化增加了周期数：仿真中 224×224 旋转 ROI fixture 用 2,943,274 个周期；按 100 MHz OOC 时钟折算约 29.4 ms 的模块时钟时间，实际端到端性能还取决于系统时钟、AXI/DDR 和集成约束。

## 验证边界

本结果只证明独立模块在本次 OOC 时钟约束下的仿真、lint 和路由时序。没有板级 I/O delay、真实 DDR/AXI 接口约束或系统时钟/复位环境；不能据此宣称整板时序、吞吐或硬件行为通过。输出契约仍是 AXI DMA 一帧一个包，不可直接接 HDMI/VDMA video input。
