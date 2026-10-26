# M1 阶段记录：文件/摄像头 → 动态手势识别闭环（首版基线）

日期：2026-10-23。对应总体方案 §3 阶段 M1。
本阶段全部在电脑侧运行，不连接开发板、不改 FPGA 固件。

## 架构落地情况

按方案 §4 的复用架构实现，识别代码只经 `FrameSource` 接口取帧：

| 模块 | 位置 | 状态 |
|---|---|---|
| 帧源抽象 | `vision/src/vision/framesource/` | `VideoFileSource`、`USBCamSource` 可用；`HDMIInSource`/`OV5640StereoSource` 为 M2/M3 占位，接口已冻结 |
| 关键点（流式） | `vision/src/vision/keypoints/holistic.py` | `HolisticTracker` 消费任意 FrameSource，特征契约与 `sign_video` 批量入口完全一致 |
| 特征 | `vision/src/vision/sign_video/` | 沿用 392 维 sign_xy_v1，未改 |
| 动态分割 | `vision/src/vision/classify/segment.py` | 手腕速度能量 + 迟滞起止，供连续流使用 |
| DTW 基线 | `vision/src/vision/classify/dtw.py` | 掩码感知帧代价 + Sakoe-Chiba 带 + 路径长度归一化 |
| 评估 | `vision/src/vision/classify/evaluate.py` + `vision/src/vision/m1/evaluate.py` | LOO 与按组留出两种协议 |
| 滑窗演示 | `vision/src/vision/m1/live_demo.py` | 文件/USB 源实时滑窗识别 |

## 首版词表与数据

8 类 28 条，全部来自 `vision/video/done` 已审定边界精剪（标注状态
reviewed_boundaries_20261021_22）：谢谢、早上、很、待会儿见（各 4 条，
全画幅组）、再见 2、没关系 3、服务 2、可以。5（跨 NL08/NL09/NL10 课次组）。
清单由 `vision/src/vision/m1/build_manifest.py` 生成（`vision/data/manifests/m1_8class/`），
SHA256 逐条校验，提取分 3 片运行（`vision/data/cache/m1/extract_part1..3`）。

## 首版结果（基线，非最终能力）

- **LOO（已见回放口径）**：28 条总体 32.1%（9/28）。分类：可以。4/5，
  谢谢 2/4，早上 2/4，没关系 1/3，其余 0。该口径同课次片段互为模板，
  不能引用为泛化准确率。
- **按组留出**（测试组 NL09/NL10/第2第3课，3 条跨组样本）：1/3（可以。命中）。
- **滑窗演示**：`1_谢谢.mp4`（自身剔除出模板）经文件源流式播放，
  35 次窗口预测全部命中"谢谢"，与次优类距离差约 5 倍
  （见运行输出；命令见下"复现"）。

结果解读：短促词类（很、服务、待会儿见）类间 DTW 距离接近，是下一步
改进的主要对象；DTW 基线的作用是钉住数据契约与评估口径，不是最终模型。
已知数据问题：`再见` 词表统计为 3 条但仅 2 条进入清单，待核对
"第2 第3课"目录路径。

## 复现

```powershell
# 仓库根目录，视觉环境 F:/PLD/.venv-vision
python -m vision.m1.build_manifest --output vision/data/manifests/m1_8class
python -m vision.sign_video.extract --manifest vision/data/manifests/m1_8class/m1_part1.json --output <新目录> --fps 15
python -m vision.m1.evaluate --features <提取目录>... --output <新目录>
python -m vision.m1.live_demo --source file:<片段路径> --templates <提取目录>... --exclude-id c001
```

## 并行实现合并说明

本阶段进行时发现仓库被另一会话并行写入了同一套 M1 架构
（framesource/keypoints/classify/manifests）。已统一收敛到该实现：
本仓库 classify/framesource 以并行版本为准，`vision/src/vision/m1/` 为数据构建、
评估运行器与滑窗演示；其上修复了两处运行缺口（长度差异过大的模板对在
带内无路径、留出组预测新标签时混淆矩阵 KeyError），修复均在 m1 侧以
子类/健壮汇总实现，未改并行版本文件。旧版 `usb_camera.py`（重名失效）
已删除。后续修改请先确认无并行会话再动手。

## 下一步（M1 收尾 → M2 入口）

1. 核对 `再见` 缺失片段与 `第2 第3课` 目录归组；
2. 特征侧排查短词类混淆（手形块权重、速度块贡献）；
3. 滑窗演示接 USB 摄像头实测一次（`--source usb:0`）；
4. 词表扩到方案 §5 D4 的 5～10 个高动态动作后，再评估是否引入 TCN/GRU。
