# 通用关键点 PL 部署前置检查（2026-10-25）

**初始前置检查结论：当时尚未部署，停在模型/设计检查阶段。** 用户目标是把身体/双手关键点提取搬到 PL，
不是再部署词语分类器，也不是把 PC 结果传回 HDMI 冒充 PL 推理。
原始结构、模型 SHA256、算子清单和资源依据见 [preflight.json](preflight.json)。

以上为最初前置检查快照。用户随后已确认单手 21 点先行，最新实施状态见
[单手阶段记录](single_hand_stage1.md)：浮点转换及 MAC 核 C/RTL 验证已完成，完整关键点尚未上板。

## 已核对的事实

- 当前 Holistic 顶层包含 PoseLandmarkCpu、HandLandmarksLeftAndRightCpu、
  SplitNormalizedLandmarkListCalculator 和 FaceLandmarksFromPoseCpu。身体/双手需求可以不保留表情输出，
  但这不等于已拆出可综合网络。
- 已安装模型使用 TFLite：身体检测输入 224×224×3，身体关键点输入 256×256×3，
  手部关键点 full/lite 均输入 224×224×3。它们的输入输出为 FLOAT32，部分权重存为 FLOAT16；
  当前不是已验证的整数 PL 推理图。
- 手关键点 full/lite 分别约 5.48MB / 2.07MB；文件大小不是 LUT、DSP 或必需片上内存估算，
  不能仅据此宣称“能放下”或“绝对放不下”。
- 本机 hls4ml 1.3.0 有 Keras/ONNX/PyTorch 等入口，没有直接 TFLite 转换入口。
  需要额外验证中间格式转换、算子语义、布局和量化；不是换文件后缀。
- 仓库已有 R3 是 14 类词语 CNN，**不输出关键点坐标**。其 CSim/综合结果不能代替本任务。
- 现有历史 W6 布线报告使用 14710/53200 LUT、95/220 DSP、44/140 BRAM Tile；
  算术剩余 38490 LUT、125 DSP、96 BRAM Tile，不是新加速器已通过资源/时序门禁。

## 为什么没有直接生成/下载 bit

缺少已验证的定点关键点图、ROI/跟踪分工、HLS/RTL 加速器、C/RTL 对齐、AXI 集成和匹配 bit/hwh。
Vivado、Vitis HLS 和旧工程都存在，但不能综合一个尚未实现的关键点 IP。
本轮未生成或执行 Tcl，未运行综合/实现，未生成 bit、未重载固件、未重启板卡。

## 建议分阶段实施，需确认阶段范围

1. **单手 21 点关键点子网先落 PL**：PC 暂时提供规范化手部 ROI，PL 输出 21×3 坐标及辅助分数；
   验证浮点/定点误差、单 ROI 延迟和资源。此阶段只是子网 PL 推理，不能称整链路板端自主。
2. 用同一硬件实例分时处理左右手；实测双手延迟，不能把单手帧率直接写成双手帧率。
3. 加入身体/手部检测及 ROI/跟踪在 PS/PL 的实现，脱离 PC 的关键点计算。
4. PS 从录制视频提供像素模拟输入，PL 推理，板端叠加并走 HDMI；单目 OV5640 保留后续输入接口。
5. 通过定点对齐、资源/时序、整板 bit/hwh 和端到端验收后，才能报告“PL 自主提取关键点”。

阶段 1 的 hand-landmark-lite 是候选，不是已替换当前模型。是否接受单手子网先行，
或要求首阶段同时交付身体与双手，需由用户确定；未获确认前不静默缩减功能。
这里不需要手语词义标签，但量化校准、关键点误差检查和独立视频评测仍不能省略。

## 复跑前置检查

```powershell
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 project/scripts/keypoints/pl_preflight.py --mediapipe-root F:/PLD/.venv-vision/Lib/site-packages/mediapipe --output project/_tmp/keypoints_pl_preflight_new
```

输出目录必须不存在；只读取外部已安装模型，所有新产出保留在仓库内。
