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
