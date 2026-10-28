# Sign-Language-Vision-Recognition

PYNQ-Z2 手语识别系统·新主线：**视频输入 → 高动态手势识别**，保留 HDMI 显示与音频线
（HDMI/音频资产自 `pld-sign-glove` 移植，不使用传感器手套识别线）。识别管线与输入源解耦，
目标输入为单目 OV5640；录制视频路线与相机采集/显示候选分别验证。旧固件仍含闲置传感器/KWS 实例，待 M0b 剥离。

## 仓库结构

| 目录 | 内容 |
|---|---|
| [ASR/](ASR/README.md) | 音频识别、上位机启动器与音频演示 |
| [docs/](docs/README.md) | 总体方案、接口约定与协作记录 |
| [vision/](vision/README.md) | 当前关键点代码，以及保留的旧词语/网页管线；入口解释代码来源与目录职责 |
| [project/](project/README.md) | FPGA/板端工程、R3 量化与 HLS、构建缓存与日志 |

根目录仅保留这四个主目录，以及 `README.md`、`AGENTS.md` 和 Git 必需文件。

共享素材交接见 [共享包说明](docs/协作/共享包说明.md)，网页依赖在
`vision/src/vision/webapp/requirements.txt`。新增清单、导出数据、便携工具均放入对应目录，避免根目录平铺。

## 当前阅读入口

- **OV5640 → HDMI 720p 本地版本（2026-10-28）**：[预览启动说明](project/board/ov5640_snapshot/HDMI_PREVIEW.md)、[固件与验证记录](project/analysis/ov5640_hdmi_20261028/README.md)。新固件已完成综合/实现、内部时序与配对校验；本轮板卡未开机，尚未部署或进行屏幕验收。

- [素材工作区约定](docs/协作/素材工作区约定.md)：当前551条SHA一致子集、85条待审版本与原片位置；[清理记录](vision/analysis/materials/20261025_cleanup/清理记录.md)。

- **当前先做无语义的通用实时关键点**：[启动与指标](vision/src/vision/keypoints/README.md)、[文件源基准](vision/analysis/keypoints_20261025/README.md)。摄像头实测待验收，暂不推进词表语义和 PL 分类器。
- **单手关键点子网已上 PL**：[加速实测与延迟](project/analysis/keypoints_pl_20261026/stream_wide.md)。PC 提供 ROI，同一 ROI 三次 64 输出均对整数参考完全一致；12.28→1.86→0.56→0.49 秒/ROI，约 2Hz，仍未达到 5Hz。新版动态 HDMI 已目视确认持续更新。
- **独立实时上板方向**：[轻量网络与板内视频流水线方案](docs/方案/03_Zynq7020独立实时关键点方案.md)。17项人工复核已导入，96/128学生在画外点掩码后完成复训，定位仍未过门禁；[当前结果与边界](project/analysis/keypoints_student_20261027/README.md)。双手各20Hz仍是目标。
- **本轮进展**：[20帧清晰复核](project/analysis/keypoints_student_20261026/清晰复核说明.md)已就绪；[板内raw吞吐](project/analysis/keypoints_pl_20261026/raw_video.md)约24次写入/秒，未含关键点、未目视确认；[媒体清单修复](docs/协作/媒体清单修复_20261026.md)保留551条池并显式登记36个缺失媒体。
- [样本现状与补采](vision/analysis/dataset/README.md)：数据总量、标签问题与下一轮采样设计。
- [PL 路线状态](project/analysis/r3/README.md)：量化基线、CSim 对齐、资源门禁；当前模型未部署。
- [系统总体方案](docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md) 与
  [PL 分类器方案](docs/方案/02_路线3_PL加速板端离线识别设计.md)：目标架构和接口。

## 已验收与待验收范围

- **M0 移植**：HDMI+音频合一工程已从本仓库干净重建出 bitstream 并**通过板端验收**
  （部署哈希一致、720p 画面目视确认、LINE IN 左声道信号正常）；
  产物与对照见 `project/board_validation/w6/timing_candidate/`。
- **BTN0 一键启动**：通电后按板载 BTN0，约 1 秒开始音频识别演示（ASR 模型 PC 开机预载，
  板端 button-watch.service 监听按键）。链路与用法见 `AGENTS.md` §4b。
- **历史 M1 识别基线**：8 类 28 条已审定精剪片段，DTW 留出法基线已跑通；
  滑窗实时识别演示（文件源流式输入）端到端命中。结果与口径说明见
  `vision/src/vision/m1/README.md`。
- **待验收**：跨人物识别、数据语义清洗和补采、PL 分类器资源达标与板端部署；
  单目 OV5640 采集/HDMI 显示候选仍待实际相机与屏幕验收。

## 快速开始

```powershell
# 当前无语义关键点（替换视频路径，输出目录必须是新的）
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.keypoints.live_demo --source "replay:<视频.mp4>" --loop --fps 20 --seconds 60 --headless --output project/_tmp/keypoints/replay_new

# FPGA 构建（Vivado 2024.1，必须走 cmd 批处理）
project\fpga\scripts\run_w6_hdmi.bat
project\fpga\scripts\launch_w6_build.bat
```

详细操作卡片与踩坑表见 [AGENTS.md](AGENTS.md)；系统级方案见
[docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md](docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md)。
