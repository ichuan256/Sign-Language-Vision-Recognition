# 脚本入口

所有示例均在仓库根目录执行。

| 位置 | 用途 |
|---|---|
| [dataset/](dataset/README.md) | 样本清单、来源和标签审计 |
| [r3/](../../project/scripts/r3/README.md) | PC 量化历史基线、HLS CSim、HLS 综合 |
| 本目录 `build_*`、`evaluate_templates.py`、`infer_sign.py` 等 | 视觉模板、评测与推理工具 |
| 本目录 `calibrate_stereo.py`、`measure_stereo_range.py` | 双目标定与测距工具 |

模型/数据版本与实验结论看 [analysis/README.md](../analysis/README.md)。
新增数据审计工具放本目录 `dataset/`；R3 实验工具放 `project/scripts/r3/`。

素材盘点工具在 `dataset/inventory_video_materials.py`。历史整理/回收脚本冻结，仅供溯源，不得再次Apply；新清单绑定显式来源与审计SHA，输出必须是新文件。数值契约工具见 `project/scripts/r3/`。
