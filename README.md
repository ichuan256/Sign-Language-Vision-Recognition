# Sign-Language-Vision-Recognition

PYNQ-Z2 手语识别系统·新主线：**视频输入 → 高动态手势识别**，保留 HDMI 显示与音频线
（HDMI/音频资产自 `pld-sign-glove` 移植，不使用传感器手套识别线）。识别管线与输入源解耦，
目标输入为单目 OV5640；录制视频与相机采集/显示候选分别验证，采集状态按硬件证据核对。历史 W6 固件含闲置传感器/KWS 实例，新候选按资源预算处理。

**接手先读[当前状态](docs/当前状态.md)**：当前AV候选的彩条、静态三栏和实时视觉已实屏确认；音频交付、指定语音闭环和稳定性继续联调，运行/暂停状态以统一入口为准。

## 仓库结构

| 目录 | 内容 |
|---|---|
| [ASR/](ASR/README.md) | 音频识别、上位机启动器与音频演示 |
| [docs/](docs/README.md) | 总体方案、接口约定与协作记录 |
| [vision/](vision/README.md) | 当前关键点代码，以及保留的旧词语/网页管线；入口解释代码来源与目录职责 |
| [project/](project/README.md) | FPGA/板端工程、教师局部迁移工具、历史R3/HLS证据与构建日志 |

根目录仅保留这四个主目录，以及 `README.md`、`AGENTS.md` 和 Git 必需文件。

共享素材交接见 [共享包说明](docs/协作/共享包说明.md)，网页依赖在
`vision/src/vision/webapp/requirements.txt`。新增清单、导出数据、便携工具均放入对应目录，避免根目录平铺。

## 当前阅读入口

- **现场状态与控制**：[统一状态](docs/当前状态.md)、[演示控制台](docs/演示控制台.md)、[旧版与三栏差异](docs/视听三栏_旧版对比_20261101.md)。
- **视觉加速**：[PS教师网络PL局部加速方案](docs/方案/04_老师模型PS_PL局部迁移.md)。冻结full教师结构与权重，首轮只迁一个热点子图；停止学生训练、蒸馏和QAT。
- **老师运行入口**：[板端 full palm + landmark](project/board/teacher_hands/README.md)；[实际模型图与候选边界](project/analysis/teacher_partition_20261028/README.md)。新局部加速尚未实现，静态 MAC 不是板端速度。
- **PC 关键点工具**：[启动与指标](vision/src/vision/keypoints/README.md)。PC 回放/推理与板端独立推理分开计时。
- **系统与工具**：[总体方案](docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md)、[开发工具入口](project/scripts/keypoints/README.md)、[操作约束](AGENTS.md)。
- **素材**：[素材约定](docs/协作/素材工作区约定.md)、[样本入口](vision/analysis/dataset/README.md)、[媒体清单修复](docs/协作/媒体清单修复_20261026.md)。551 条活动池与 85 条待审版分开；本轮不为训练扩数据。
- **历史证据**：[旧 lite 整网 PL 实测](project/analysis/keypoints_pl_20261026/stream_wide.md)、[raw 帧缓冲吞吐](project/analysis/keypoints_pl_20261026/raw_video.md)、[R3 词语分类器](project/analysis/r3/README.md)。这些都不是新 full 老师局部加速结果。

## 已验收与待验收范围

- **历史M0移植**：当时HDMI+音频合一工程从本仓库干净重建，并通过对应W6板端验收
  （部署哈希一致、720p 画面目视确认、LINE IN 左声道信号正常）；
  证据见 [移植验收](project/M0_移植清单.md)。
- **历史W6 BTN0**：曾实现按键启动电脑ASR及HDMI演示；最近OV候选不含该按钮链，旧监听已禁用。仅对应旧固件的用法见`AGENTS.md` §4b。
- **历史 M1 识别基线**：8 类 28 条已审定精剪片段，DTW 留出法基线已跑通；
  滑窗实时识别演示（文件源流式输入）端到端命中。结果与口径说明见
  `vision/src/vision/m1/README.md`。
- **OV显示**：[固件兼容关系](project/board/ov5640_snapshot/README.md)。当前AV候选的720p彩条、静态三栏和实时视觉已获实屏确认；指定语音、字幕及对应手语播放的联合验收仍待完成。
- **语音词表**：[最新扩展](docs/语音词表扩展_cfx567_20261031.md)，557项映射、575种写法、563份视频，SD同步核验完成；最近固件的视听联合播放尚待验收。
- **教师迁移**：P1已验证PS后处理等价优化与边界重放，下一步测CPU分区接图及拆分损耗，再决定HLS；实际PL接入和端到端净收益未完成。真实相机、PC Holistic与PS手部教师分别验收。

## 快速开始

```powershell
# PC 关键点工具（不作为本轮板端 PS 基线；输出目录必须是新的）
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.keypoints.live_demo --source "replay:<视频.mp4>" --loop --fps 20 --seconds 60 --headless --output project/_tmp/keypoints/replay_new

# 历史W6构建示例，仅用于该旧固件，不生成最近OV视听候选
# Vivado 2024.1，必须走cmd批处理；最近候选看发布包自身构建记录
project\fpga\scripts\run_w6_hdmi.bat
project\fpga\scripts\launch_w6_build.bat
```

详细操作卡片与踩坑表见 [AGENTS.md](AGENTS.md)；系统级方案见
[docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md](docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md)。
