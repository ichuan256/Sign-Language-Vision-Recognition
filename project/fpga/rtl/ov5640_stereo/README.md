# ATK-OV5640 双路 DVP 接收 RTL

## 当前实现范围

当前目录实现两路独立的 OV5640 DVP 采集、SCCB 读写与按位读改写、RESET/PWDN 上电时序、27 项已确定配置子表，以及新增的完整冷启动候选入口。新入口包含基础模拟/ISP、720p模式与窗口、自动成像初值、双路 ID/关键寄存器校验和检查通过后的 stream-on；已完成30根物理引脚约束；未完成真实相机验证、外部输入时序、异步 FIFO、DDR/VDMA 或 HDMI 接入。

新增完整入口为 `ov5640_stereo_startup`，与 DVP 组合的壳为 `ov5640_stereo_startup_capture`；308项ROM 为 `ov5640_startup_table`，每路事务适配器为 `ov5640_sccb_register_access`。来源、参数、冷启动与完成语义见 [完整冷启动记录](../../../analysis/ov5640_stereo_20261026/startup_sequence.md)。下述旧顶层及 27 项子表保持原接口，不自动变成完整启动入口。

- `ov5640_dvp_capture.v`：单路 PCLK 域采集器。
- `ov5640_stereo_capture_pair.v`：实例化 OV1、OV2 两路采集器；两路仍处于各自相机 PCLK 域。
- `ov5640_sccb_write.v`：一个 SCCB 写事务引擎。
- `ov5640_sccb_read.v`：一个 SCCB 寄存器读事务引擎，支持先写寄存器地址、重复起始、读 8 位数据；SCCB 的 don't-care 位不作为 I2C ACK 检查。
- `ov5640_pll_config.v`：按当前目标输出五项 PLL/根分频寄存器流；它是配置表的一段，不是 FPGA fabric PLL 或完整相机模式表。
- `ov5640_stereo_sccb_pair.v`：两组独立 SCCB 写引擎，可分别启动或同时写同一条寄存器命令。
- `ov5640_stereo_top.v`：将双路 DVP 和 SCCB 写引擎连成一个可仿真的基础顶层；SCCB 命令由外部上层控制器提供。
- `ov5640_stereo_camera_init.v`：双路共同 PWDN/RESET 上电时序、外部寄存器流握手、双路 SCCB 完成等待和事务超时。
- `ov5640_stereo_camera_top.v`：带双路 DVP、双路 SCCB 和相机控制脚的高层壳；帧尺寸默认1280×720，但不会内置或宣称已完成720p30配置。
- `ov5640_known_config_table.v`：27 项索引式 ROM，包含地址、值、写掩码、逐项毫秒延时和末项标志。
- `ov5640_sccb_masked_write.v`：每路独立的 SCCB 读改写适配器；全掩码直接写，部分掩码先读再写。
- `ov5640_known_config_sequencer.v`：将表连接到原有 `cfg_*` 握手，保持当前项直到发送和延时全部完成。
- `ov5640_stereo_known_config.v`：组合原上电控制器、表序列器和两路读改写器的可实例化入口；仅执行已确定子表，不包含 DVP/全局模拟 ISP 初始化或 stream-on。
- `../../tb/ov5640_stereo/`：自检 testbench。

低层 `ov5640_stereo_top` 的 `sys_clk` 只驱动 SCCB 写引擎，保留外部单次命令接口以供总线测试；高层 `ov5640_stereo_camera_top` 增加初始化控制器和相机 RESET/PWDN 输出。两路像素输出仍分别同步于 `ov1_pclk`/`ov2_pclk`。高层的默认1280×720 是采集尺寸契约，只有外部配置流内容经过核验且成功发送后控制器才报告完成；它不代表寄存器已读回或相机输出已经验证。低层1280×720、VSYNC 高有效和 SCCB 半周期 500 个 `sys_clk` 周期仍是可覆盖的接口参数，需与实际传感器配置及输入时钟匹配。

## 单路接口契约

