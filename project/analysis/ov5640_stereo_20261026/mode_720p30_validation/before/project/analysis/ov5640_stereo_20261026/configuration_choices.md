# OV5640 起步参数及本次实现范围

日期：2026-10-26。针对现有 `ov5640_stereo` 采集壳和候选相机模式；已落实初始化时序默认值及可执行的 27 项已确定配置子表，包含双路独立读改写和逐项延时。物理管脚按用户要求稍后处理。

## 1. W6 系统时钟与已修改的默认值

已核对仓库实际工程，而非依赖端口名称推测：

- `project/fpga/scripts/w6_audio_bd.tcl:57` 注明 FCLK_CLK0 为 100 MHz；`:68` 用其驱动音频时钟模块。
- `project/fpga/scripts/w6_hdmi_bd.tcl:300` 连接 `ps7/FCLK_CLK0` 到 `video/clk_100M`。脚本后部还将原名为 `clk_142M` 的视频支路接回 FCLK_CLK0，因此不能仅按该端口名字取 142 MHz。
- `project/fpga/project/glove/glove.srcs/sources_1/bd/system/system.bd:517` 的 `PCW_CLK0_FREQ=100000000`，`:832` 的 `PCW_FPGA0_PERIPHERAL_FREQMHZ=100`；`:6225` 的网络列出实际连接。
- 相机控制器尚未实例化在 W6 BD 中。本次选用的接入方案是让 `sys_clk` 使用 FCLK_CLK0，`SYS_CLK_HZ=100000000`；本次没有改动 BD 或执行板端部署。

| 参数 | 本次默认 | 100 MHz 周期数 | 状态 |
|---|---:|---:|---|
| `SYS_CLK_HZ` | 100 MHz | — | 已加入高层壳和初始化控制器 |
| `PWDN_SETTLE_CYCLES` | 20 ms | 2000000 | 已改 RTL 默认值 |
| `RESET_RELEASE_WAIT_CYCLES` | 20 ms | 2000000 | 已改 RTL 默认值 |
| `SCCB_HALF_PERIOD_CYCLES` | SCL 100 kHz 的半周期 | 500 | 已按系统时钟派生 |
| `SCCB_TIMEOUT_CYCLES` | 10 ms | 1000000 | 已改 RTL 默认值；检测发送器未完成 |

所有周期数均向上取整且至少为 1；可继续显式覆盖原有周期参数。此处 `SYS_CLK_HZ` 是频率声明，不会改变实际时钟发生器。默认 10 ms 超时留有余量：100 kHz 下，现有一次 4 字节、每字节 9 个时钟的 SCCB 写有效位时长约为 360 μs，另有起止状态开销。它不能证明传感器存在或寄存器接受了写入。

数据手册 §2.7（PDF 29-30 页）及 Linux `ov5640_powerup_sequence()` 给出：电源稳定到 PWDN 下降至少 5 ms，PWDN 下降到 RESETB 上升至少 1 ms，RESETB 上升到 SCCB 至少 20 ms。20 ms / 20 ms 是本次保守起步选择；调用 `start_init` 前仍需保证电源已稳定至少 5 ms，且 XCLK 已运行至少 1 ms。

## 2. PLL 与采样边沿

现有 `ov5640_pll_config.v` 发出五项相机寄存器写入（0x3034-0x3037、0x3108），配置相机内部时钟树。它不包含 0x4740，不会实例化 FPGA 的 PLL/MMCM，也不会生成或调整 FPGA 的采样时钟。

若接入的是 FPGA Clocking Wizard，PLL/MMCM 可以对输入 PCLK 做缓冲、分频或相移；仍须配置相位、等待锁定、处理复位，并验证相机数据与采样边沿之间的建立/保持余量。接入 PLL 模块本身不能证明余量足够。

