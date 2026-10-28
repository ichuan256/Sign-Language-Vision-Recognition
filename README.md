# Sign-Language-Vision-Recognition

PYNQ-Z2 手语识别系统·新主线：**视频输入 → 高动态手势识别**，保留 HDMI 显示与音频线
（HDMI/音频资产自 `pld-sign-glove` 移植，不使用传感器手套识别线）。识别管线与输入源解耦，
目标输入为单目 OV5640；录制视频与相机采集/显示候选分别验证，采集状态按硬件证据核对。历史 W6 固件含闲置传感器/KWS 实例，新候选按资源预算处理。

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

## 当前阅读入口（2026-10-28）

- **当前任务**：[PS 教师网络的 PL 局部加速方案](docs/方案/04_老师模型PS_PL局部迁移.md)。冻结 full 老师结构与权重，首轮只迁一个热点子图；停止学生训练、蒸馏和 QAT。
- **老师运行入口**：[板端 full palm + landmark](project/board/teacher_hands/README.md)；[实际模型图与候选边界](project/analysis/teacher_partition_20261028/README.md)。新局部加速尚未实现，静态 MAC 不是板端速度。
- **PC 关键点工具**：[启动与指标](vision/src/vision/keypoints/README.md)。PC 回放/推理与板端独立推理分开计时。
- **系统与工具**：[总体方案](docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md)、[开发工具入口](project/scripts/keypoints/README.md)、[操作约束](AGENTS.md)。
- **素材**：[素材约定](docs/协作/素材工作区约定.md)、[样本入口](vision/analysis/dataset/README.md)、[媒体清单修复](docs/协作/媒体清单修复_20261026.md)。551 条活动池与 85 条待审版分开；本轮不为训练扩数据。
- **历史证据**：[旧 lite 整网 PL 实测](project/analysis/keypoints_pl_20261026/stream_wide.md)、[raw 帧缓冲吞吐](project/analysis/keypoints_pl_20261026/raw_video.md)、[R3 词语分类器](project/analysis/r3/README.md)。这些都不是新 full 老师局部加速结果。

## 已验收与待验收范围

- **M0 移植**：HDMI+音频合一工程已从本仓库干净重建出 bitstream 并**通过板端验收**
  （部署哈希一致、720p 画面目视确认、LINE IN 左声道信号正常）；
  证据见 [移植验收](project/M0_移植清单.md)。
- **BTN0 一键启动**：通电后按板载 BTN0，约 1 秒开始音频识别演示（ASR 模型 PC 开机预载，
  板端 button-watch.service 监听按键）。链路与用法见 `AGENTS.md` §4b。
- **历史 M1 识别基线**：8 类 28 条已审定精剪片段，DTW 留出法基线已跑通；
  滑窗实时识别演示（文件源流式输入）端到端命中。结果与口径说明见
  `vision/src/vision/m1/README.md`。
- **OV5640 → HDMI 720p 本地候选（2026-10-28）**：[预览启动说明](project/board/ov5640_snapshot/HDMI_PREVIEW.md)、[固件与验证记录](project/analysis/ov5640_hdmi_20261028/README.md)。新固件已完成综合/实现、内部时序与配对校验；本轮板卡未开机，尚未部署或进行屏幕验收。
- **本轮待验收**：PS 老师同条件基线、算子剖析、单段 PL 接入、全部输出一致性和端到端净提速；真实摄像头与身体网络分别核对，不计入手部迁移已完成范围。

## 快速开始

```powershell
# PC 关键点工具（不作为本轮板端 PS 基线；输出目录必须是新的）
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.keypoints.live_demo --source "replay:<视频.mp4>" --loop --fps 20 --seconds 60 --headless --output project/_tmp/keypoints/replay_new

# FPGA 构建（Vivado 2024.1，必须走 cmd 批处理）
project\fpga\scripts\run_w6_hdmi.bat
project\fpga\scripts\launch_w6_build.bat
```

详细操作卡片与踩坑表见 [AGENTS.md](AGENTS.md)；系统级方案见
[docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md](docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md)。
