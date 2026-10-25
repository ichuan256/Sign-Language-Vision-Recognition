# 数据清单与剪辑记录

原根目录 `剪辑记录/` 已归入此处。

| 位置 | 用途 |
|---|---|
| `manifest_fullframe_20261024.csv` | 当前全画幅 636 条/440 原标签清单；输出路径指向根目录 `video/` |
| `manifest_available_sha_verified_20261025_r2.csv` | 当前551条可用子集；新增共享包的P09/P10已恢复，全部严格匹配旧审计SHA |
| `manifest_available_sha_verified_20261025_r2.csv.validation.json` | 从636行筛选551行、显式跳过85行的最终逐条记录 |
| `current_available_fullframe.json` | 当前可用子集指针、哈希及统计；不改变模型或实验默认输入 |
| `manifest_available_sha_verified_20261025.csv` | 首阶段349条子集，保留作迁移过程证据 |
| `manifest_available_sha_verified_20261025.csv.validation.json` | 从636行筛选349行、显式跳过287行的逐条记录 |
| `source_registry_current.json`、`source_registry_20261025_clean.csv` | 当前32个原片的路径、来源族和哈希；旧问候单轨已清理 |
| `source_registry_20261025.csv` | 迁移时33个来源/旧单轨文件的历史索引，保留作溯源 |
| `pending_lesson02_03_current.csv` | 当前done/wsy内85条差异版本的实际位置与待审标记，不纳入551子集 |
| `全22课_fullframe/` | 旧全画幅与第一课周期的来源、边界和验收快照 |
| `P08_购物/`、`P09_聚会/`、`P10_旅游/` | 各课精剪验收清单 |
| `w2_上位机全画幅模板与演示记录_20261024.md` | 上位机历史演示与评测记录 |

当前数据结论以 [样本现状](../../analysis/dataset/README.md) 为准。
CSV/JSON 中的旧机器绝对路径属于原始溯源记录，不批量替换为猜测路径。

生成新的可用子集时必须显式提供旧清单、对应审计和未存在的输出文件，
不扫描整个 `video/done`，不覆盖旧日期的清单：

```powershell
C:\Python314\python.exe -B -X utf8 scripts/build_fullframe_manifest_20261024.py --source-manifest data/manifests/manifest_fullframe_20261024.csv --audit analysis/dataset/label_source_audit_20261025.json --output data/manifests/<新的清单名>.csv --allow-missing
```

目录约定及当前缺口见 [素材工作区约定](../../docs/协作/素材工作区约定.md)。
