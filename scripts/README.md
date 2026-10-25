# 脚本入口

所有示例均在仓库根目录执行。

| 位置 | 用途 |
|---|---|
| [dataset/](dataset/README.md) | 样本清单、来源和标签审计 |
| [r3/](r3/README.md) | PC 量化历史基线、HLS CSim、HLS 综合 |
| 根目录 `build_*`、`evaluate_templates.py`、`infer_sign.py` 等 | 既有视觉模板、评测与推理工具，运行路径保留 |
| 根目录 `calibrate_stereo.py`、`measure_stereo_range.py` | 既有双目标定与测距工具，运行路径保留 |

模型/数据版本与实验结论看 [analysis/README.md](../analysis/README.md)。
新增数据审计工具放 `dataset/`，新增 R3 实验工具放 `r3/`，避免继续平铺日期脚本。

`build_templates.py`必须显式提供`--manifest`和`--output`，默认不覆盖已有模型。
旧裁剪媒体已清理，只保留一个测试样例；旧225行清单不能直接用于全量重建。
该工具的`--help`和参数/输出保护不要求提前加载视觉依赖。
