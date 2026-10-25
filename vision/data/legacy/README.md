# 历史数据

- `material/`：原裁剪域样本与 `dataset_manifest_20261020.csv`，不是当前全画幅语料。
- `material_fullframe_20261021/`：旧版清单副本，不包含该清单列出的全部媒体，不能当作完整训练集。

本轮只迁移路径；`material` 清单中的输出前缀已改为 `vision/data/legacy/material/`，
标签、原片时间、哈希和视频内容未变。旧模板与单元测试仍可引用这些样本。
当前全画幅语料入口在根目录 `vision/video/done/` 与 [清单](../manifests/README.md)。
