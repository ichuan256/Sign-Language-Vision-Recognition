# 数据审计工具

`audit_labels_sources.py` 读取全画幅清单、来源 CSV、媒体元数据和 R3 既有缓存，
检查标签别名、文件哈希、来源回溯及划分相关性；不会重标、删媒体或训练模型。

输入主清单：`data/manifests/manifest_fullframe_20261024.csv`，媒体路径仍按仓库根解析。

```powershell
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 scripts/dataset/audit_labels_sources.py
```

默认报告：`analysis/dataset/label_source_audit_20261025.md/.json`。
可用 `--output-prefix` 将复跑结果写入新快照；既有日期是对应数据版本的快照名，
新增素材后应使用新的输出名。当前样本与补采入口：
[analysis/dataset/README.md](../../analysis/dataset/README.md)。

`inventory_video_materials.py` 递归盘点含忽略目录的本地视频，计算SHA、重复组、
旧清单覆盖及可选ffprobe元数据；必须指定不存在的新输出目录，媒体只读。
`organize_workspace_materials_20261025.ps1` 是本次已执行的单次迁移计划，默认仅预检，
`-Apply` 拒绝覆盖目标；整理后不要重新应用，恢复按执行日志中的逆向映射。
实际执行中的工具占用及续作记录见
[执行记录](../../analysis/materials/20261025_organization/执行记录.md)。

用户随后授权清理；历史归档/完整回退ZIP当前已不存在。当前保留范围与清理证据见
[清理记录](../../analysis/materials/20261025_cleanup/清理记录.md)。
`recycle_unused_materials_20261025.ps1`为此次317文件的单次回收操作：默认只检查计划，
`-Apply`发送到Windows回收站，拒绝越界、链接和SHA变化，不清空回收站，执行后不要重复应用。
