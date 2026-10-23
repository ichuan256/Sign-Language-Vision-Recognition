# Sign-Language-Vision-Recognition

PYNQ-Z2 手语识别系统·新主线：**视频输入 → 高动态手势识别**，保留 HDMI 显示与音频线
（自 `pld-sign-glove` 移植，**不含传感器手套部分**）。识别管线与输入源解耦，
后续可切换为板端 HDMI 输入或 OV5640 双目，识别逻辑零改动。

## 仓库结构

| 目录 | 内容 |
|---|---|
| `pynq-vision/` | 板端工程：Vivado 2024.1 工程（xc7z020clg400）、IP 仓库、构建脚本、板端脚本、已发布与新构建固件 |
| `vision/` | 视频手势识别：帧源抽象 `framesource/`、流式关键点 `keypoints/`、DTW 基线 `classify/`、特征提取 `sign_video/`、M1 运行器与结果 `m1/` |
| `asr/` | 音频线上位机（sherpa-onnx 流式 ASR → HDMI 字幕/手语视频连播） |
| `docs/方案/` | 总体方案与接口约定 |
| `video/` | 素材库（**不入库**，线下共享；精剪清单 CSV 在库内） |
| `AGENTS.md` | 工具链操作手册（构建/部署/踩坑，接手必读） |

## 当前进度（2026-10-23）

- **M0 移植**：HDMI+音频合一工程已从本仓库干净重建出 bitstream
  （`write_bitstream Complete!`，WNS=+1.244 ns，6 分钟），产物与对照见
  `pynq-vision/board_validation/w6/timing_candidate/`；板端点亮验收待板子上线。
- **M1 识别基线**：8 类 28 条已审定精剪片段，DTW 留出法基线已跑通；
  滑窗实时识别演示（文件源流式输入）端到端命中。结果与口径说明见
  `vision/m1/README.md`。
- 下一步：板端点亮复验 → USB 摄像头实测 → M2 板端 HDMI 输入。

## 快速开始

```powershell
# 视觉识别（Python 环境 F:\PLD\.venv-vision，仓库根目录运行）
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.live_demo --source file:<片段.mp4> --templates vision/m1/runs/extract_part1 vision/m1/runs/extract_part2 vision/m1/runs/extract_part3

# FPGA 构建（Vivado 2024.1，必须走 cmd 批处理）
pynq-vision\fpga\scripts\run_w6_hdmi.bat
pynq-vision\fpga\scripts\launch_w6_build.bat
```

详细操作卡片与踩坑表见 [AGENTS.md](AGENTS.md)；系统级方案见
[docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md](docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md)。
