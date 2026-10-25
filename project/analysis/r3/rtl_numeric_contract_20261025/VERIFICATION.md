# 本次验证记录

2026-10-25，Python 3.14.7标准库，无TensorFlow/NumPy依赖。
执行：python -m unittest discover -s tests -p test_rtl_numeric_contract.py -v
结果：7个测试通过，退出码0，最终运行0.055秒。

- 赋值边界：负数AP_TRN向下取整、正负溢出回绕/饱和、收敛舍入的正负半LSB及邻近值。
- 格式处理：有符号/无符号码往返；拒绝不支持的模式、非零N参数和非法位宽。
- 输入映射：256个uint8端点和单调性；对254个内部值以相邻binary32码与精确有理数的距离独立核验最近值，检查F=38转换无额外损失。
- 导出完整性：18个源操作入口、来源哈希、256行映射、35个合成边界向量；无网络golden时就绪标志为false，拒绝覆盖已有证据。

导出：python scripts/r3/export_rtl_numeric_contract.py --output analysis/r3/rtl_numeric_contract_20261025
退出码0；partial_source_contract；rtl_numeric_contract_ready=false。
输入软件模型：精确p/255替代binary32归一化时254/256项不同，最大8160输入LSB，约2.97e-8实数值。这不是输出logit差异或识别误差。

阻断全部完成的缺口：原权重、BN参数、生成运算类型、逐层golden及Vitis交叉验证。原模型/tensors/HLS工程未找到，用户表示应该没有。未重训或编造权重。
本次未执行RTL仿真、综合、实现或板端操作；来源哈希见contract.json。
