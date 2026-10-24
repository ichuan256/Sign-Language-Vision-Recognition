# 数据目录

| 位置 | 内容与约定 |
|---|---|
| [manifests/](manifests/README.md) | 当前清单、来源记录和剪辑验收；元数据可入库 |
| [legacy/](legacy/README.md) | 原 `material/` 裁剪域旧样本与旧版清单，供历史实验复现 |
| `exports/` | 导出工具的新产物默认目录；尚未生成的目录无需预建 |

正式全画幅媒体仍位于仓库根的 `video/`，不入库；部署/识别模型仍在 `models/`。
这两处是既有运行契约，本轮不搬动。当前样本状态与补采见
[analysis/dataset/README.md](../analysis/dataset/README.md)。

所有清单中的相对媒体路径按仓库根解释，调用数据加载器时传 `repo_root`。
移动清单不改变标签、来源时间和样本划分；旧快照中的绝对路径保留历史含义。
