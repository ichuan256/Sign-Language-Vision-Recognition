# 单手关键点加速：计算核原型

当前方案见 [PS 教师网络的 PL 局部加速](../../../docs/方案/04_老师模型PS_PL局部迁移.md)。
本目录的 `kp_layer`、`kp_gemm_tile` 和 `kp_vector` 是历史 W12/A16 整数整网核，
不能直接接入原版 full 老师的 FP32 张量。学生 W8/A8 路线已停止，新浮点子图核尚未实现。
历史 lite 整网 PL 数值与时延见 [日期证据](../../analysis/keypoints_pl_20261026/stream_wide.md)，不代表当前板上状态。

## 历史分块核契约

以下只描述 `kp_gemm_tile` 接口；不是当前新核设计或后续交付计划。

接口：A 为 rows×depth，B 为 depth×16（输出通道不足 16 时补齐），
rows≤64、columns≤16、depth≤1024。DDR 中 A/B/out 为有符号 16bit，bias 为 64bit 容器
（有效值必须在 48bit 有符号范围），shift 为 8bit；内部累加 48bit，输出做最近偶数舍入与 16bit 饱和。
shift=F_input+F_weight−F_output，允许 [-31,47]。非法尺寸/shift/bias 通过返回状态拒绝。
调用者还必须保证整个点积加 bias 不溢出 48bit；核不逐乘加检查溢出。
导出的模型参考按完整 16bit 输入码范围检查保守累加界，不能只凭 bias 合法就断言所有模型安全。

`kp_gemm_tile_test.cpp` 使用独立 Python 整数黄金向量，测试正负半值、饱和、长点积、
不满 16 列、真实首层卷积的 16 位置×16 通道片段，以及非法尺寸。
复跑见 [脚本说明](../../scripts/keypoints/README.md)，最新结果见
[单手阶段记录](../../analysis/keypoints_pl_20261025/single_hand_stage1.md)。

冻结 `fpga/rtl/` 不用于新开发。新核必须有独立名称、数值契约、C/RTL 向量及寄存器映射。
