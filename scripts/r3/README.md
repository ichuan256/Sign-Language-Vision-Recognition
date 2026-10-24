# R3 历史实验复跑

从仓库根目录执行；使用已有 `F:\PLD\.venv-r3` 环境。缓存与模型路径仍为 `_tmp/r3/`。

| 脚本 | 行为 | 结果位置 |
|---|---|---|
| `r3_baseline_20261024.py` | 复现旧标签分层划分并训练；默认覆盖同名模型缓存 | `_tmp/r3/` |
| `r3_hls4ml_20261024.py` | 转换与 CSim，不执行综合 | `analysis/r3/r3_hls4ml_20261024.json` |
| `r3_hls_synth_20261025.py` | 逐位门禁通过后执行 HLS C 综合；无 IP 导出/实现 | `analysis/r3/r3_hls_synth_20261025.json` |

```powershell
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 scripts/r3/r3_baseline_20261024.py --help
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 scripts/r3/r3_hls4ml_20261024.py --help
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 scripts/r3/r3_hls_synth_20261025.py --help
```

阶段状态与限制见 [analysis/r3/README.md](../../analysis/r3/README.md)。这些脚本用于
复现原实验，整理目录没有改变网络、训练划分、数值语义或 HLS 综合选项。