2026-10-26 用户已确认采样边沿：**FPGA 使用 PCLK 上升沿采样，相机配套在 PCLK 下降沿更新数据**。现有采集器的 `posedge cam_pclk` 与该决定一致，无需修改采样逻辑。DVP 指南 §4.2（PDF 27 页）将 `0x4740[5]=1` 定义为下降沿输出；现已在子表中落实 `value=0x20/mask=0x20`，分别读回两只相机的旧值后更新，保留其他尚待核验的极性位。板级输入时序和实物验收仍待完成。

极性资料存在实质差异，不能把 0x4740 的整字节值直接冻结：

| 项 | DVP 应用指南 / 数据手册 | Linux 上游驱动 |
|---|---|---|
| VSYNC bit 0 | 指南和数据手册将 1 解释为高有效 | 明确注明数据手册与硬件相反，实物 0 高有效、1 低有效 |
| HREF bit 1 | 指南写 0 时 HREF 高有效；数据手册写 1 为 active high | 驱动高有效标志置 bit 1 |
| PCLK bit 5 | 指南写 1 时数据在下降沿输出 | 驱动为上升沿采样置 bit 5，与该采样关系相容 |

FPGA 当前按 VSYNC 高有效脉冲、HREF 高有效采集。之后应以目标模组上的波形及行/帧计数核验该契约，不能用寄存器默认值代替测量。

## 3. 输入时序是否有通用数值

常用的是“错开数据更新与采样边沿”的方法；`set_input_delay -min/-max` 没有可脱离传感器输出时序、所选边沿及板上走线的通用纳秒数。它们描述外部数据到达 FPGA 的时间，不是命令硬件把数据推迟多少。

对相机直接转发的 PCLK，可按选定的数据发射边沿计算：

```text
input_delay_max = sensor_Tco_max + max(data_trace_delay - pclk_trace_delay)
input_delay_min = sensor_Tco_min + min(data_trace_delay - pclk_trace_delay)
```

相机下降沿更新时，约束也要引用对应发射边沿。使用 PLL/MMCM 相移后仍需保留真实外部输入延迟模型。候选 PCLK 168 MHz 的周期约 5.95 ns，半周期约 2.98 ns；这只是理想半周期，尚未扣除器件输出延迟、占空比偏差、抖动和板级偏差，不能当作可用建立时间或直接填入约束。

已实际检索 AMD 本地文档库：UG949 “Defining Input Delays” 说明 min/max 应由外部 Tco 和时钟、数据走线延迟计算。当前管脚/走线尚未确定，本次不生成假定数值的 XDC。

## 4. 曝光、增益、白平衡和防闪烁

第一轮采图建议使用自动曝光（AEC）、自动增益（AGC）、自动白平衡（AWB），并关闭夜景延长曝光帧周期。按国内室内供电环境先选 50 Hz 防闪烁。以下是**全局初始化及对应 ISP 模块已启用后**的位操作，不能替代完整初始化表：

| 功能 | 寄存器位操作 | 说明 |
|---|---|---|
| 自动曝光、自动增益 | 清 `0x3503[1:0]` | 保留其他位；已有初始化表可在该阶段临时关闭自动控制，完成模式切换后恢复 |
| 自动白平衡 | 清 `0x3406[0]` | 使用全局表配套的 AWB 参数 |
| 指定 50 Hz | 置 `0x3C01[7]`，置 `0x3C00[2]` | 此处“手动指定”指灯光频率，曝光和增益仍自动 |
| 开启 banding filter | 置 `0x3A00[5]` | 还需按实际内部系统时钟、HTS/VTS 计算 band step |
| 关闭夜景降帧 | 清 `0x3A00[2]` | 防止夜景功能通过插入额外行延长帧周期 |

曝光上限和 gain ceiling 应与最终模式表一起配置。保持固定帧周期时，可先把曝光限制在帧长允许范围内；Linux 曝光范围使用 `VTS-4` 行作为上限，候选 VTS=1120 时为 1116 行。毫秒值需要用实际曝光行时间换算，不能把 PCLK 的字节周期直接当成曝光行时间。对快速手势，如出现拖影，可在光照允许时进一步缩短曝光，但本次未把任意固定曝光或增益值写入 RTL。

