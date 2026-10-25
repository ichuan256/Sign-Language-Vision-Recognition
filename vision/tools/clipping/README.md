# 剪裁与核验工具

> 当前目录为 `vision/tools/clipping/`；清单在 `vision/data/manifests/`，正式精剪素材仍在 `vision/video/done/`。
> 新导出默认进入 `vision/data/exports/`，检查图进入 `project/_tmp/`。以下是历史导出流程，
> FFmpeg 和原片位置需按本机配置核对，不代表所有脚本在当前机器已重新验收。

本文件夹保存按“已确认时间边界 + 保留原视频尺寸”生成手语视频的方法。
现有**两套管线**，输出规格不同，各按各的清单与验收执行：

- **A. 全 22 课样本数据集**（`export_fullframe_dataset.py`，2026-10-21，wsy）
- **B. P08–P10 逐词句精剪**（`detect_boundaries_20261022.py` + `cut_reviewed_20261022.py`，2026-10-22，Tomcat）

> **2026-10-22 布局变更**：视频本体不再入库，统一放入仓库根目录 `vision/video/`
> （git 忽略、线下传播，结构见 `vision/video/剪辑任务分布记录.md` 与 `docs/协作/共享包说明.md`）。
> A 的数据集视频在 `vision/video/done/wsy/全22课全画幅样本_fullframe_264条_20261021/`，
> 清单/说明在 `vision/data/manifests/全22课_fullframe/`；
> B 的片段在 `vision/video/done/Tomcat/`，机检清单在 `vision/data/manifests/P08_购物`、`P09_聚会`、`P10_旅游/`，
> 逐课边界与审修细节见同目录 P08/P09/P10 精剪说明。

## 共同规则（A/B 均适用）

1. 不按固定矩形裁剪画面，保留全画幅，手部、面部与上肢完整可见。
2. 字幕与词卡内容不参与裁剪验收。
3. 输出写入独立目录，不覆盖旧数据集。
4. 模糊的“约某秒到某秒”范围不用于自动新增样本。

## A. 全 22 课样本数据集（352×288）

1. 时间边界取自 `全部22parts_训练样本清单_20261020.csv`（现收录于 `vision/data/manifests/全22课_fullframe/`）。
2. 输出规格：352×288、20 fps、无音轨、H.264；第一课动作周期（31 段）例外，保留原片 1920×1080、25 fps（见其导出说明）。

运行（项目根目录）：

```powershell
python .\vision\tools\clipping\export_fullframe_dataset.py            # 重新导出
python .\vision\tools\clipping\export_fullframe_dataset.py --skip-encode  # 只核验不重新编码
```

输出文件已存在时默认停止防误覆盖；确认重写加 `--overwrite`。

输入：`全部22parts_训练样本清单_20261020.csv`（225 条已确认样本及精确起止秒）、
`全部22parts_不确定与不足项_20261020.csv`、p01–p22 原片、本地 FFmpeg。
脚本另保留 8 条曾因旧固定裁剪被淘汰、但有明确时间窗的候选（百货、个、大、中国、烤鸭、交往、他们、旅游，带 `_全画幅` 后缀）。

输出与机检：`<类别>/<样本>.mp4`、`dataset_manifest_fullframe_20261021.csv`、
`validation_fullframe_20261021.json`；逐条检查输出路径、352×288、20 fps、无音轨、
时长、完整解码，并重新计算 SHA256。

## B. P08–P10 逐词句精剪（1920×1080）

1. 候选与时间窗取自 `中国手语教程_10课_逐词句剪裁策略_20261021.csv`（词句已读图核对）。
2. 边界确定：运动能量自动检测 → 起点/终点邻域核验图逐条人工目检，
   对话/单人轮次另按逐秒总览图重排 → 审定结果落盘各课
   `中国手语教程_P0x_已审定动作边界_20261022.csv`（起始秒/结束秒_不含/复核状态/核对说明）。
3. 输出规格（策略表「建议输出规格」）：1920×1080 全画幅、24 fps、H.264/yuv420p、无音轨。
4. 重复示范（同一候选窗内两次独立示范）逐次核对后各导出一条，分 `_C1/_C2`；
   「单示范+长保持」被误分段的合并为一条。
5. 精剪按审定表执行并逐条机检：分辨率、帧率、无音轨、时长偏差 <0.3 s、完整解码，
   结果写入各课 `manifest_P0x_reviewed_20261022.csv`（无 SHA256 列）。

运行（以第 10 课为例）：

```powershell
python .\tools\clipping\detect_boundaries_20261022.py --lesson 10 --from 0 --to 100
# 人工目检 _inspect_frames/P10/strips/ 与逐秒总览图，修正后写审定 CSV
python .\tools\clipping\cut_reviewed_20261022.py --csv <审定表> --jobs 5
```

注意：`--to` 为切片下标（不含），候选总数 100 时须写 `--to 100`，否则漏末条。
逐课特点与人工修正统计见 `P08精剪说明_20261022.md`、`P09精剪说明_20261022.md`、`P10精剪说明_20261022.md`。
