# 单手关键点整网与上板记录

**单手关键点完整网络已在 PYNQ-Z2 的 PL 上运行，64 个输出对整数参考逐值一致，HDMI 叠加已由用户目视确认。**
当前是 PC 提供 ROI 的功能原型，单 ROI 前向 12.28 秒，尚未达到实时。
结构化实测与发布哈希见 [single_hand_board.json](single_hand_board.json)。
本记录接续 [模型与 MAC 核阶段](single_hand_stage1.md)，不替代原始探针精度边界。

## 实现范围

PC 提供 224×224 RGB 规范化单手 ROI；PS 负责索引、分块、DDR 数据搬运和输出尺度还原。
卷积、depthwise、全连接、残差、ReLU、最大池化、均值和 sigmoid 都调用 PL MAC / vector 核。
硬件运行路径没有 CPU 神经网络回退。身体、手部检测、自动 ROI 和双手并行尚未实现。

整网使用 A16/W12、48bit 累加，权重存入 DDR。16 路 MAC 分时复用；当前 depthwise
展开为稀疏矩阵，便于先验证正确性，运算和搬运均有额外成本。这是功能原型，不是实时性能定版。

## 已完成门禁

| 门禁 | 结果 | 本机完整证据 |
|---|---|---|
| 独立 HLS C 执行完整网络 | 7 ROI 对整数参考全部逐值相同，最大差 0 | `project/_tmp/kp_graph_c_v3/report.json` |
| MAC C/RTL co-sim | PASS，含非法尺寸拒绝 | `project/_tmp/kp_mac_ip_v1/` |
| vector C/RTL co-sim | PASS，8 组、2056 输出、0 LSB | `project/_tmp/kp_vector_ip_v1/` |
| 整板综合 | LUT 31556/53200，DSP 117/220，BRAM Tile 59/140 | `project/_tmp/kp_system_v3/utilization_synth.rpt` |
| 布局布线 | LUT 28387/53200（53.36%），FF 37455/106400，DSP 117/220，BRAM Tile 59/140 | `project/_tmp/kp_system_v3/utilization_routed.rpt` |
| 时序/布线 | WNS 0.623ns、WHS 0.008ns，TNS/THS=0；61463 条可布线网络全部完成、0 错误 | `project/_tmp/kp_system_v3/` |
| 实际 PL 整网 | 1 ROI、64 输出，最大差 0；presence=0.7578125；无 CPU 神经网络回退 | `project/_tmp/kp_board_result_v1/` |
| HDMI | 静态 ROI 与 PL 坐标叠加，60 秒有界接收；用户确认骨架正常 | `project/_tmp/kp_board_hdmi_v1/` |
| 软件回归 | 123 项通过，2 条既有 protobuf 警告 | `vision/tests/` |

每个 ROI 调用 MAC 4846 次、vector 1047 次。PC 上编译执行 HLS C 的时间不是板端时间。
原定点探针与浮点模型之间的漂移仍适用：7 ROI 最大坐标漂移 14.06，浮点接受的 5 ROI 最大漂移 1.58；
这不是人工标注的定位准确率，也不证明任意视频泛化。

## 整板工程与部署约束

从旧工程导出设计配置，在 `project/_tmp/kp_system_v3/` 创建独立 Vivado 工程；
保留 HDMI、音频、按键和原有闲置模块，通过空闲 HP3 接入两个新计算核。
MAC 控制地址 `0x43C20000`，vector `0x43C30000`，计算时钟 100MHz。
补齐旧 W6 的 HDMI 约束禁用项和接口约束加载顺序；通过 setup、hold 和时钟方法学检查后才导出候选。
原来的 `project/fpga/rtl/` 未修改。

板端先备份当前 bit/hwh，再成对替换并冷重启；不修改 boot.py / systemd，也不运行中重载 FPGA。
驱动从生成的 HLS 寄存器头提取偏移；板端核对候选哈希、重启 ID 和冷启动完成状态后，仅 `download=False` 接管。
已核对新 boot ID、启动服务完成和候选 bit/hwh 哈希，随后运行实际推理。
原固件备份位置与完整部署清单位于本机 `project/_tmp/kp_board_deploy_v2/deployment.json`。
首次传输的校验清单因 CRLF 失败，未替换固件；改为 LF 后通过。Windows SSH 在重启断连时返回
UINT32_MAX，已通过新 boot ID 和哈希确认成功，没有二次加载或再次重启。

保留的工程告警包括 TIMING-18 外部 I/O 延迟预算、厂商转换器 LUTAR-1、控制集使用建议；
没有 TIMING-4/27/36，bus-skew 报告最小裕量 8.816ns。时序门禁通过不等于全部外部接口完成电气验收。

## 延迟实测与下一步

以下是一次独立进程、一个规范化 ROI 的测量，没有包含摄像头、视频解码和手部检测。

| 阶段 | 耗时 |
|---|---:|
| 板端完整前向：PL 运算＋PS 调度/数据搬运 | **12.276 秒** |
| 一次性 Overlay 元数据、缓冲区和模型初始化 | 14.139 秒 |
| 板端初始化＋前向 | 26.415 秒 |
| SSH 请求开始至板端进程返回 | 31.732 秒 |

前向按算子分组：普通卷积 4.623 秒、depthwise 3.989 秒、ReLU 3.387 秒、残差 0.184 秒、
其余约 0.094 秒。它们包含各层调度和搬运，不能写成纯 PL 内核时间。
当前等效吞吐约 0.081 ROI/s，未测稳态分布或双手吞吐；HDMI 的刷新率也不是关键点更新率。

优先优化方向：合并卷积与 ReLU/残差，减少 5893 次 PS 发起；专用 depthwise 避免稀疏矩阵浪费；
复用 DDR 中间张量和权重，减少逐块复制及缓存操作；随后把检测/ROI、连续视频输入和叠加计时接起来。
每次改动仍需整数对齐与板端复验，再谈双手/身体、OV5640 和最终实时指标。
旧 PC Holistic 视频回放仍是独立演示入口，本次静态图不代表该视频链路已改成实时 PL 推理。

本机候选位于 `project/_tmp/kp_system_v3/release/hand_hdmi.bit/.hwh`；旧 W6 发布文件未覆盖。
旧 ASR 启动器仍按自己的固件清单核验，本次没有将新固件宣称为音频回归通过版本；
HDMI 接管新候选时显式使用本记录 JSON 的 `--release-manifest`。