Linux 上游 `ov5640_set_autoexposure()`、`ov5640_set_autogain()`、`ov5640_set_ctrl_white_balance()`、`ov5640_set_ctrl_light_freq()`、`ov5640_set_bandingfilter()` 和 `ov5640_set_night_mode()` 提供上述位操作和时序依赖依据。DVP 指南 PDF 41-42 页提供夜景与 50/60 Hz 设置说明。以上位操作现已加入已确定子表，仍不等于完整初始化表或已验证曝光效果。

按本组 PLL 参数，相机内部 SCLK 为 84 MHz。HTS=2500/VTS=1120 时，50 Hz step=336、60 Hz step=280，最大 band 数各为 3；子表先写 `3a08=01, 3a09=50, 3a0a=01, 3a0b=18, 3a0d=03, 3a0e=03`，再开启 banding 和自动曝光/增益。推导和原始函数依据见 [known_config_register_evidence.md](known_config_register_evidence.md)，数值合同见 [known_config_contract.json](known_config_contract.json)。改变时钟或 HTS/VTS 时须同步重算，不能混用 FPGA 的 100 MHz。

## 5. 初始化表内的逐项等待

PWDN/RESET 的 20 ms 默认值只作用于上电状态机。Linux 公共初始化表在 `0x3C00=0x04` 项后另有 300 ms 延时，不能统一替换成 20 ms。采用该序列时应保留其明确的逐项等待。

原有 `cfg_*` 仍只携带地址、值和末项标志，没有每项延时字段。新增 `ov5640_known_config_table` 表项显式携带 `write_mask` 与 `post_delay_ms`；序列器保持当前项直到两路发送完成，再执行该项延时。末项使用原控制器内部 `transport_done`，不等待永不再次拉高的 `cfg_ready`；额外 300 ms 完成后才输出新入口的 `known_config_done`。换算使用 64 位中间值，100 MHz 下为 30000000 周期。原顶层 `config_done` 的发送语义没有改变，新入口的完成也仅表示配置子集发送及等待结束。

## 6. 检查结果与边界

Vivado 2024.1 XSim 中，新增默认值自检和已有 8 个自检均有独立 PASS 标记，合计 9 个。分类结果及每个测试对应日志见 [verification.json](timing_defaults_validation/verification.json)。

新增自检实际测量输出翻转所经历的时钟周期，覆盖三种频率参数下的默认等待、超时和 SCL 高低半周期；其余用例覆盖控制顺序和超时错误、RGB565 与坏帧恢复、独立 PCLK、SCCB 开漏收发及配置流握手。参数边界包含向上取整、至少 1 周期、大频率不溢出和旧位置覆盖兼容。

为兼容旧位置参数，`SYS_CLK_HZ` 放在末尾，XSim 首次编译对声明前引用给出 VRFC 10-3380 警告；实测重算结果正确。参数边界检查中的静态实例有未接时钟的展开警告；它们只检查参数而不宣称验证该实例动态行为。回归还出现 Vivado 未自动找到 GCC 的环境警告，实际编译、展开与行为仿真均成功。初次回归采集脚本在关闭仿真之前读取未刷新的日志造成检查失败；现已改为先关闭仿真再保存日志，完整重跑成功。

本次没有生成位流、处理实际引脚或部署相机；完整模式表、实际曝光效果、外部输入时序、DDR 通路及板上帧率仍未验收。

## 7. 已确定子表的实际落地状态

新增 `project/fpga/rtl/ov5640_stereo/ov5640_known_config_table.v` 保存 27 项地址/值/掩码/延时；`ov5640_sccb_masked_write.v` 在每条 SCCB 总线上独立执行完整写或先读后写；`ov5640_known_config_sequencer.v` 负责背压和逐项等待；`ov5640_stereo_known_config.v` 是具有真实 SCCB 与 RESET/PWDN 端口的执行入口。原有外部配置入口与 PLL 五项生产者保留兼容。

