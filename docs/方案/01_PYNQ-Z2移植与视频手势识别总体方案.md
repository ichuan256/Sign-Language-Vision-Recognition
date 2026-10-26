# PYNQ-Z2 移植与视频输入高动态手势识别总体方案

设计基线日期：2026-10-23。实施状态已更新，见 [仓库入口](../../README.md)；
当前样本见 [数据入口](../../vision/analysis/dataset/README.md)，PL 分类器见 [R3 入口](../../project/analysis/r3/README.md)。
2026-10-25 当前实施顺序：**录制视频按实时节拍模拟摄像头 → 无语义关键点叠加 → 板卡 HDMI**，
连续播放已目视确认，见 [操作卡](../../vision/keypoints/HDMI_REPLAY.md)。目标摄像头改为单目 OV5640，未到货，仅接口留位。
2026-10-26 用户选定后续视觉线独立上板方向：轻量关键点网络与板内视频流水线，见
[独立实时关键点专题](03_Zynq7020独立实时关键点方案.md)。已测 PL 基线仍约 0.49 秒/ROI；
新专题中的 20Hz 双手与低延迟指标为待验证目标，当前不计作已实现。
源工程：`F:\PLD\pld-sign-glove`（妙手通言）。目标仓库：`F:\PLD_new\Sign-Language-Vision-Recognition`（随 git 上传）。

> 本文保留移植与视频识别线的总体设计基线。源工程既有的接口冻结、
> 数据契约、验证结论继续有效；本文只做移植裁剪与新增路线的规划，
> 各阶段是否实现以对应验收/实验记录为准。

## 0. 需求理解与范围界定

用户要求：

1. 把 PYNQ-Z2 工程从 `F:\PLD` 移植到 `F:\PLD_new\Sign-Language-Vision-Recognition`；
2. **不移植传感器部分**（十路弯曲 + 四颗 IMU 的 W3 采集链、W5 姿态链全部剥离）；
3. **只移植 HDMI 通路和音频线**（"听觉线"按音频线理解：ADAU1761 采集 +
   LINE IN → 电脑 ASR → HDMI 字幕/视频显示这条已复验的闭环）；
4. 在此基础上新增 **视频输入 → 高动态手势识别**；
5. 识别逻辑要可复用，后续把视频输入换成 **单目 OV5640** 时复用帧源契约；真实硬件仍需独立验收。

当前 W6 合一固件仍含闲置传感器 SPI/DMA 与旧 HLS KWS，不能称为“无传感器固件”。
本系统不使用传感器识别链；物理剥离属于 M0b 待办，需后续重建与验收。

## 1. 移植资产清单

### 1.1 移植（HDMI + 音频线）

| 资产 | 源路径（F:\PLD\pld-sign-glove 下） | 说明 |
|---|---|---|
| HDMI 输出 IP | `fpga/ip_repo/rgb2dvi_v1_2`、`axi_dynclk_v1_0`、`color_swap_1.1`、`if/tmds_v1_0` | 逐层复刻 PYNQ v3.0.1 base 的 hdmi_out，`pynq.lib.video` 零改动可用 |
| 音频 IP | `fpga/ip_repo/audio_codec_ctrl_v1.0` | ADAU1761 控制，地址 0x43C00000，`pynq.lib.audio` 零改动可用 |
| HLS 视频 IP | `algo/video_hls/pixel_unpack`、`color_convert` | 需先跑 `run_video_hls.bat` 导出 |
| BD 脚本 | `fpga/scripts/w6_audio_bd.tcl`、`w6_hdmi_bd.tcl`、`w6_hdmi_build.tcl`、`w6_bitgen_only.tcl`、`vivado_build_common.tcl` | w6_hdmi_bd.tcl 含 TUSER 黑屏幂等修复，必须保留 |
| 约束 | `fpga/xdc/hdmi_w6.xdc`、`audio_w6.xdc`、（`w6_interfaces.xdc` 按需裁剪） | 引脚与时钟约束 |
| 板端脚本 | `board_validation/w6/`：`hdmi_display.py`、`hdmi_renderer.py`、`hdmi_audio_receiver.py`、`boot.py` 等 | HDMI 原位绘制与音频接收的已验证入口 |
| 已发布固件 | `board_validation/w6/kws_hdmi.bit/.hwh` + `release_manifest.json` + `baseline_20261018_visible/` | 移植后第一轮点亮的保底基线 |
| 音频上位机 | `ps/asr/`（sherpa-ncnn 流式识别，剔除 `recog_live_ncnn.py` 中的 `BaseOverlay("base.bit")` 行为） | 音频闭环的电脑侧 |
| 视觉特征提取 | `algo/sign_video/`（MediaPipe Holistic → 392 维 `sign_xy_v1`） | 视频识别线的既有基础，整体搬入 |

### 1.2 不移植（传感器部分）

- RTL：`sensor_if_spi.v`、`spi_master.v`、`ts_align.v`、`mahony_pe.v`、
  `merge_stream*.v`、`bringup_seq.v`、`axi_lite_regs.v`、`kws_mlp_accel.v`
  （旧 HLS KWS 是否保留见 §5 决策点 D3）；
