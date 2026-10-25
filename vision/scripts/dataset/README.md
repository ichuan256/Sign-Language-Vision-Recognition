# 数据审计工具

`audit_labels_sources.py` 读取全画幅清单、来源 CSV、媒体元数据和 R3 既有缓存，
检查标签别名、文件哈希、来源回溯及划分相关性；不会重标、删媒体或训练模型。

输入主清单：`vision/data/manifests/manifest_fullframe_20261024.csv`，媒体路径仍按仓库根解析。

```powershell
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 vision/scripts/dataset/audit_labels_sources.py
```

默认报告：`vision/analysis/dataset/label_source_audit_20261025.md/.json`。
可用 `--output-prefix` 将复跑结果写入新快照；既有日期是对应数据版本的快照名，
新增素材后应使用新的输出名。当前样本与补采入口：
[analysis/dataset/README.md](../../analysis/dataset/README.md)。
