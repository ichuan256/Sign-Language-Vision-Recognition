# Pmod A/B SPI 外部接口释放记录

日期：2026-10-27。状态：工程源码修改完成；Vivado 2024.1 BD 校验及 wrapper 生成通过；未构建或部署新固件。

## 修改范围

- system.bd 移除 spia/spib 的 SCLK、MOSI、MISO、CS 八组外部端口，共十二根信号；移除八条外部连线。保留的 sif_l/miso、sif_r/miso 接到一位 const_zero，输出不再接外部引脚。
- sign_glove_master.xdc 移除十二根 SPI PACKAGE_PIN/IOSTANDARD 约束；其他 Arduino 外设约束保持原样。JA/JB 其余四个信号脚原本无分配，因此W6 的 master/interfaces 约束中十六个 Pmod 信号脚均未分配；独立摄像头候选可使用自己的约束分配这些引脚。
- w6_interfaces.xdc 移除两路 SPI 生成时钟、输入/输出延迟和多周期约束；音频、HDMI 时序段逐字保持原样。
- w6_hdmi_build.tcl、w6_timing_inspect.tcl 的输入时序报告移除已不存在的 SPI 输入；构建新增 wrapper SPI 端口残留检查。
- 新增 w6_release_pmod_spi.tcl；HDMI BD 补丁和 timing_prepare 均调用它，使旧工程进入构建时也执行接口释放。脚本可以重复执行。
- 更新仓库中的旧 imported wrapper，使其与 Vivado 新生成的 wrapper 完全一致，避免旧端口残留。

本次只释放外部接口；内部传感器、DMA、旧 KWS 的完整架构裁剪仍属后续 M0b。摄像头端口尚未加进此 W6 BD。

## 实际验证

Vivado MCP 使用已有空闲 Tcl 会话 vivado-20261026-233541-f9f60dfa，确认工具为 2024.1 后打开当前工作区 glove.xpr：

- 使用 delete_bd_objs 移除端口/连线，connect_bd_net 将两个 MISO 接到 const_zero，保存 BD；外部 SPI 端口计数为零。
- validate_bd_design 返回 exit_code=0。
- make_wrapper 返回 exit_code=0，新 wrapper 无 spia_/spib_，保留 HDMI、音频、DDR、FIXED_IO、IIC_1 和按键。
- 连续两次执行释放脚本均返回 exit_code=0，仍只有原 const_zero_dout 网络，未增加重复端口或连线。

verify_release.py 比较 before 快照和最终源码，确认端口只减少预期八组，BD 内部组件/接口/其他连线不变，两路 MISO 正确接零，原十二项以外的管脚约束不变，音频/HDMI 时序原样保留，W6 master/interfaces 中十六个 Pmod IO 均无活动物理分配，两个 wrapper 一致，构建入口有释放钩子。运行结果为 PASS，详见 verification.json。git diff --check 通过。

复跑静态检查：python -X utf8 project/analysis/pmod_spi_release_20261027/verify_release.py。该检查使用本目录 before 快照与本机新生成的 wrapper；不替代 Vivado 构建。

Vivado 打开旧工程时提示旧板卡仓库路径不存在、旧 PS DDR skew 参数及模块接口元数据警告；BD 校验存在既有 PS 时钟参数传播警告，wrapper 生成存在既有 AXI arlock 宽度警告。本次未修改对应组件或连线，也未把 BD 校验等同于综合/时序/板上通过。

Vivado 自动更新的 sif_l/sif_r ADC_MASK、merge_stream 参数顺序与本次无关，已保存在 automatic_metadata 后恢复原内容；最终变更不包含这些参数修改。

## 固件边界

已发布 project/board/w6/kws_hdmi.bit 与 .hwh 哈希均保持原样，详见 verification.json。未运行综合、实现、位流生成、部署或板上采图。

板上已经加载的旧固件不会因源码修改自动释放 Pmod。需后续生成配套 bit/HWH，成对部署后冷启动一次，新接口才在硬件生效；禁止运行中为此再次加载 bitstream。

2026-10-27 提交前复核：验证脚本的 Pmod 空闲检查仅覆盖 W6 的 master/interfaces，避免把独立相机候选 XDC 误算作 W6 占用；原有组件、接口、wrapper 和发布哈希检查保持。
