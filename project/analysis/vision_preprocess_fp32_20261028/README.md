# PL FP32 归一化实现与验证

后续状态：同日已删除旧 RGB888 输出模块及 PS 归一化工具函数。下文四组 XSim、17 项 Python 为清理前的原始验证记录；当前三组 XSim、16 项 Python 的重验见 [清理记录](../vision_preprocess_fp32_cleanup_20261028/README.md)。

2026-10-28，Vivado 2024.1，`xc7z020clg400-1`。本次将原来留在 PS 的 `uint8 → float32 / 255` 实现在独立 PL 预处理模块中。没有操作板卡、修改老师模型或生成部署位流。

## 实现

原 `vision_rgb565_affine` 的 RGB565 展开、坐标量化、双线性插值和整数舍入保持不变，其 RGB888 输出接新增 `rgb888_axis_fp32_normalize`。256 项查找表使用精确整数除法与 nearest-even 舍入生成，逐位对齐 NumPy `float32(x)/float32(255)`，没有采用乘以已舍入倒数或浮点除法 IP。

32 位 AXIS 每拍一个通道，按 R、G、B 顺序输出；TKEEP 恒为 0xF，TUSER 仅帧首 R，TLAST 仅帧尾 B。末 B 被接收后才报告完成。版本升级为 `0x00020000`，每像素 12 字节；192×192 为 442368 字节，224×224 为 602112 字节。驱动拒绝旧版本和错误长度。

`fp32_to_model_tensor` 通过小端 FP32 的 `frombuffer` 视图得到 `(1,H,W,3)`，不再转换类型或除以 255。调用者须先确认 IP/DMA 完成、拒绝错误并 invalidate，且保留 DMA 缓冲的生命周期。见 [接口契约](../../board/vision_preprocess/CONTRACT.md)。

## 实际验证

| 类别 | 覆盖与结果 | 证据 |
|---|---|---|
| Python，17 项通过 | 实际 RTL 的全部 256 项逐 bit 对照独立 NumPy 除法；生成器重建一致；零拷贝 NHWC；版本和旧/短/长包拒绝；原几何、黑边、负坐标、32 位地址边界、全部 65536 个 RGB565 值；错误/超时保留缓冲 | [日志](python_final.txt)、[测试](../../board/vision_preprocess/test_preprocess.py) |
| 新归一化器 XSim | R/G/B 每通道覆盖全部 256 值，单像素、连续帧、气泡、随机及 100 周期背压、R/G/B 阶段 reset；11 完整帧、1134 个阻塞周期，TEST_PASS | [完整运行记录](xsim/tb_rgb888_axis_fp32_normalize/simulate.log)、[测试](../../fpga/tb/vision_preprocess/tb_rgb888_axis_fp32_normalize.sv) |
| 原 packer XSim | 49 帧、2821 个背压周期，尾拍/帧标记检查仍通过 | [运行记录](xsim/tb_rgb888_axis_pack32/simulate.log) |
| 原 sampler XSim | 16 组 fixture、19 帧、15 个非法配置；负坐标、边界邻居、地址范围、720p letterbox/旋转 ROI、读错误及恢复均通过 | [运行记录](xsim/tb_vision_rgb565_affine/simulate.log)、[向量](vectors.json) |
| V2 wrapper XSim | AXI-Lite AW/W 独立到达、WSTRB、响应背压、shadow/start，DDR 读等待/错误和异常 RLAST drain；FP32 顺序、末 B 阻塞时 busy=1/done=0/44 字节，消费后完成 48 字节；reset，TEST_PASS | [运行记录](xsim/tb_vision_preprocess_axi/simulate.log)、[测试](../../fpga/tb/vision_preprocess/tb_vision_preprocess_axi.sv) |
| RTL lint | 完成，保留 1 条 ASSIGN-9 WARNING，未使用 waiver | [官方解析器生成的 CSV](lint/linter_final.csv) |
| OOC 综合/布局布线 | 内部 10 ns setup/hold 通过，WNS +0.077 ns、WHS +0.113 ns；3468/3468 可路由网络完成，routing errors=0 | [结果](ooc/result.tcl)、[时序](ooc/timing_routed.rpt)、[路由](ooc/route_status.rpt) |

