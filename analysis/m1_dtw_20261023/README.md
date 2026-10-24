# M1 识别线首轮：FrameSource + DTW 基线（2026-10-23）

> 历史实验快照：26 类/90 条。当前数据看 [数据入口](../dataset/README.md)，
> 此记录不同于 `vision/m1/README.md` 的 8 类/28 条实验。

电脑侧闭环第一版已跑通：视频文件 → MediaPipe Holistic → sign_xy_v1
392 维时序特征 → 掩码感知 DTW 模板分类。识别逻辑全程只依赖
`FrameSource` 抽象，后续换 USB 摄像头 / 板端 HDMI in / OV5640 时只新增
FrameSource 实现，特征与分类器零改动（对应总体方案 §4）。

## 本次落地的代码

| 模块 | 内容 |
|---|---|
| `vision/framesource/` | FrameSource 抽象契约 + VideoFileSource + USBCamSource；`read() → (BGR帧, 帧号, 时间戳)`；降采样/限帧率下沉到源层 |
| `vision/keypoints/holistic.py` | HolisticTracker：任意 FrameSource → sign_xy_v1（与 extract.py 同契约） |
| `vision/classify/dtw.py` | 掩码感知帧代价（xy/速度/手形三块，无效维双端剔除）+ 归一化时间窗 DTW + TemplateClassifier |
| `vision/classify/segment.py` | 动态分割：手腕速度能量 + 起止迟滞 + 时长过滤（连续流输入用，本轮仅合成数据验证） |
| `vision/classify/evaluate.py` + `run_m1_baseline.py` | LOO 与 source_group 留出两套评估协议，分别出数、永不混报 |
| `vision/manifests/build_m1_manifest.py` | 从 wsy 全画幅清单按"≥3 段"规则生成 26 类/90 段词表 manifest（含 sha256） |

单元测试 19 项全绿（含修正一处随仓库迁移的旧导入 `algo.` → `vision.`）。

## 数据与口径

- 语料：`video/done/wsy/全22课全画幅样本_fullframe_264条_20261021/`，
  352×288 @ 20 fps，15 fps 采样提取，90/90 段成功，平均双手覆盖率 63.9%
  （漏检由显式掩码兜底，不做插值——沿用源工程数据契约）。
- **LOO 的 0.422 是本实验同源素材的留一片段命中率，不是跨人物泛化准确率；人物身份未逐条确认。**
- 唯一诚实的泛化读数：谢谢跨 p01/p04 的 group hold-out = **0/4**，双向皆错。
  该小样本结果提示跨来源能力不足，不能单独证明模型依赖了哪种外观信号。

## 主要读数

- LOO 分层大：3 类回放量 1.00（对不起我不知道/很抱歉我迟到了/我是志愿者，
  均为 3–4 段小样本），8 类为 0（多为 5–7 字长句，互相混淆严重，
  高频误吸方向是"很抱歉我迟到了"）。
- 混淆呈"长度/句法相似吸聚"特征：祝你旅途愉快→很抱歉我迟到了 3/4、
  今天天气怎么样→很抱歉我迟到了 3/3。单字/双字（很、早上、谢谢）明显好于长句。
- 谢谢 hold-out 中 top-3 距离与正确标签差距不大（0.077 vs 0.103），
  基线有信号但区分度不足，不是完全没学到。

## 已知限制与下一步

1. 词表未定（方案 D4）：本轮是 26 类可行性摸底，不是定版词表。建议下一步
   定 5–10 个**短动态手势**词表（单/双字优先，如 很、早上、谢谢、新年好），
   并补录未见分组/未见录制者样本，否则无诚实准确率可报。
2. 人物身份没有逐条核验，不能根据 wsy 目录认定素材均为同一人；跨人物评测需补 performer_id。当前样本总览见 [数据入口](../dataset/README.md)。
3. 低分辨率 352×288 下右手覆盖率仅 41–66%，若升级素材分辨率/码率，
   掩码负担会显著下降；摄像头实时线（USBCamSource + segment +
   TemplateClassifier）已具备接通条件，缺的是定版词表与阈值标定。
4. 动态分割仅在合成数据上验证过；接入连续流（摄像头/HDMI in）时需用
   真实连续素材复测 segment 参数。
5. 距离阈值/拒识尚未标定：当前分类器永远输出最近模板，没有"以上都不是"。

## 复现

```powershell
F:/PLD/.venv-vision/Scripts/python.exe vision/manifests/build_m1_manifest.py
F:/PLD/.venv-vision/Scripts/python.exe -X utf8 -m vision.sign_video.extract `
  --manifest vision/manifests/m1_vocabulary_20261023.json `
  --output analysis/m1_dtw_20261023/features --fps 15
F:/PLD/.venv-vision/Scripts/python.exe -X utf8 -m vision.classify.run_m1_baseline `
  --manifest vision/manifests/m1_vocabulary_20261023.json `
  --npz-dir analysis/m1_dtw_20261023/features `
  --output analysis/m1_dtw_20261023/eval   # 目录必须不存在
F:/PLD/.venv-vision/Scripts/python.exe -m pytest vision/tests -q
```

产物：`features/`（90 个 npz + report.json + 预览图）、`eval/`（report.json + README.md）。
