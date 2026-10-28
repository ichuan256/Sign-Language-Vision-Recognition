# 板端 PS full 老师与 PL 接入入口

当前方案：[PS 教师网络的 PL 局部加速](../../../docs/方案/04_老师模型PS_PL局部迁移.md)。
保留原模型，当前候选为 landmark 相邻两个残差块组成的一个连续分区；delegate 和新浮点核尚未实现。

| 文件 | 作用 |
|---|---|
| run_teacher.py | 原版 full palm → ROI → full landmark → 跟踪/绘制；有界帧数、loop 和 benchmark-only |
| run_raw_teacher.py | 板内 raw 老师入口；输入及显示协议按实际固件核对 |
| teacher_runtime.py | ctypes 调用 ARMv7 TFLite C ABI；当前只支持整图 invoke，没有 PL delegate |
| tflite_runner.cpp | 原解释器封装；新 delegate 在此接入，不从 Python 逐层调用 |
| teacher_geometry.py | palm 解码/NMS、ROI、归一化、四输出与跟踪，保留基线行为 |
| build_native.sh | TensorFlow 2.12.1、ARMv7/NEON 构建；XNNPACK 实际使用情况需查执行计划 |
| run_student_hdmi.py | 停用的学生 PS TFLite 演示，不是 PL 推理入口 |
| teacher_p0_board.py | 有界原库基线、原输入/输出保存与隔离诊断；不加载 FPGA |
| teacher_probe.cpp | 同版本原 wrapper 的诊断扩展，准备前挂接 profiler 并记录实际执行计划；不替换原库 |
| teacher_p1_postprocess.py / test_teacher_postprocess.py | 后处理边界测试、真实缓存对照及完整视频配对；原四输出/跟踪全部核验 |
| teacher_p1_boundary.py | 原模型附加可读边界，100 ROI 的四输出和独立 CPU 子图重放对齐 |
| teacher_p1_transfer.py | 按实际 XRT PSDDR 目标测 CMA 复制/缓存维护，释放缓冲；不创建 overlay 或启动 PL |

full landmark 输入 [1,224,224,3] FP32，按顺序输出 [1,63]、[1,1]、[1,1]、[1,63]，
依次为图像坐标、presence、handedness、world 坐标。不得改成旧 64/65 项协议。
SHA、palm 输出和逐节点清单见 [模型证据](../../analysis/teacher_partition_20261028/README.md)。

历史 2 线程零输入 benchmark 中 palm 约 550ms、landmark 约 490ms，各重复 5 次，只作初查。
真实视频 PS 性能须按当前模型/库/固件和显示设置重测；run_teacher.py 的 landmark_ms 包含 ROI 等工作，不是纯算子耗时。
frames.json 的时间戳语义须在 P0 明确，不能直接当作采集起始帧龄。
编译开启 CPU 优化不等于实际生效；核对 delegate 顺序与实际执行计划，正式基线不关闭原有优化。

这条手部管线不是完整身体 Holistic。已有 HDMI writer 依赖特定 VDMA/帧缓冲并含 R/B 补偿，
接管其他固件前核对颜色与寄存器，不能盲用历史地址或补偿配置。

首轮 [P0 实测](../../analysis/teacher_partition_20261028/p0.md) 已完成：120 帧、不写屏，landmark 原库调用 P50 约 501ms；
保存 100 个重放输入，各 12 个掌检/landmark 优化诊断输入均与原库全部输出逐值相同。
[P1 实测](../../analysis/teacher_partition_20261028/p1.md) 中后处理同场约 709.63→0.96ms；两轮 120 帧的平均处理约 1.57→1.01 秒，输出和跟踪逐帧一致。
本地 teacher_geometry.py 已应用保守预筛；板端只在隔离目录验证，原部署源码/模型/库、服务和固件未覆盖。
100 ROI 的单块/双块重放逐值一致，CMA 复制/缓存约 1.386ms；下一步测一个双块分区接图后的 CPU 剩余开销。
这些是 PS 优化和诊断，不是 PL 加速验收；相关工具见 [脚本说明](../../scripts/keypoints/README.md)。

本轮先只读核对板端 SHA/进程，再做真实输入剖析、分区冻结、CPU 测试接图、FP32 核与完整链路验收。
不提供未实现的 PL 启动命令；不启动学生训练，不自动改服务或加载固件。
