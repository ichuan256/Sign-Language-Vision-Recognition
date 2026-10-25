# PYNQ-Z2 移植与视频输入高动态手势识别总体方案

设计基线日期：2026-10-23。实施状态已更新，见 [仓库入口](../../README.md)；
当前样本见 [数据入口](../../vision/analysis/dataset/README.md)，PL 分类器见 [R3 入口](../../project/analysis/r3/README.md)。
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
5. 识别逻辑要可复用，后续把视频输入换成 **OV5640 双目** 时只换输入、不改识别。

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

### 1.3 释放出的板卡资源（对 §3 双目至关重要）

不移植传感器后，**Pmod A（JA）、Pmod B（JB）、Arduino D0–D13 全部空出**。
这正是后续 OV5640 双目的物理接入位置，移植时约束文件里这些引脚不再占用。

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

> **2026-10-23 用户决策：OV5640 双目确定为摄像头方案，且与直接图像输入共用
> 同一套识别逻辑（§4 的 FrameSource 契约保证）。M2 整段暂缓——若最终演示
> 不需要外部 HDMI 视频源进板，则跳过 M2 直奔 M3；HDMI-in 仅作为带宽/延迟
> 彩排手段保留在备选。**

- 在 M1 识别逻辑不动的前提下，给板端 BD **新增 hdmi_in 子系统**
  （dvi2rgb + VDMA 采集，PYNQ base 有现成结构；源工程 W6 当年"只做输出"
  的取舍在此处补齐）；
- 帧去向两条可选：
  - a) 采集帧经网络/USB 回传电脑跑识别（改动小，推荐先走通）；
  - b) 直通环回 + OSD 叠加识别结果（FPGA 内 video in → out，识别仍电脑）；
- 意义：验证"外部视频源 → 板 → 识别 → 板端显示"的完整链路与带宽，
  为双目上板做带宽与延迟摸底；
- 验收：720p 输入连续采集无丢帧、环回画面稳定、识别帧率 ≥ 30 fps。

### 阶段 M3：OV5640 双目（复用识别的最终输入）

- 接入位置：释放出的 JA + JB（+ 必要时 Arduino IO）。单目 OV5640 并口
  需 8bit 数据 + PCLK/VSYNC/HREF + SCCB 约 12 个信号，一个 Pmod 只有
  8 信号，双目规划：JA 走左目数据、JB 走右目数据，控制线（SCCB/复位/
  电源使能，双目 SCCB 可共总线分地址）放 Arduino D0–D5；
- 信号完整性是最大风险：Pmod 排线承载 OV5640 典型 24MHz+ PCLK 很勉强，
  缓解手段为降低分辨率（先用 640×480 或更低）降低 PCLK、短软排线、
  约束内加输入延迟校准；备选方案是双目 USB 摄像头（识别逻辑完全不变，
  仅再写一个 `FrameSource` 实现）；
- PL 侧新增：OV5640 采集控制器（SCCB 配置 + 并口采样 + 行缓存）、
  双目时间戳对齐（双目帧同步打标，给后续视差/双手空间关系用）、
  VDMA 写 DDR；
- 识别逻辑**零改动**：双目先按"左目主识别、右目辅助"接入，后续再评估
  立体信息对高动态动作的收益；
- 验收：双目同采帧率、左右目时间戳偏差、端到端识别准确率不劣于 M1 基线。

## 4. 识别逻辑复用架构（核心设计）

换输入只换一层，其余不动：

```
VideoFile / USBCam / HdmiIn / OV5640Mono / OV5640Stereo
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
缺失帧零填充 + 掩码，不插值。OV5640 双目接入时唯一新增的是
`OV5640StereoSource` 实现和（可选的）双目同步字段，特征与分类器不动。

## 5. 待确认决策点

- **D1 工程重建路线**：源文档明确"W6 从空目录重建尚未验收"。两条路：
  (a) 保底——直接部署已发布 `kws_hdmi.bit/hwh` 点亮，Vivado 工程稍后重建；
  (b) 彻底——复制整个 `fpga/project/glove` 工程目录（含 .xpr）到新位置
  原地改名重建 BD。**建议先 (a) 点亮保底，再并行推进 (b)**。
- **D2 阶段 M2 是否必须**：若演示场景的视频源本来就在电脑上，HDMI 输入
  可整段跳过，直奔 M3 双目；HDMI in 的价值取决于最终演示形态。
- **D3 旧 HLS KWS 去留**：`kws_hdmi.bit` 内含旧 HLS KWS 加速器，新系统
  用电脑 ASR 已够。剥离可省 PL 资源（留给视频核），但需重出固件；
  不剥离则 M0 零风险。建议 M0 保留、M2 重建时剥离。
- **D4 词表与素材**：动态手势词表先定 5～10 个（可沿用"你好/早上好/谢谢"
  等已有素材但须先复核切片语义——源工程已发现标签与画面字幕不一致问题）。
- **D5 双目硬件**：**已定**——OV5640 双目为确认方案（2026-10-23），与直接
  图像输入共用识别逻辑；模组（含排线）×2 的采购与转接方式待定，
  Pmod 直插 vs 自制转接板影响 M3 排期。

## 6. 里程碑与验收

| 里程碑 | 内容 | 验收证据 |
|---|---|---|
| M0 移植点亮 | 资产拷入、新仓库结构、已发布 bit/hwh 板上点亮 720p + 音频 LINE IN 通路复验 | 目视画面 + 音频回路录音，对照 release_manifest |
| M0b 工程重建 | Vivado 2024.1 从新仓库脚本重建 HDMI+音频 BD，时序通过，与基线画面一致 | w6_timing/utilization 报告 + 目视 |
| M1 识别闭环 | 文件/摄像头 → 392 维特征 → DTW 基线 → 上位机 + HDMI 字幕 | 未见样本分组准确率报告、延迟实测 |
| M2 板端视频输入 | HDMI in 采集/环回，识别帧率 ≥ 30 fps | 连续运行无丢帧记录 |
| M3 OV5640 双目 | 双目采集上板，识别逻辑零改动接入 | 端到端准确率对照 M1、双目同步偏差 |

## 7. 主要风险

1. **W6 重建未验收**（源文档明示）——M0 用已发布固件保底，重建单独立项；
2. **HDMI 黑屏根因**（寄存器片 TUSER_WIDTH=0 切断 SOF）——构建脚本含幂等修复，
   任何 HLS 重导出/工具升级后必须重跑网表检查；
3. **OV5640 走 Pmod 的信号完整性**——降分辨率、短线、备选 USB 双目兜底；
4. **素材标签与动作语义不一致**（2026-10-20 已发现）——训练前必须人工复核切片；
5. **覆盖率 ≠ 准确率**——沿用源工程口径，不以关键点覆盖率宣称识别能力；
6. 换 bitstream 会硬复位板子（2026-10-15 实测）——音频与视频显示若需共存，
   必须合一固件，不能运行时反复加载 overlay。
