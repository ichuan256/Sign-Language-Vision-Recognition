# 流式计算与访存扩展（2026-10-26）

第二版已冷部署并完成实际数值/时延验证：**0.505 / 0.490 / 0.490 秒/ROI**，
三次各 64 输出都与整数参考完全一致。相对 [0.56 秒基线](cache_pipeline.md)，稳定重复耗时
降低约 13%，约 2Hz；尚未达到 200ms/5Hz。三次是同一 ROI 的重复，不是三个独立样本。

同一模型、W12/A16、48bit 累加和两次舍入边界保持不变。将卷积与 depthwise 合并为
16 路乘累加生产者，使用深度 4 的 FIFO 向量化写回消费者传递结果，两阶段并行执行。
MAC 循环实际 II=1，量化消费者实际 II=2；不能把目标 II 当成综合结果。

启用 AXI 自动扩展上限 128bit 与 64 字节基址对齐。实际生成端口为输入 32bit、权重 32bit、
参数 128bit、输出 64bit，尚未达到所有端口 128bit。参数池按层补齐 64 字节，驱动检查
所有传入地址。普通 RGB、非整通道和 63 坐标输出保留标量尾部处理。

验证记录：

- 整网主机 C：7 ROI 的 64 输出全部逐值一致，`project/_tmp/kp_stream_c_v1/report.json`。
- C/RTL：10 组、5106 输出一致，包含 stride、padding、通道尾数、负数舍入与输出尾部哨兵。
- 首版 HLS 估计：DSP 57、BRAM18K 169、LUT 30754、FF 23115。
- 第二版将已检查范围内的尺寸乘法收窄，HLS 为 DSP 39、BRAM18K 169、LUT 29701、FF 20861；
  7 ROI 整网 C 与 10 组 C/RTL 再次全部通过，证据 `project/_tmp/kp_stream_c_v2/`、`kp_stream_ip_v2/`。
- Python 回归：157 项及 32 个子测试通过，两条既有 protobuf 弃用警告。

首版整板 `project/_tmp/kp_stream_system_v1/` 完成布线但 setup 失败：WNS 约 -0.58ns，
WHS 0.016ns。关键路径经过共享的通用 32 位尺寸乘法；没有发布到板卡。
第二版工程 `project/_tmp/kp_stream_system_v2b/`、同模型/对齐寄存器 `project/_tmp/kp_stream_model_v2/`。
`kp_stream_system_v2/` 在 Vivado Tcl 子解释器初始化时失败，另起新目录重试，没有删除失败证据。
各轮没有复用旧布局布线结果。

第二版整板最终 LUT 37742/53200、FF 46706/106400、DSP 165/220、BRAM Tile 119.5/140。
Routed WNS 0.307ns、WHS 0.010ns、TNS/THS=0，时钟方法学门禁通过。
发布目录 `project/_tmp/kp_stream_system_v2b/release/`，冷部署记录 `project/_tmp/kp_stream_deploy_v2/`。
旧 0.56 秒成对固件已备份；未修改启动项，未运行中重载 FPGA。

实际板端证据 `project/_tmp/kp_stream_board_v2/`：首次进程初始化与前向合计 14.833 秒，
SSH 请求墙钟 21.082 秒；二者都不能当成每帧推理时延。每 ROI 49 次整层＋13 次 vector 调用。
首轮分项普通卷积 0.300 秒、depthwise 0.114 秒，vector 总调用墙钟 0.041 秒。
仍以访存和卷积为主要下一轮优化点；输入与权重端口尚未扩到 64/128bit。

| 整板资源 | 0.56 秒基线 | 本版 |
|---|---:|---:|
| LUT | 39327 | 37742 |
| DSP | 179 | 165 |
| BRAM Tile | 107 | 119.5 |

额外 12.5 个 BRAM Tile 换取这轮延迟下降，不能宣称所有资源都减少。
动态验收 `project/_tmp/kp_stream_dynamic_v2/` 正常结束：2353 视频帧、1242 帧有效 PC ROI、
243 次实际 PL 结果，10 组不同输入及输出，至少 600 次确认写屏，输入逐次 SHA 核验。
用户已确认视频正常、右侧 PL 持续更新。并发 PL 前向中位数 0.533 秒、P95 0.620 秒；
整段约 1.56 次结果/秒，包含启动及缺 ROI 的间隙，不能用 15fps 视频发布值替代。
紧凑证据、发布哈希和资源见 [stream_wide.json](stream_wide.json)。

随后已启动 600 秒播放，进度 `project/_tmp/kp_stream_dynamic_live_v2/live.json`；
结束后保留最后一帧，该长播放的稳定性不能提前判通过。左侧仅黄色 PC ROI 框，右侧实际 PL 输入与输出。

上一轮 600 秒演示最终因 SSH 连接重置退出，不能计为稳定性通过。
本轮已重新连接并确认板卡冷初始化完成；只有新固件通过整板时序并冷部署后，才能报告提速幅度。
