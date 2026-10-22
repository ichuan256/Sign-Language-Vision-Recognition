# 剪裁方法

本文件夹保存按“已确认时间边界 + 保留原视频尺寸”生成手语视频的方法。

> **2026-10-22 布局变更**：视频本体不再入库，统一放入仓库根目录 `video/`
> （git 忽略、线下传播，结构见 `video/剪辑任务分布记录.md` 与根目录 `共享包说明.md`）。
> 本 README 描述的是 22 课样本数据集（`export_fullframe_dataset.py`）的生成方法；
> 该数据集的视频、manifest、validation 现位于 `video/done/wsy/全22课全画幅样本_fullframe_264条_20261021/`，
> 说明与清单同时收录于 `剪辑记录/全22课_fullframe/`。P08–P10 精剪见同目录 P08/P09/P10 精剪说明。

## 当前规则

1. 不按固定矩形裁剪画面。
2. 时间边界取自 `全部22parts_训练样本清单_20261020.csv`（现收录于 `剪辑记录/全22课_fullframe/`）。
3. 22 课样本统一输出为 352×288、20 fps、无音轨、H.264；第一课动作周期（31 段）保留原片 1920×1080、25 fps。
4. 字幕内容不参与本次裁剪验收。
5. 输出写入数据集目录，不覆盖旧数据集。
6. 模糊的“约某秒到某秒”范围不用于自动新增样本。

## 运行

在项目根目录执行：

```powershell
python .\剪裁方法\export_fullframe_dataset.py
```

只核验已有输出、不重新编码：

```powershell
python .\剪裁方法\export_fullframe_dataset.py --skip-encode
```

输出文件已存在时，默认停止以防止误覆盖；确认要重写时加 `--overwrite`。

## 输入

- `material_fullframe_20261021/全部22parts_训练样本清单_20261020.csv`：225 条已确认样本及精确起止秒。该文件随数据集一起保存，不依赖 `训练视频/`。
- `material_fullframe_20261021/全部22parts_不确定与不足项_20261020.csv`：未纳入候选及处理原因。
- `video/BV1Hs411E7aP_p*.mp4`：p01–p22 原片，是本地剪裁输入，不需要上传。
- `训练视频/.tools/imageio_ffmpeg/binaries/ffmpeg*.exe`：本项目本地 FFmpeg 可执行文件。

脚本另外保留 8 条曾因旧固定裁剪被淘汰、但已有明确时间窗的候选：百货、个、大、中国、烤鸭、交往、他们、旅游。它们只在原尺寸输出时有意义，并带 `_全画幅` 后缀。

## 输出

- `material_fullframe_20261021/<类别>/<样本>.mp4`
- `material_fullframe_20261021/dataset_manifest_fullframe_20261021.csv`
- `material_fullframe_20261021/validation_fullframe_20261021.json`

脚本会逐条检查输出路径、352×288 分辨率、20 fps、无音轨、时长和完整解码，并重新计算 SHA256。
