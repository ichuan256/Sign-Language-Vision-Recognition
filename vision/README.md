# 视觉模块：代码来源与目录入口

当前主线是 **PS 老师关键点网络 → PL 局部加速 → 板端叠加**。本目录同时保留旧词语识别管线与历史证据，
不能把每个文件夹都当成当前训练或部署入口。

最新 [P1 进展](../project/analysis/teacher_partition_20261028/p1.md)：PS 后处理等价优化和原老师子图边界重放已验证，
下一步测单个连续分区接图开销；尚无新 PL 固件或加速验收，不需要标注/训练。

2026-10-26 已完成物理归并，主目录收敛为：

```text
vision/
  src/       # 所有运行源码：vision 包与旧 signrec 包
  scripts/   # 命令行/审计脚本，历史生成器放 legacy/
  tests/     # 回归测试
  data/      # 清单、模型与旧特征缓存
  analysis/  # 分析和历史证据
  tools/     # 剪辑与便携工具
  video/     # 本地视频，路径保持原样，不入库
```

根 `__init__.py` 只负责把 `src/vision` 加入包搜索路径，因此 `python -m vision.keypoints...`、
`vision.m1...`、`vision.webapp...` 仍可从仓库根运行；源码没有保留两份。

## 代码来自哪里

主仓库：[ichuan256/Sign-Language-Vision-Recognition](https://github.com/ichuan256/Sign-Language-Vision-Recognition)，
当前 Git remote 为 `git@github.com:ichuan256/Sign-Language-Vision-Recognition.git`。
HDMI/音频从原 `pld-sign-glove` 工程移植到 `project/`、`ASR/`；视觉 M1 继承其中的输入/骨架特征基础，
本项目随后新增了网页视觉嵌入识别、无语义关键点、HDMI 回放和 PL 关键点工作。
`vision/` 不是某个单一第三方视觉仓库的原样副本。

| 内容 | 来源及边界 |
|---|---|
| `src/vision/framesource/`、`src/vision/keypoints/` | 本项目维护的输入接口、关键点运行、数据/评测和显示连接代码；使用 MediaPipe/OpenCV 库 |
| `src/signrec/`、`src/vision/{webapp,m1,classify}/` | 本项目维护的旧视觉嵌入/DTW、网页与词语基线 |
| `src/signrec/_vendor/opencv_zoo/` | 明确复制保留的第三方封装；上游固定在 `47534e27c9851bb1128ccc0102f1145e27f23f98`，见 [来源与许可](src/signrec/_vendor/opencv_zoo/README.md) |
| `data/models/` 中的 ONNX | OpenCV Zoo 的 MobileNetV2、person/pose 预训练模型，各子目录 README 记录模型来源与哈希 |
| 手部关键点教师 | 本机 MediaPipe 安装中的预训练模型，导出报告记录版本/哈希；不在 `vision/data/models/` 重复存放 |
| 历史学生网络 | 已停止训练与部署推进；本地实验原件保留，不作为当前运行入口 |

上述是代码/模型来源；视频素材来源另见 [数据入口](data/README.md)。

## 当前工作只看这些入口

| 工作 | 入口 |
|---|---|
| 输入文件、USB 与单目 OV5640 占位 | [framesource/](src/vision/framesource) |
| PC 关键点与显示连接 | [keypoints/README.md](src/vision/keypoints/README.md) |
| PS 老师网络的 PL 局部加速 | [当前方案](../docs/方案/04_老师模型PS_PL局部迁移.md) |
| PS full 老师与开发工具 | [老师运行入口](../project/board/teacher_hands/README.md)、[工具说明](../project/scripts/keypoints/README.md) |
| 历史 lite 整网 PL 基线 | [日期证据](../project/analysis/keypoints_pl_20261026/stream_wide.md)，不代表当前板上状态 |

`src/vision/keypoints/HDMI_REPLAY.md` 记录 PC 回放通路，不等于板端独立推理。
真实摄像头采集状态单独按硬件记录核对，不把播放率或理论 MAC 当作推理速度。

## 当前老师模型

板端手部基线为原版 MediaPipe `palm_detection_full.tflite` 与 `hand_landmark_full.tflite`，
通过 TFLite ARMv7 运行；模型结构和权重保持不变。它与 PC Holistic 的完整身体/双手管线范围不同。
当前加速验证对照冻结老师输出，不再导出伪标签训练学生。模型 SHA 与输出契约见
[板端说明](../project/board/teacher_hands/README.md)。素材数量和来源以 [数据入口](data/README.md) 为准。

## 其余目录的职责

| 分类 | 目录 | 使用约定 |
|---|---|---|
| 旧词语/网页管线 | `src/signrec/`、`src/vision/webapp/` | 视觉嵌入＋DTW 演示，保留原运行入口 |
| 旧骨架词语基线 | `src/vision/{m1,classify}/`、`data/manifests/` | 不同口径的历史实验，不能与无语义学生训练混用 |
| 共享骨架特征 | `src/vision/sign_video/` | 392 维特征契约与批量提取，仍被旧管线引用 |
| 日常/历史辅助脚本 | [scripts/](scripts/README.md)、[tools/](tools/README.md) | 清单审计、模板工具、剪辑和历史双目工具；不是全部都需要运行 |
| 模型、模板和旧缓存 | `data/models/`、`data/cache/m1/` | 旧 ONNX/DTW 资产，缓存不当人工标签 |
| 元数据与本地媒体 | [data/](data/README.md)、`video/` | 清单可入库，视频本体不入库 |
| 分析与历史证据 | [analysis/](analysis/README.md) | 按实验口径保存；日期快照不作为当前操作卡 |
| 回归测试 | [tests/](tests/README.md) | 代码验证，不能代替板端/摄像头验收 |

物理目录由 `project/scripts/check_layout.py --code-only` 检查；会拒绝重新在顶层散放 `keypoints/` 等源码目录。
