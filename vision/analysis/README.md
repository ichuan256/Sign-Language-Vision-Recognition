# 分析与证据入口

当前样本状态见 [dataset/README.md](dataset/README.md)，PL 路线状态见
[r3/README.md](../../project/analysis/r3/README.md)。先读这两处，再查带日期的实验记录。

| 位置 | 用途 | 状态 |
|---|---|---|
| [dataset/](dataset/README.md) | 样本现状、补采计划、标签与来源审计 | 当前数据入口；审计不等于语义清洗完成 |
| [r3/](../../project/analysis/r3/README.md) | 量化训练、HLS 对齐、综合报告与原始 JSON | 当前 PL 入口；当前网络资源/时序未通过 |
| [m1_dtw_20261023/](m1_dtw_20261023/README.md) | 首轮关键点 DTW 的 26 类/90 条实验及特征、评测结果 | 历史证据；与 `vision/m1/` 的 8 类/28 条实验不同 |
| [stereo_review_20261024.md](stereo_review_20261024.md) | 双目 Python 代码评审 | 日期快照；不是当前缺陷清单或硬件验收 |

资料约定：

- `README.md` 是目录的阅读入口，列当前事实、限制与下一步。
- 带日期的 `.md/.json` 保留实验口径、配置和数值，不把不同实验合并成一个准确率。
- 候选网络、补采数量和预期收益要明确标为计划，未经实验不写成结果。
- 清单/媒体的重复与语义问题进入复核队列，不通过目录整理自动改标签或删素材。
- 缓存、生成的 HLS 工程与临时日志继续放 `project/_tmp/`；分析目录保留可复核证据。
- 调整路径时同步脚本默认输出、文档链接和导入；不保留旧路径下的重复副本。

复跑工具入口：[scripts/README.md](../scripts/README.md)。系统运行入口：[根 README](../../README.md)。
