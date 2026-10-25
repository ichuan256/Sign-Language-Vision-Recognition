# 单手 21 点先行：模型与 MAC 计算核阶段（2026-10-25）

这是模型与独立 MAC 核阶段的历史快照；后续完整网络、整板构建和部署状态见 [整网上板记录](single_hand_board.md)。

用户已确认按“单手关键点子网先落 PL、再扩展双手/身体”实施。
**本阶段已完成浮点转换、定点候选评估和 MAC 核 C/RTL 验证；完整关键点网络尚未上 PL。**
结构化实测见 [single_hand_stage1.json](single_hand_stage1.json)，
源代码/复跑入口见 [scripts/keypoints](../../scripts/keypoints/README.md)。

## 浮点模型转换

保留已安装 hand-landmark-lite 权重，重建成 tf-keras；输出 63 个 ROI x/y/z 值与 1 个手存在分数，
不输出词语类别，不使用 world-landmark 头，也没有把网络模型换成未训练的小 CNN。
模型共 968640 个参数，原模型 SHA256 为
`048edd3645c9bf7397d19a9f6e3a42957d6e414c9bea6598030a2e9b624156e6`。

3 个合成输入 + 28 个真实 ROI 上，对原 TFLite 的最大坐标误差 0.000923 ROI 单位，
手存在分数误差 0.00000221。通过的是数值转换对齐，不是人工标注定位精度。
ROI 使用现有关键点指导旋转裁剪；PC 提供 ROI 是第一阶段的明确前提，不是 PL 自主检测。

输入为 224×224 RGB、[0,1]；坐标输出仍在模型 ROI 单位，z 不是公制深度。
预处理/输出头依据 [MediaPipe v0.10.21 官方图](https://github.com/google-ai-edge/mediapipe/blob/v0.10.21/mediapipe/modules/hand_landmark/hand_landmark_cpu.pbtxt)。

## 定点候选：不能只报好看的部分

21 个 ROI 用于校准，7 个 ROI 来自未用于校准的 NL08/09/10 来源组。
这是数值探针，数量很小；不是跨人物准确率，不能代表任意输入视频。
激活 16bit、累加 48bit，权重按输出通道用二进制尺度量化；参考使用整数值卷积，
每个乘加的保守边界检查小于 float64 精确整数范围，平均池化/移位/查表仍需全网络独立 C/RTL 对齐。

| 权重 | 所有 7 ROI 坐标最大漂移 | 原浮点接受的 5 ROI 最大漂移 | 存在分数最大差 | 门控决策变化 |
|---|---:|---:|---:|---:|
| 8bit | 22.13 | 12.02 | 0.20674 | 1/7 |
| 12bit | 14.06 | 1.58 | 0.01677 | 0/7 |
| 16bit | 13.11 | 0.99 | 0.01944 | 1/7 |

“接受”严格使用 presence **>0.5**，与 [官方阈值计算器](https://github.com/google-ai-edge/mediapipe/blob/v0.10.21/mediapipe/calculators/util/thresholding_calculator.cc)一致；
未接受 ROI 的坐标并不直接发布，但仍保留其原始漂移，不删除失败输入。
8bit 候选不达当前原型精度目标；12bit 可作为进一步门控验证的候选，**不是最终定版或已部署结果**。
16bit 仍有近阈值门控翻转，说明单纯提高权重位宽不替代整条定点链路验证。

## 为什么采用 DDR 与计算核复用

单 ROI 约 145562816 次 MAC；957152 个卷积/全连接核权重。
12bit 紧凑权重约 1.44MB（16bit 容器约 1.91MB），最大中间激活 802816×16bit≈1.61MB。
旧 W6 历史报告只余 96 BRAM36 Tile，约 432KiB；不能把权重和特征全片上存储。
这不等于模型不能上 FPGA，而是必须采用外部 DDR、分块和计算核复用等架构。

16 路 MAC、100MHz 时，仅理想算术量对应约 91ms/ROI；这不含 DDR、图调度和其他算子，
**不是 PL 实测延迟或 11fps 性能保证**。双手还需独立评估分时处理代价。

## MAC 分块核验证

源：`project/algo/keypoints/kp_gemm_tile.*`。16 路、输入/权重 16bit 容器、48bit 累加，
每输出通道独立移位，最近偶数舍入和 16bit 饱和。bias 的 DDR 容器是 64bit，限制有效范围 48bit。

- Vitis HLS 2024.1、xc7z020clg400-1，目标周期 10ns。
- CSim：6 组向量、596 输出，**0 LSB**；含真实首层卷积的 16 位置×16 通道子块。
- XSim C/RTL co-sim：**PASS**；另测非法尺寸拒绝，合计 7 个事务。
- HLS 估计：LUT **9944**、DSP **24**、FF **8124**、BRAM18K **23**，估计周期 **7.300ns**。
- 这只是 MAC 核资源，不是全网络或整板实现。未做布局布线、未生成 bit、未下载板卡。

本机完整证据：`project/_tmp/kp_tile_hls_v4/`，含 build.tcl、console.log、csynth XML 和 cosim 报告。
早期 v1 的 ap_int 三目表达式类型歧义已修正；v2 首层误假定只有 16 个通道也已修正，
实际首层为 24 通道，当前测试取其前 16 通道子块。失败日志保留，不覆盖。
验证按 vivado-hardware-fastflow 的轻量路线停在模拟/综合，不把 RTL 仿真称作上板验收。

## 仍需完成

1. 全网络独立整数 C 对齐，尤其 depthwise、残差、池化、均值及 presence 查表；扩大低置信度 ROI 探针。
2. DDR 图调度、权重布局和非 MAC 算子，验证整张图的实际吞吐。
3. AXI/PS 驱动与现有 HDMI 工程集成，再做整板综合/实现与 bit/hwh 成对发布。
4. 按冷启动流程部署，实测 PC ROI→PL 坐标→叠加 HDMI 的延迟，不能复用 PC 的计时冒充。

当前 PC Holistic→HDMI 演示未被此原型替换；单目 OV5640 仍为输入接口占位。

工程回归：117 项测试通过；目录、素材路径、原 bit/hwh 哈希及文档链接检查通过。
