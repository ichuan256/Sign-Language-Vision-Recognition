# 视觉模块

- [样本现状与补采](analysis/dataset/README.md)、[来源审计](analysis/dataset/label_source_audit_20261025.md)
- [数据与清单](data/README.md)、[分析索引](analysis/README.md)、[辅助工具](tools/README.md)
- [M1 关键点识别](m1/README.md)、[网页演示](webapp/README.md)、[复跑脚本](scripts/README.md)

`src/signrec/` 是视觉嵌入识别库；`models/` 放模型与模板；`tests/` 放测试。
`video/` 是本地素材库，不入 Git。量化/HLS 已归入 [project](../project/README.md)，不在此重复维护。

在仓库根目录启动网页：

```powershell
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 vision/webapp/run_fullframe_20261024.py
```

浏览器访问 `http://127.0.0.1:8001`。