- 脚本：`w1/w2/w3/w4/w5*` 全部 tcl/bat；
- 约束：`sign_glove_master.xdc`、`w3_data_acquire.xdc`、`w2_bringup.xdc`；
- 算法：`algo/` 下的 `attitude_*`、`imu_*`、`quaternion.py`、`dma_receiver.py`、
  `features.py`、`dtw.py`（传感器版）、`svm_baseline.py` 等；
- 文档：W2/W3 接线、引脚冻结表中 Pmod 传感器部分（保留表格但标注"已释放"）。

### 1.3 待释放的板卡资源

目标是在 M0b 剥离闲置传感器逻辑后释放相应 Pmod/Arduino 资源；
当前固件仍含旧传感器模块，不能直接宣称全部引脚空闲。
单目 OV5640 的模组电平、时钟和管脚接法待硬件确认，不沿用旧双目引脚假设。

## 2. 新工程结构（仓库 F:\PLD_new\Sign-Language-Vision-Recognition 内，随仓库上传）

```
Sign-Language-Vision-Recognition\
  project\                  # 新板端工程（沿用源工程目录约定）
    fpga\ip_repo\               # rgb2dvi / axi_dynclk / color_swap / audio_codec_ctrl / tmds if
    fpga\scripts\               # 更名后的 w6_* 构建脚本 + 新增 hdmi_in / ov5640 脚本
    fpga\xdc\                   # hdmi.xdc / audio.xdc（后续 hdmi_in.xdc / ov5640.xdc）
    fpga\project\glove\         # Vivado 2024.1 工程（xc7z020clg400，薄拷贝，工程名暂保留 glove）
    algo\video_hls\             # pixel_unpack / color_convert（路径与 w6_hdmi_bd.tcl 推导一致）
    board\w6\                   # hdmi_display.py 等板端脚本 + kws_hdmi bit/hwh 发布区
  vision\                       # 视频手势识别（自 algo/sign_video 演进）
    framesource\                # §4 的输入抽象层
    keypoints\  features\  classify\
  ASR\                          # 音频线上位机（自 ps/asr 裁剪）
  vision\video\                        # 现有视频素材库（gitignore，不上传）
  docs\                         # 本方案及后续接口冻结
```

原则：源工程只读，所有文件**复制**进新仓库后再改；旧工程不回写。
2026-10-23 更新：应用户要求，全部移植资产已归入待上传仓库
`Sign-Language-Vision-Recognition`，正文路径以该仓库根为基准。

## 3. 视频输入 → 高动态手势识别：三阶段路线

"高动态"按快速、带方向和大位移的双手动作理解。端到端指标目标（初定，可调整）：
采样 ≥ 30 帧/秒、识别延迟 < 200 ms、限定词表（先 5～10 个动态手势）分组交叉验证。

### 阶段 M1：文件/摄像头识别闭环（最先做，纯电脑）

- 输入：`FrameSource` 的文件源与 USB 摄像头源；
- 流水线：帧 → 预处理（锐化默认关闭，沿用 2026-10-20 对照结论）→
  MediaPipe Holistic 关键点 → `sign_xy_v1` 392 维时序特征 →
  **动态分割 + 分类器**；
- 分类器分两档：先 DTW 模板基线（数据少时可用），再轻量时序网络
  （TCN 或 GRU，~100K 参数级，电脑训练，后续可量化部署）；
- 动态分割：手腕速度幅值 + 有效掩码的起止检测，替代人工切片；
- 显示：识别结果低频文字经网络下发，板端 HDMI 原位绘制字幕
  （复用 `hdmi_display.py` 通路，不重载固件）；
- 验收：同一词表未见样本的逐类准确率 + 覆盖率，已见回放单独标注；
  同源切片/增强必须同分组（沿用源工程数据契约）。

### 阶段 M2：板端 HDMI 输入（视频源上板）

> **2026-10-25 用户更新：目标摄像头为单目 OV5640，尚未到货。当前先用录制视频模拟输入，
> 经 PC 叠加后走板卡 HDMI OUT，不等于 HDMI IN 采集已实现。M2 继续暂缓。**

- 在 M1 识别逻辑不动的前提下，给板端 BD **新增 hdmi_in 子系统**
  （dvi2rgb + VDMA 采集，PYNQ base 有现成结构；源工程 W6 当年"只做输出"
  的取舍在此处补齐）；
- 帧去向两条可选：
  - a) 采集帧经网络/USB 回传电脑跑识别（改动小，推荐先走通）；
  - b) 直通环回 + OSD 叠加识别结果（FPGA 内 video in → out，识别仍电脑）；
- 意义：验证"外部视频源 → 板 → 识别 → 板端显示"的完整链路与带宽，
  为后续摄像头上板做带宽与延迟摸底；
- 验收：720p 输入连续采集无丢帧、环回画面稳定、识别帧率 ≥ 30 fps。

### 阶段 M3：单目 OV5640（硬件到货后实施）

