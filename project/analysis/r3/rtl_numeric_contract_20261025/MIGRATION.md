# 目录迁移说明（2026-10-25）

本目录原有5个文件的Git内容与本地恢复快照b272988逐字节相同；旧路径和来源哈希是当时证据，不改写为迁后已验证。

迁后新来源契约见[新目录](../rtl_numeric_contract_20261025_layout/README.md)，由[导出器](../../../scripts/r3/export_rtl_numeric_contract.py)重新读取当前源码并计算哈希。迁后数值测试验证截断、舍入、回绕/饱和、256输入映射及拒绝覆盖；不是完整网络golden或RTL验证。

新旧契约均为partial_source_contract，model_golden_ready与rtl_numeric_contract_ready仍为false；没有训练、HLS/RTL运行或上板。
