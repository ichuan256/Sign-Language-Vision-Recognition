# 四模块合并与素材核验（2026-10-25）

当前551条由迁后历史636清单与对应审计显式生成，85条缺失的历史预期版本被排除；本机另外保存的85条不同SHA版本继续独立待审，未补入可用子集。

- [当前清单验证报告](../../../data/manifests/manifest_available_sha_verified_20261025_layout.csv.validation.json)：636输入、551纳入、85缺失；重生成CSV与迁后551清单逐字节相同。
- [保护媒体与路径映射](protected_media_layout.csv)：816条旧路径→新路径、大小和SHA；全部已在隔离工作区核验，最终main还要再核验。
- [模型数组比较](model_array_comparison.json)：两份既有模板的features、offsets、labels逐项相同。
- [M1迁移前状态](m1_before.json)：28条来源路径均可读，最终main必须继续全部可读。
- [合并执行记录](../../../../docs/协作/Git合并执行记录_20261025.md)：基线、恢复点、检查与最终状态。

旧盘点/回收记录的路径是历史快照；本目录提供本次迁移映射，未改标签、时间边界、人物ID或训练测试划分。

本目录测试日志副本仅去除行尾空白以通过Git差异检查，原始输出保留在project/_tmp。最终全套日志：[147项回归](merge_full312_pytest.log)；先前环境失败日志保留供核对。
