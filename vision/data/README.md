# 数据目录

| 位置 | 内容与约定 |
|---|---|
| [manifests/](manifests/README.md) | 当前清单、来源记录和剪辑验收；元数据可入库 |
| `models/` | 从旧 `vision/models/` 移入的 ONNX、模板与许可；二进制哈希不变 |
| `cache/m1/` | 从旧 `vision/m1/runs/` 移入的历史关键点提取结果；不是当前教师或人工真值 |
| [legacy/](legacy/README.md) | 原 `material/` 裁剪域旧样本与旧版清单，供历史实验复现 |
| `exports/` | 导出工具的新产物默认目录；尚未生成的目录无需预建 |

正式全画幅媒体仍位于仓库根的 `vision/video/`，不入库；部署/识别模型仍在 `vision/data/models/`。
正式 `vision/video/done` 相对路径保留，原片在`vision/video/raw`；新增素材接收区为`vision/video/inbox`。
第二三课现存85条已核对为原审计SHA版本，位于done/wsy/第2 第3课，仍单列待审，不自动加入551条池。
历史保护媒体中31个原片及5个旧演示片段缺失；历史归档已不在工作区。
当前样本状态与补采见
[analysis/dataset/README.md](../analysis/dataset/README.md)。

本机当前可用子集为 `manifests/manifest_available_sha_verified_20261025_layout.csv`（551条）；
旧636条清单与模板保持原样。素材位置与使用边界见
[素材工作区约定](../../docs/协作/素材工作区约定.md)。

所有清单中的相对媒体路径按仓库根解释，调用数据加载器时传 `repo_root`。
历史 M1/提取器清单例外：其 `file` 相对清单所在目录；物理移动已同步换算相对路径，媒体目标保持不变。
移动清单不改变标签、来源时间和样本划分；旧快照中的绝对路径保留历史含义。

迁后活动清单以 current_available_fullframe.json / source_registry_current.json 为准；旧r2、clean及旧validation文件原样保留作历史证据。新布局核验见 `vision/analysis/materials/20261025_merge/`。

当前学生从551条池抽取40条1080p视频，614个手部ROI按训练320/验证106/开发留出188分组。
用户17项复核已导入，人工坐标在三组分别6/3/2项；已完成画外点掩码后的浮点复训。
教师指MediaPipe Holistic软件模型，未知区域不自动当负例。定位尚未过门禁，
见[当前结果](../../project/analysis/keypoints_student_20261027/README.md)；旧670/136/191划分保留于历史试跑。