子表包括 PLL、输出宽高、候选 HTS/VTS、RGB565、PCLK bit 5、band-step 及自动曝光/白平衡/50 Hz 位操作。部分掩码共有六项，左右相机分别保留自己的旧位，未冻结的 VSYNC/HREF 不被整字节覆盖。没有加入未确定的全局模拟/ISP、裁剪起止、曝光/gain ceiling 或 stream-on。

该入口会先执行物理复位，所以**不能先全局初始化再调用它**。未来完整启动须在同一次复位之后、子表之前插入匹配的基础初始化；当前只证明子集可执行，不证明相机已经初始化或输出 1080p30。

新四项与既有九项自检最终均通过，分批结果、相关源哈希和完整日志见 [known_config_validation/verification.json](known_config_validation/verification.json)。新增测试检查：全部表值和掩码、无效索引及背压；真实总线地址解码、全写/读改写和忙时锁存；双路不同旧值的未知位保留；逐项及最后一项延时、超时错误保持和中途复位恢复。动态延时测试缩放时钟声明，并独立检查 100 MHz×300 ms 的 64 位换算。

真实 SCCB 模型发现旧读原语在重复 START 后缺少首位低电平准备，已修复；STOP 准备阶段现保持 SCL 低，以免 SDA 下降与 SCL 上升同时产生额外 START。旧读测试模型原先提前一个时钟送数据，也已修正，并新增 START/STOP 计数。读、读改写、双路集成和超时测试在最终修复后重跑；DVP/默认时序等未依赖该改动的通过结果按依赖复用，具体批次在验证清单中列明。

综合核验后又将读写 FSM 分成同文件 `*_core` 和保持原端口的薄封装；适配器直接 OR 两 core 的拉低使能，每条 pad 仅一处三态驱动。结构调整后重跑读、单路/双路写、RMW、双路配置、超时、原顶层及默认时序共八项，均通过；其余未依赖改动的结果复用。

最终正常顶层综合确认两路各一个 SDA IOBUF、一个 SCL OBUFT，四个 I 端接 GND，无多驱动/黑盒。证据见 [synth_final_pad_buffers.txt](known_config_validation/synth_final_pad_buffers.txt) 和 [synth_final_drc.rpt](known_config_validation/synth_final_drc.rpt)。未指定管脚/IOSTANDARD、独立壳缺 PS7、SCL 缺输入缓冲及乘法器流水建议仍在报告中；不等于通过实际工程的约束、布局布线或发布检查。最初 OOC 三态警告与正常综合结果分开保存，不将其当成最终硬件结构结论。

## 原始资料

- [Linux 上游 OV5640 驱动](https://github.com/torvalds/linux/blob/master/drivers/media/i2c/ov5640.c)；本次联网核对，按函数名追踪，避免依赖漂移的行号。
- [OmniVision CSP3 数据手册 v2.01](../../../backup/【正点原子】OV5640双目摄像头模块/【正点原子】OV5640双目摄像头模块资料/2，OV5640参考资料/OV5640_CSP3_DS_2.01_Ruisipusheng.pdf)：§2.7、§6.6、§7.8。
- [OmniVision DVP 应用指南 R2.13C](../../../backup/【正点原子】OV5640双目摄像头模块/【正点原子】OV5640双目摄像头模块资料/2，OV5640参考资料/OV5640_自动对焦照相模组应用指南(DVP_接口)__R2.13C.pdf)：PDF 27、41-42 页。相关表格已渲染核对；提取证据在 `configuration_evidence/`。
- [AMD UG949：Defining Input Delays](https://docs.amd.com/r/2023.1-English/ug949-vivado-design-methodology/Defining-Input-Delays)，本地索引适用版本包含 2024.1；2024.1 页面未能联网打开，联网原文回退到同主题 2023.1 页面。
