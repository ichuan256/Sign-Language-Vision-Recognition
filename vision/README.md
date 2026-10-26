# 视觉模块：代码来源与目录入口

当前主线是 **无语义关键点 → 独立板端实时叠加**。本目录同时保留旧词语识别管线与历史证据，
不能把每个文件夹都当成当前训练或部署入口。

## 代码来自哪里

主仓库：[ichuan256/Sign-Language-Vision-Recognition](https://github.com/ichuan256/Sign-Language-Vision-Recognition)，
当前 Git remote 为 `git@github.com:ichuan256/Sign-Language-Vision-Recognition.git`。
HDMI/音频从原 `pld-sign-glove` 工程移植到 `project/`、`ASR/`；视觉 M1 继承其中的输入/骨架特征基础，
本项目随后新增了网页视觉嵌入识别、无语义关键点、HDMI 回放和 PL 关键点工作。
`vision/` 不是某个单一第三方视觉仓库的原样副本。

| 内容 | 来源及边界 |
|---|---|
| `framesource/`、`keypoints/` | 本项目维护的输入接口、关键点运行、数据/评测和显示连接代码；使用 MediaPipe/OpenCV 库 |
| `src/signrec/`、`webapp/`、`m1/`、`classify/` | 本项目维护的旧视觉嵌入/DTW、网页与词语基线；不是当前学生网络 |
| `src/signrec/_vendor/opencv_zoo/` | 明确复制保留的第三方封装；上游固定在 `47534e27c9851bb1128ccc0102f1145e27f23f98`，见 [来源与许可](src/signrec/_vendor/opencv_zoo/README.md) |
| `models/` 中的 ONNX | OpenCV Zoo 的 MobileNetV2、person/pose 预训练模型，各子目录 README 记录模型来源与哈希 |
| 手部关键点教师 | 本机 MediaPipe 安装中的预训练模型，导出报告记录版本/哈希；不在 `vision/models/` 重复存放 |
| 新学生网络 | 本项目定义，配置在 [project/algo/keypoints](../project/algo/keypoints/README.md)；本地试训权重和原始报告在 `project/_tmp/`，尚未作为通过精度验收的模型发布 |

上述是代码/模型来源；视频素材来源另见 [数据入口](data/README.md)。

## 当前工作只看这些入口

| 工作 | 入口 |
|---|---|
| 输入文件、USB 与单目 OV5640 占位 | [framesource/](framesource/) |
| PC 关键点与显示连接 | [keypoints/README.md](keypoints/README.md) |
| 独立实时学生网络与板内流水线 | [当前方案](../docs/方案/03_Zynq7020独立实时关键点方案.md) |
| 教师导出、训练、评测、HLS 和板端脚本 | [project/scripts/keypoints](../project/scripts/keypoints/README.md) |
| 已部署 0.49 秒 PL 基线 | [实际证据](../project/analysis/keypoints_pl_20261026/stream_wide.md) |

当前目标摄像头为单目 OV5640，尚未实测。`keypoints/HDMI_REPLAY.md` 记录现有 PC 回放通路，
不等于最终独立板端通路。新模型的理论 MAC 缩减也不等于板端已达到 20Hz。

## 其余目录的职责

| 分类 | 目录 | 使用约定 |
|---|---|---|
| 旧词语/网页管线 | `src/signrec/`、`webapp/` | 视觉嵌入＋DTW 演示，保留原运行入口 |
| 旧骨架词语基线 | `m1/`、`classify/`、`manifests/` | 不同口径的历史实验，不能与无语义学生训练混用 |
| 共享骨架特征 | `sign_video/` | 392 维特征契约与批量提取，仍被旧管线引用 |
| 日常/历史辅助脚本 | [scripts/](scripts/README.md)、[tools/](tools/README.md) | 清单审计、模板工具、剪辑和历史双目工具；不是全部都需要运行 |
| 模型和模板资产 | `models/` | 旧 ONNX/DTW 模板，新学生配置与权重不放这里 |
| 元数据与本地媒体 | [data/](data/README.md)、`video/` | 清单可入库，视频本体不入库 |
| 分析与历史证据 | [analysis/](analysis/README.md) | 按实验口径保存；日期快照不作为当前操作卡 |
| 回归测试 | [tests/](tests/README.md) | 代码验证，不能代替板端/摄像头验收 |

目前同时存在顶层 Python 包和旧 `src/signrec` 结构，是多轮移植、合并后的结果。
整理时以当前入口为准；物理移动需同步导入、CLI、清单基准路径和测试，不能只移动文件夹。