四组 XSim compile、elaborate、run 均完成；已读取每组完整 transcript，均有 TEST_PASS 且无 Fatal/Error，汇总见 [regression.txt](xsim/regression.txt)。测试均有 watchdog 和 `$finish`。Python 为 CPython 3.14.7、NumPy 2.5.3；当前环境无 OpenCV，本次未重跑 OpenCV 对照或 ARM 板端数值比较。

整个 V2 模块 routed 资源为 **1285 LUT、1947 FF、7 DSP、0 BRAM**，见 [资源报告](ooc/utilization_routed.rpt)。这是整个独立预处理模块的资源，不是归一化器单独占用或整板占用。

另在相同 routed 网表上，为 AXIS 输出施加同钟 0 ns output delay、为 ready 施加 0 ns input delay，检查原 OOC 没有覆盖的寄存器到输出路径；该理想下游假设下最差 slack **+1.731 ns**，见 [假设](ooc/fp32_output_ideal_boundary.txt)、[路径](ooc/fp32_output_ideal_boundary.rpt)。此检查不替代真实 DMA/系统边界时序。

## 保留告警

| 规则 | 严重度 | 数量 |
|---|---|---:|
| ASSIGN-9 | WARNING | 1 |

| 文件 | 数量 | 位置 |
|---|---:|---|
| vision_preprocess_axi.v | 1 | m_axis_tdata，首次报告 bit 30 |

报告经技能的 `parse_lint_report.py` 转为 CSV。[UG901](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/List-of-Linter-Rules) 将 ASSIGN-9 定义为 I/O 位未赋值；本次 RTL 查表结果处于 [0,1]，已显式拼接零高位，但告警仍存在。不宣称 lint 零告警，也未找到 AMD 确认本次现象为工具缺陷的依据。

全部 256 值的完整 32 位仿真输出正确。进一步查询最终 routed 网表，bit 30、31 均连接 `<const0>`，驱动均为 GND/G、REF_NAME=GND，见 [网表核对](ooc/fp32_high_bits.txt)。实际高位有明确驱动。顶层中间线的诊断尝试产生 ASSIGN-5/6 后已撤回，诊断 CSV 单独保留，不包含在最终源码中；没有增加 waiver。

DRC 保留 10 条 Warning：原 sampler 的 5 条 DPOP-1、4 条 DPOP-2 为 DSP 流水建议，1 条 ZPS7-1 来自独立 OOC 未实例化 PS7，见 [DRC](ooc/drc.rpt)。实际接口 input/output delay、HD.CLK_SRC、PARTPIN 位置仍缺失；内部时序余量较窄，不能据此声称整板 AXI/DDR 或相机 I/O 时序签核。

## 复现与边界

入口见 [操作说明](../../board/vision_preprocess/README.md)，源 SHA 见 [source_sha256.txt](source_sha256.txt)，独立归一化 oracle 副本见 [normalize_expected.mem](normalize_expected.mem)。本次工程为 `project/_tmp/vision_preprocess_fp32_20261028_224455`，向量在 `project/_tmp/vision_preprocess_fp32_vectors_20261028`。Vivado 内调用外部 Python 解析 lint 时使用 `python -E`，避免继承 Vivado Python 3.8 标准库环境。

仍待接入相机整板工程、确认 S2MM 最大长度和缓冲大小、冷部署，以及真实采集→预处理→原老师的输入张量/最终输出对照。输出从每像素 3 字节增至 12 字节，尚未测量端到端净收益。老师结构、权重、输出头及训练路线未改变。

本次使用一个 `gpt-6.1-sol/high` 工程子代理及其修正轮次，主代理完成集成、Vivado 运行和验收。没有完整逐项计费用量，主代理、子代理和工具的实际总 API 费用未知，不报告节省比例。