- `FRAME_WIDTH`/`FRAME_HEIGHT` 是正数，代表输出图像的 RGB565 像素宽高，必须与 OV5640 SCCB 初始化后实际输出尺寸一致。默认值1280×720与当前候选目标一致，仍可覆盖，尚未由寄存器配置或实物测量验证。
- `VSYNC_ACTIVE_LEVEL` 可设置帧同步脉冲有效电平。当前逻辑把 VSYNC 有效脉冲的结束边沿视为新图像区间开始，把下一次有效边沿视为帧结束。
- `pixel_data` 在 `pixel_valid` 周期有效。模组手册规定 RGB565 每像素低字节先输出，因此输出为 `{第二字节, 第一字节}`。
- `pixel_sof` 与首像素同周期；`pixel_eol` 与每行预期最后一个像素同周期。
- `frame_start`、`frame_done` 和 `frame_error` 都是单个相机 PCLK 周期的脉冲。帧号 `frame_id` 在帧完成时递增，包括被拒绝的帧。
- 坏帧错误涵盖行像素数不足/超出、奇数字节、行数不足/超出以及帧边界时仍有活动行。超出设定宽高的像素不会继续输出，避免写出预期帧缓冲范围。已经发出的部分像素不会回滚；下游必须等 `frame_done`，并在同周期检查 `frame_error`，再提交或丢弃整帧缓冲。
- 输出没有 ready/backpressure。采集器不能停顿相机，之后必须按每只相机各接一个异步 FIFO；不能跨时钟直接采样多位像素总线，也不能直接将此接口连到会反压的 AXI-Stream 接口。

复位 `rst_n` 在每个相机 PCLK 域内异步拉低、同步释放。若相机 PCLK 停止，局部复位会保持有效。

## SCCB 写事务接口

`ov5640_sccb_write` 在系统时钟域串行发出一次 3 相写：`{7-bit device address, write=0}`、16 位寄存器地址、8 位寄存器值。默认器件地址 `0x3c`，总线首先看到写地址字节 `0x78`。每个字节后第九时钟由主机释放 SDA；按模组手册 SCCB 写周期定义，这一位为 don't-care，不按 I2C ACK 处理。SCL/SDA 都只会拉低或高阻释放，不主动驱动高电平；模组板上的上拉电阻负责拉高。

`HALF_PERIOD_CYCLES` 配合 `clk` 决定 SCL 频率；例如系统时钟 100 MHz、半周期 500 时约为 100 kHz。事务期间 `busy` 保持有效，结束时 `done` 脉冲一周期。忙时到达的 `start` 不排队。双路封装提供独立的开始、忙和完成信号。

写原语不读取 SCCB 响应、不检查器件是否存在，也不处理总线卡低或时钟延展；它只证明本机按参数发出了写事务。读原语提供寄存器读回，但当前没有 ACK/器件存在性检测，也不处理总线卡低或时钟延展。要可靠判断芯片 ID，仍需在上层检查读出的 `0x300a/0x300b` 值并对读事务超时做错误处理。

### 相机上电和寄存器流接口

`ov5640_stereo_camera_top` 保留低层 `ov5640_stereo_top` 的现有接口兼容性，并额外提供 `start_init`、`cfg_*`、四根 RESET/PWDN 控制输出、`config_done` 和 `config_error`。复位期间两路 PWDN 均为高、RESET 均为低；启动后先拉低 PWDN 并等待 `PWDN_SETTLE_CYCLES`，再释放 RESET 并等待 `RESET_RELEASE_WAIT_CYCLES`，之后才置 `cfg_ready`。

2026-10-26 起，高层壳与初始化控制器新增 `SYS_CLK_HZ`，默认 **100 MHz**；默认周期数由频率向上取整换算，仍允许显式覆盖已有 `*_CYCLES` 参数。默认 PWDN 释放至 RESET 释放等待 **20 ms**、RESET 释放至允许 SCCB 等待 **20 ms**，100 MHz 下各为 **2000000 周期**。高层 SCCB 半周期默认 **500 周期**，目标 SCL 为 **100 kHz**；单项双路发送等待超时 **10 ms / 1000000 周期**。除法与余数计算避免频率乘毫秒时的整数溢出，并至少保留 1 周期。新增频率参数放在原参数列表末尾以保留原位置覆盖顺序。