- 当前只提供 `OV5640MonoSource` 占位；读取会明确报未实现，不假装 USB 或文件是真实相机。
- 到货后先确认模组接口、电平、时钟、可用引脚与旧固件资源冲突，再设计采集和约束。
- 目标采集帧仍按 `FrameSource` 返回 BGR、帧号、时间戳；不要求下游依赖摄像头品牌。
- 本阶段先验收真实帧率、丢帧、关键点覆盖和 HDMI 叠加延迟，不把词义分类作为采集前置条件。
- 旧 `OV5640StereoSource` 仅保留历史接口兼容，不再作为当前采购或双目同步实施计划。

## 4. 识别逻辑复用架构（核心设计）

换输入只换一层，其余不动：

```
VideoFile / Replay / USBCam / HdmiIn / OV5640Mono
            │  统一接口 FrameSource：read() → (BGR帧, 帧号, 时间戳)
            ▼
      预处理（锐化可选、缩放、色彩）      ← 与源无关
            ▼
      关键点提取（MediaPipe Holistic，双手42+身体9点）
            ▼
      特征 sign_xy_v1（392维，肩宽归一化，速度单位肩宽/秒）
            ▼
      动态分割 + 分类（DTW 基线 / TCN / GRU）
            ▼
      结果事件（标签, 置信度, 起止, 拒识）→ 上位机 / 板端HDMI字幕
```

硬性约定（沿用源工程教训）：二维坐标做分类候选，不混用不同模型的 z 原点；
肩宽归一化保证跨摄像头、跨距离可比；同源增强归同一数据分组；
缺失帧零填充 + 掩码，不插值。当前运行链路在关键点提取后直接叠加原画并回传 HDMI，
不运行下方特征分类。单目采集接入后复用同一帧源契约，但输入画质、时序和性能必须重测。

## 5. 待确认决策点

- **D1 工程重建路线**：源文档明确"W6 从空目录重建尚未验收"。两条路：
  (a) 保底——直接部署已发布 `kws_hdmi.bit/hwh` 点亮，Vivado 工程稍后重建；
  (b) 彻底——复制整个 `fpga/project/glove` 工程目录（含 .xpr）到新位置
  原地改名重建 BD。**建议先 (a) 点亮保底，再并行推进 (b)**。
- **D2 阶段 M2 是否必须**：若演示场景的视频源本来就在电脑上，HDMI 输入
  可整段跳过，直奔 M3 单目；HDMI in 的价值取决于最终演示形态。
- **D3 旧 HLS KWS 去留**：`kws_hdmi.bit` 内含旧 HLS KWS 加速器，新系统
  用电脑 ASR 已够。剥离可省 PL 资源（留给视频核），但需重出固件；
  不剥离则 M0 零风险。建议 M0 保留、M2 重建时剥离。
- **D4 词表与素材**：动态手势词表先定 5～10 个（可沿用"你好/早上好/谢谢"
  等已有素材但须先复核切片语义——源工程已发现标签与画面字幕不一致问题）。
- **D5 摄像头硬件**：2026-10-25 更新为**单目 OV5640**，尚未到货；
  模组与转接接线待实物确认，当前先做录制视频模拟输入与 HDMI 叠加，不实施双目方案。

## 6. 里程碑与验收

| 里程碑 | 内容 | 验收证据 |
|---|---|---|
| M0 移植点亮 | 资产拷入、新仓库结构、已发布 bit/hwh 板上点亮 720p + 音频 LINE IN 通路复验 | 目视画面 + 音频回路录音，对照 release_manifest |
| M0b 工程重建 | Vivado 2024.1 从新仓库脚本重建 HDMI+音频 BD，时序通过，与基线画面一致 | w6_timing/utilization 报告 + 目视 |
| M1 识别闭环 | 文件/摄像头 → 392 维特征 → DTW 基线 → 上位机 + HDMI 字幕 | 未见样本分组准确率报告、延迟实测 |
| M2 板端视频输入 | HDMI in 采集/环回，识别帧率 ≥ 30 fps | 连续运行无丢帧记录 |
| M3 单目 OV5640 | 实物到货后实现采集，复用帧源接口 | 采集帧率/丢帧、关键点与 HDMI 叠加实测 |

## 7. 主要风险

1. **W6 重建未验收**（源文档明示）——M0 用已发布固件保底，重建单独立项；
2. **HDMI 黑屏根因**（寄存器片 TUSER_WIDTH=0 切断 SOF）——构建脚本含幂等修复，
   任何 HLS 重导出/工具升级后必须重跑网表检查；
3. **OV5640 接口与信号完整性**——待模组确认后设计电平、时钟和接线，不提前假定 Pmod 分配；
4. **素材标签与动作语义不一致**（2026-10-20 已发现）——训练前必须人工复核切片；
5. **覆盖率 ≠ 准确率**——沿用源工程口径，不以关键点覆盖率宣称识别能力；
6. 换 bitstream 会硬复位板子（2026-10-15 实测）——音频与视频显示若需共存，
   必须合一固件，不能运行时反复加载 overlay。
