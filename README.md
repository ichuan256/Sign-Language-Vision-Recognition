# Sign-Language-Vision-Recognition

PYNQ-Z2 手语识别系统·新主线：**视频输入 → 高动态手势识别**，保留 HDMI 显示与音频线
（自 `pld-sign-glove` 移植，**不含传感器手套部分**）。识别管线与输入源解耦，
后续通过帧源适配接入板端 HDMI 输入或 OV5640 双目，仍需验证输入与时序契约。

## 仓库结构

| 目录 | 内容 |
|---|---|
| `pynq-vision/` | 板端工程：Vivado 2024.1 工程（xc7z020clg400）、IP 仓库、构建脚本、板端脚本、已发布与新构建固件 |
| `vision/` | 视频手势识别：帧源抽象 `framesource/`、流式关键点 `keypoints/`、DTW 基线 `classify/`、特征提取 `sign_video/`、M1 运行器与结果 `m1/` |
| `asr/` | 音频线上位机（sherpa-onnx 流式 ASR → HDMI 字幕/手语视频连播） |
| `docs/方案/` | 总体方案与接口约定 |
| `analysis/` | 数据现状、PL 状态与历史实验证据，见 [分析入口](analysis/README.md) |
| `scripts/` | 运行与复跑工具；数据审计在 `dataset/`，量化/HLS 在 `r3/` |
| `data/` | 数据清单、历史素材与导出产物，见 [数据目录](data/README.md) |
| `tools/` | 剪裁/核验和便携工具，见 [工具入口](tools/README.md) |
| `video/` | 素材库（**不入库**，线下共享；精剪清单 CSV 在库内） |
| `AGENTS.md` | 工具链操作手册（构建/部署/踩坑，接手必读） |

共享素材交接见 [共享包说明](docs/协作/共享包说明.md)，网页依赖在
`webapp/requirements.txt`。新增清单、导出数据、便携工具均放入对应目录，避免根目录平铺。

## 当前阅读入口（2026-10-25）

- [样本现状与补采](analysis/dataset/README.md)：数据总量、标签问题与下一轮采样设计。
- [PL 路线状态](analysis/r3/README.md)：量化基线、CSim 对齐、资源门禁；当前模型未部署。
- [系统总体方案](docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md) 与
  [PL 分类器方案](docs/方案/02_路线3_PL加速板端离线识别设计.md)：目标架构和接口。

## 已验收与待验收范围

- **M0 移植**：HDMI+音频合一工程已从本仓库干净重建出 bitstream 并**通过板端验收**
  （部署哈希一致、720p 画面目视确认、LINE IN 左声道信号正常）；
  产物与对照见 `pynq-vision/board_validation/w6/timing_candidate/`。
- **BTN0 一键启动**：通电后按板载 BTN0，约 1 秒开始音频识别演示（ASR 模型 PC 开机预载，
  板端 button-watch.service 监听按键）。链路与用法见 `AGENTS.md` §4b。
- **M1 识别基线**：8 类 28 条已审定精剪片段，DTW 留出法基线已跑通；
  滑窗实时识别演示（文件源流式输入）端到端命中。结果与口径说明见
  `vision/m1/README.md`。
- **待验收**：跨人物识别、数据语义清洗和补采、PL 分类器资源达标与板端部署；
  OV5640 双目采集仍属后续输入路线，接口复用不代表硬件已实现。

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