W6 的时钟来源已核对：`../../scripts/w6_audio_bd.tcl` 第 57 行将 FCLK_CLK0 标为 100 MHz，`../../scripts/w6_hdmi_bd.tcl` 第 300 行将 `ps7/FCLK_CLK0` 接到 `video/clk_100M`；`../../project/glove/glove.srcs/sources_1/bd/system/system.bd` 的 `PCW_CLK0_FREQ=100000000`、`PCW_FPGA0_PERIPHERAL_FREQMHZ=100`。当前相机模块尚未接入该 BD，接入时需将 `sys_clk` 接到这路时钟，并保持 `SYS_CLK_HZ` 一致。

依据 OV5640 CSP3 v2.01 §2.7（PDF 第 29-30 页）和 [Linux 原始驱动的 `ov5640_powerup_sequence()`](https://github.com/torvalds/linux/blob/master/drivers/media/i2c/ov5640.c)，PWDN 释放至 RESET 释放至少 1 ms，RESET 释放至 SCCB 至少 20 ms，故采用 20 ms / 20 ms 的起步默认值。**调用 `start_init` 前，调用方还须保证传感器供电已稳定至少 5 ms，且 XCLK 已运行至少 1 ms。** 本控制器没有电源检测输入；两段默认等待不能替代电源稳定条件。

上层应在 `cfg_valid && cfg_ready` 时提供一个寄存器项，最后一项将 `cfg_last` 置高。控制器锁存地址和值，同时启动两条独立 SCCB；只有两路 `done` 都出现后才接受下一项。末项双路 `done` 后 `config_done` 保持为高；等待任一路 `done` 超过 `SCCB_TIMEOUT_CYCLES` 后 `config_error` 保持为高。两路 SCCB 写原语不读取响应，因此这里的 `done` 仅表示本机完成了发送状态机，超时只能发现发送状态机未完成，不能发现传感器缺席、未 ACK、寄存器未生效或错误图像。

**当前目标是双路独立 8-bit DVP、24 MHz XCLK、1280×720@30fps（标称）、RGB565；FPGA 接收端 VSYNC 契约为高有效。** 完整冷启动候选表现已实现，实际相机模式尚未验收。用户已确认 **FPGA 使用 PCLK 上升沿采样**，与现有 `posedge cam_pclk` 一致。新入口使用可覆盖的 `DVP_POLARITY_VALUE=8'h22`，按 Linux 解释设置 VSYNC/HREF 高有效与相应 PCLK 位，并关闭 PCLK 门控。指南、数据手册和上游驱动对部分极性位存在差异，因此该值仍是待波形确认的候选；旧 27 项子表只更新 bit 5 的合同保持不变。来源与边界见 [完整冷启动记录](../../../analysis/ov5640_stereo_20261026/startup_sequence.md)。

720p30使用固定Linux v6.12的28项模式事实、DVP窗口(0,250,2624,1456)、偏移(16,4)、HTS1892/VTS740；3814/3815=31并开启双向binning。RGB565 LE为4300=6f、501f=01，关闭JPEG与MIPI。

PLL：3034=18、3035=20、3036=54、3037=13、3108=01。24MHz XCLK→VCO672MHz→SCLK42MHz/PCLK84MHz，计算29.998286fps。生成器检查最终寄存器推导时钟≤96MHz、VCO范围、窗口、曝光及防闪烁。

旧1080p候选168MHz已停用。来源、308项ROM与硬件边界见 [startup_sequence.md](../../../analysis/ov5640_stereo_20261026/startup_sequence.md)。本次XSim与配置审计证据见 [mode_720p30_validation/](../../../analysis/ov5640_stereo_20261026/mode_720p30_validation/)，未重新综合、布局布线或部署。旧日志按原版本保留。

### 已确定配置子表的执行入口

`ov5640_stereo_known_config` 使用 `sys_clk`、`rst_n`、单周期 `start`，输出两路 RESET/PWDN、两组开漏 SCCB，以及 `busy`、`known_config_done`、`known_config_error`。时钟、等待、SCCB 半周期和超时参数与上面的默认值一致；本次保留原外部 `cfg_*` 顶层，新增入口单独实例化，不改变旧端口。

表内固定 PLL五项、1280×720输出尺寸、HTS1892/VTS740、RGB565 低字节先出、PCLK 下降沿更新、50/60 Hz band-step、自动曝光/增益/白平衡、指定 50 Hz 及开启 banding/关闭夜景。内部SCLK42MHz，band-step221/184，max 50/60Hz bands=3/4。滤波参数先于自动曝光/增益开启写入。逐项合同和来源见 [`known_config_contract.json`](../../../analysis/ov5640_stereo_20261026/known_config_contract.json) 和 [`known_config_register_evidence.md`](../../../analysis/ov5640_stereo_20261026/known_config_register_evidence.md)；改变 XCLK/PLL/HTS/VTS 后必须同步重算。

全掩码 `ff` 直接写入；六处部分掩码由每路适配器各自读旧值，再计算 `(old & ~mask) | (value & mask)`。尤其 `0x4740` 只更新 bit 5，保留该相机原有 VSYNC/HREF 位。读写引擎互斥启动，事务输入在 `start` 时锁存，忙时新请求不排队。现有无 ACK、无总线卡低检测的限制仍然适用；上层 10 ms 超时覆盖一次完整读改写，不含表内延时。

原读/写模块的外部接口和默认参数保持不变，内部 FSM 另提供同文件中的 `*_core`，输出拉低使能而不直接驱动 pad。适配器将两 core 的 SCL/SDA 拉低使能分别 OR 汇合，每个 pad 只生成一次 `0/Z` 驱动。正常顶层综合已确认每路 SDA 一个 IOBUF、SCL 一个 OBUFT，四个 I 端均接 GND；不依赖综合器把两组三态驱动合并为数据 LUT。

序列器在 `cfg_valid && cfg_ready` 后保持当前行，先等 ready 下降，再等非末项 ready 回升或末项原控制器的 `transport_done`。随后完成该行 `post_delay_ms` 才前进；最后 `0x3c00` 的 300 ms 也包含在 `known_config_done` 之前。毫秒换算采用 64 位中间值、向上取整；100 MHz 下 300 ms 为 30000000 周期。完成与错误保持到 `rst_n` 复位，不支持无复位重启。

**此入口会执行物理 RESET/PWDN，只在复位后发送该配置子集。** 完整启动将来必须在同一次硬复位之后、应用子表之前插入匹配的全局模拟/ISP 初始化；不能先运行全局初始化，再调用这个会复位的入口。当前没有裁剪起止、完整 ISP、曝光/gain ceiling 或 stream-on，`known_config_done` 仅表示子表两路发送及等待结束，不表示相机或720p30图像就绪。

## 当前720p验证

配置审计与19项Vivado2024.1 XSim回归均通过；包括完整1280×720帧、RGB565字节序、短行/坏帧恢复、独立PCLK、双路SCCB及启动故障门禁。主要新增测试为../../tb/ov5640_stereo/tb_ov5640_720p_frame.v。详细证据和硬件限制见 [本次验收记录](../../../analysis/ov5640_stereo_20261026/mode_720p30_validation/README.md)。

## 历史验证（切换前，适用版本见各日志）

本次子表实现完成 Vivado 2024.1 XSim 行为仿真：新增四项自检与既有九项均有 PASS 记录，最终相关源哈希及分批执行说明见 [`known_config_validation/verification.json`](../../../analysis/ov5640_stereo_20261026/known_config_validation/verification.json)。隔离工程和可复跑脚本在同目录，不操作 W6 工程。

- 表与序列器：27 项值/掩码/末项、无效索引、背压稳定、非末项和末项延时、向上取整、100 MHz×300 ms 的溢出边界及错误保持。
- 真实 SCCB：模拟从设备解码地址 `78/79`、寄存器和数据；验证全掩码不读、部分掩码读改写、忙时输入锁存、读写引擎互斥及读/写中途复位后恢复。
- 双路集成：每路 27 次写、6 次独立读，左右旧值不同仍各自保留未选位；检查 PWDN/RESET 等待、最终 300 ms 缩时门控及无末项 ready 死锁。每路严格检查 39 个 START、33 个 STOP。
- 异常：实际发送速度超过缩短的事务超时后保持错误，晚到完成不能变成成功，复位恢复安全控制脚和释放总线。既有 DVP、PLL、默认时序回归保留其原覆盖范围。

真实总线模型暴露并修复了读原语两个边沿问题：重复 START 后增加低电平首位准备，避免读地址少一位；STOP 准备阶段保持 SCL 低，避免 SDA 下降/SCL 上升同时发生形成额外 START。旧读测试的从设备原先只等八个地址时钟便送数据，现修正为完整八位加第九时钟，并检查恰好两个 START/一个 STOP。初始失败证据保留于 `known_config_validation/pre_repair/`。

主要新测试位于 `../../tb/ov5640_stereo/tb_ov5640_known_config*.v` 和 `tb_ov5640_masked_write.v`；动态延时集成测试缩放 `SYS_CLK_HZ` 以缩短运行，不代表对实际相机或电源进行了测量。

新增入口另外完成 xc7z020clg400-1 的正常顶层综合，未发现多驱动或黑盒；pad 连接证据见 [`synth_final_pad_buffers.txt`](../../../analysis/ov5640_stereo_20261026/known_config_validation/synth_final_pad_buffers.txt)。综合 DRC 仍有未指定管脚/IOSTANDARD、独立 Zynq 壳缺 PS7、SCL 只使用输出缓冲及延时乘法器流水建议；本次未提供物理约束，不是完整发布门禁。最初 OOC 综合的三态转逻辑警告按 AMD [AR 000034588](https://adaptivesupport.amd.com/s/article/000034588?language=en_US) 与 [AR 1651](https://adaptivesupport.amd.com/s/article/1651?language=en_US) 核对，最终以正常综合的单 pad 缓冲及 I=GND 为依据。没有布局布线、输入时序、ACK/器件存在性或板上验收。

2026-10-26 默认时序修改已完成 Vivado 2024.1 XSim 行为仿真：新增 `tb_ov5640_timing_defaults.v` 加原有 8 个自检均通过。新增检查在输出边沿上计数，覆盖 100 MHz、50 MHz、125000003 Hz 参数对应的等待/超时周期数及实际 SCL 高低半周期；另检查向上取整、低频至少 1 周期、大频率整数计算和旧位置参数覆盖。不同 `SYS_CLK_HZ` 用例检查的是频率参数换算后的周期数，不代表已用硬件产生并测量了这些系统时钟。

既有回归覆盖上电状态、双路发送完成等待和超时、RGB565 字节序和坏帧恢复、独立相机 PCLK、开漏 SCCB 单路/双路写、重复起始读回及五项 PLL 配置流。逐测试完整编译/展开/运行日志及汇总见 [`timing_defaults_validation/verification.json`](../../../analysis/ov5640_stereo_20261026/timing_defaults_validation/verification.json)。这些检查不包含板级输入时序、完整相机模式表、布局布线或板上采图验证。

在仓库根目录的 PowerShell 执行：

```powershell
New-Item -ItemType Directory -Force project/_tmp | Out-Null
iverilog -g2012 -s tb_ov5640_dvp_capture -o project/_tmp/tb_ov5640_dvp_capture.vvp `
  project/fpga/rtl/ov5640_stereo/ov5640_dvp_capture.v `
  project/fpga/tb/ov5640_stereo/tb_ov5640_dvp_capture.v
vvp project/_tmp/tb_ov5640_dvp_capture.vvp

iverilog -g2012 -s tb_ov5640_stereo_capture_pair -o project/_tmp/tb_ov5640_stereo_capture_pair.vvp `
  project/fpga/rtl/ov5640_stereo/ov5640_dvp_capture.v `
  project/fpga/rtl/ov5640_stereo/ov5640_stereo_capture_pair.v `
  project/fpga/tb/ov5640_stereo/tb_ov5640_stereo_capture_pair.v
vvp project/_tmp/tb_ov5640_stereo_capture_pair.vvp

iverilog -g2012 -s tb_ov5640_sccb_write -o project/_tmp/tb_ov5640_sccb_write.vvp `
  project/fpga/rtl/ov5640_stereo/ov5640_sccb_write.v `
  project/fpga/tb/ov5640_stereo/tb_ov5640_sccb_write.v
vvp project/_tmp/tb_ov5640_sccb_write.vvp

iverilog -g2012 -s tb_ov5640_stereo_sccb_pair -o project/_tmp/tb_ov5640_stereo_sccb_pair.vvp `
  project/fpga/rtl/ov5640_stereo/ov5640_sccb_write.v `
  project/fpga/rtl/ov5640_stereo/ov5640_stereo_sccb_pair.v `
  project/fpga/tb/ov5640_stereo/tb_ov5640_stereo_sccb_pair.v
vvp project/_tmp/tb_ov5640_stereo_sccb_pair.vvp

iverilog -g2012 -s tb_ov5640_stereo_camera_init -o project/_tmp/tb_ov5640_stereo_camera_init.vvp `
  project/fpga/rtl/ov5640_stereo/ov5640_stereo_camera_init.v `
  project/fpga/tb/ov5640_stereo/tb_ov5640_stereo_camera_init.v
vvp project/_tmp/tb_ov5640_stereo_camera_init.vvp

iverilog -g2012 -s tb_ov5640_stereo_top -o project/_tmp/tb_ov5640_stereo_top.vvp `
  project/fpga/rtl/ov5640_stereo/ov5640_dvp_capture.v `
  project/fpga/rtl/ov5640_stereo/ov5640_stereo_capture_pair.v `
  project/fpga/rtl/ov5640_stereo/ov5640_sccb_write.v `
  project/fpga/rtl/ov5640_stereo/ov5640_stereo_sccb_pair.v `
  project/fpga/rtl/ov5640_stereo/ov5640_stereo_top.v `
  project/fpga/tb/ov5640_stereo/tb_ov5640_stereo_top.v
vvp project/_tmp/tb_ov5640_stereo_top.vvp
```

已覆盖：低字节先到的 RGB565 拼接、帧首/行尾标记、正确帧完成、奇数字节和超宽错误、超宽像素抑制、坏帧后恢复、不同 PCLK 双路采集、SCCB 写地址/寄存器/数据顺序和开漏起止条件、双路 SCCB 写事务、基础顶层双时钟采集联调、PWDN/RESET 阶段及外部寄存器流握手/双路完成等待/缺失 done 超时。读事务自检用模拟从设备回传 `0x56`，验证重复起始和 8 位采样；PLL 配置自检检查五项寄存器值、顺序、末项标记和每次写事务的完成握手。它们是 RTL 仿真结果，不代表目标初始化表、实际相机时序、电气连接、CDC、DDR 带宽或板上功能已验证。

## 后续接入顺序

双路 SCCB 初始化、RESET/PWDN 控制及物理引脚 XDC 已完成；后续按以下顺序接入。

1. 核对实际板卡/模组版本、线束、供电与 IO 电平，并确认实际摄像头输出符合当前初始化表的尺寸、VSYNC 极性和 RGB565 格式。
2. 为各路采集域添加独立异步 FIFO，并定义帧缓冲溢出处理；坏帧不得提交给消费者。
3. 将现有相机端口、物理引脚约束及 FIFO/DDR 通路接入 W6 BD；当前 W6 HDMI 的 MM2S 输出不能代替相机的 S2MM 写入通路。
4. 补齐基于传感器规格或实测的外部 IO 时序，完成 CDC/复位与初始化控制路径的时序收敛，再生成同批 bit/HWH 并冷启动进行真机验收。独立引脚验证已完成布局布线，但整体时序尚未收敛；不能依赖 RTL 帧输出代表传感器已初始化。

模块侧 P1 接线核对记录：`project/analysis/ov5640_stereo_20261026/interface_and_pin_map.md`。

## 2026-10-27 摄像头物理约束

最新版接线已写入统一JSON并派生project/fpga/xdc/ov5640_stereo_pins.xdc。OV1 PCLK=Y9、OV2 PCLK=U7；OV1 VSYNC=W10、OV2 D2=W18，其余按用户最新版，PWDN=R16/U17。当前映射跨RPi两半区，取代旧连续分区。

XDC应用于具备30根相机端口的顶层，配套load_ov5640_pins.tcl在read_xdc前完成全部端口/冲突检查，不自动加入无相机端口的W6。生成器--check和独立Vivado检查见../../../analysis/ov5640_stereo_20261026/pin_configuration_validation_20261027/README.md。物理约束完成不代表外部输入时序、系统集成或板上采图通过。
