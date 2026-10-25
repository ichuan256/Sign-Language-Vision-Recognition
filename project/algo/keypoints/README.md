# 单手关键点加速：计算核原型

当前 `kp_gemm_tile` 是 **16 路整数 MAC 分块核**，不是完整关键点网络，也没有输出完整 21 点的板端驱动。
目标部件为 xc7z020clg400-1；100MHz 为综合目标，不是板端实测时钟/吞吐验收。

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

旧冻结 `fpga/rtl/` 未修改。后续仍需要 depthwise/向量运算、图调度和 AXI 整板集成，
不能把这个核的 C/RTL PASS 或资源估计称为“关键点已经在 PL 自主识别”。
