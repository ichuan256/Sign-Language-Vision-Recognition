# 双路 OV5640 引脚修改验收记录

日期：2026-10-27。结论：最新版物理接线、统一 JSON、30 根物理 XDC 和一致性检查已落地；独立验证顶层综合、布局、布线完成，管脚与时钟资源可布通。整体时序未通过，不能作为可部署固件验收。

## 实施范围

用户要求接续“修改摄像头引脚配置”对话（01a1792b-da86-71e0-a4e9-bce7d20433bb）。采用其最后完整列表并实施当时记录的最少四项修正：

| 相机/信号 | 用户列表 | 本次采用 | RPi 物理脚 |
|---|---|---|---:|
| OV1 PCLK | W10 | Y9 | 40 |
| OV1 VSYNC | Y9 | W10 | 23 |
| OV2 PCLK | W18 | U7 | 11 |
| OV2 D2 | U7 | W18 | 3 |

其余用户信号保留，PWDN 沿用 OV1 R16/Arduino D6/J4-7、OV2 U17/D7/J4-8。DO、VSNC、RST 分别规范为 D0、VSYNC、RESET。当前接线跨 RPi 两半区，取代旧连续分区方案。完整接线在[接口表](../interface_and_pin_map.md)，[JSON](../physical_pin_map_20261027.json) 为唯一生成输入；旧文档/JSON保存在 before/。

生成器为 project/scripts/ov5640/generate_pin_constraints.py，输出 project/fpga/xdc/ov5640_stereo_pins.xdc。只设置 PACKAGE_PIN/IOSTANDARD，不虚构外部输入/输出延迟，不增加 FPGA SCCB 上拉，不使用 CLOCK_DEDICATED_ROUTE=FALSE。配套project/fpga/scripts/load_ov5640_pins.tcl在read_xdc之前完成30根端口及管脚冲突检查。XDC本体仅含30条标准set_property命令。未把该文件自动加入当前没有相机端口的 W6 XPR。

本次没有修改功能 RTL、glove.xpr、system.bd、已发布 bit/HWH，也没有运行综合/位流部署脚本或操作板卡。旧SPI源码释放是前一对话已有结果，本次保留。用户取消子代理后由主代理直接完成；没有继续委派。实际模型用量、缓存和费用未获得可核算记录，不声明节省比例。

## 实际执行的检查

- 映射/数据合同：30根信号完整且唯一、P1针脚及方向、TUL v1.1 RPi物理脚映射、PWDN分配、LVCMOS33、PCLK的P侧管脚、RTL端口名称、生成文件一致性。
- 错误配置：故意注入重复封装脚、缺信号、错误板针/RTL端口/方向/P1脚/IO标准，均被拒绝；原普通IO时钟和N侧候选被拒绝。
- XDC执行：通过Tcl测试真实脚本文本，覆盖带方括号的数据位名、重复执行；缺少最后一根端口或旧SPI端口占用Y9时，在任何管脚赋值前报错。
- 原生加载：最初把循环写进XDC仅能source，read_xdc报不支持foreach/unset；已按UG903改成30条标准set_property的XDC和单独guard Tcl。最终实际执行loader/read_xdc返回0，无Error/Critical Warning，只有重复加载文件提示，见native_load_verification.json。最终各管脚赋值与布线时相同，因此复用已完成布线证据。
- 既有外设：静态比较 camera 脚与保留的 sign_glove_master/audio_w6/hdmi_w6 三份活动物理约束，无重叠。不是整个BD的camera集成测试。
- Vivado2024.1 / xc7z020clg400-1：in-memory隔离顶层实例化实际 ov5640_stereo_startup_capture，执行 synth_design、opt_design、place_design、route_design；使用30根正式camera XDC与7根验证壳板载时钟/按钮/LED约束。2473条可布线网全部完成，0布线错误；未生成bitstream。
- 网表和pad：30根camera端口均有唯一LVCMOS33分配；Y9/U7确认为SRCC P侧且分别使用BUFGCTRL_X0Y0/X0Y1；两路SDA为IOBUF、SCL为OBUFT，四个输出数据输入均接GROUND，仅控制三态/拉低。见 pad_and_clock_checks.txt 和 package_pin_properties.txt。

Python共8项测试通过，内容见 project/scripts/ov5640/test_pin_constraints.py 与 python_tests.log；不是本次重新跑过19项行为仿真。功能RTL保持原版本，原720p XSim证据仍在同级 mode_720p30_validation/，其历史结论不替代此次物理输入时序或板上验收。

## 时序、警告与限制

验证壳使用板载125MHz振荡器，SYS_CLK_HZ=125000000；它不同于W6的PS 100MHz。两路PCLK用配置计算的84MHz，Vivado按1ps分辨率将周期舍入为11.905ns，未实测。没有为取得通过添加虚构外部延迟、异步时钟分组/false path或时钟布线绕过。

- timing_summary.rpt：总体 WNS=-20.913ns、TNS=-723.368ns，时序不通过；两路PCLK域内部寄存器路径WNS分别+6.097ns、+6.599ns，仅限此独立壳。
- system_clock_timing.rpt：最差系统时钟路径从startup controller的table_index到delay_cycles，经过ms_cycles计算的DSP/进位链，35级逻辑、28.899ns数据路径。属于已有启动逻辑在该验证壳125MHz下的实际违例，不能归结为引脚错误，也不能断言W6 100MHz一定通过；需在系统集成阶段修复/验证，未在本次引脚任务中改算法。
- 系统时钟到相机域的同步/复位路径也有违例，需在正式集成中审查CDC及约束。具体输入/输出缺外部延迟，见timing_summary.rpt，输入时序尚未验收。
- DRC无Error/Critical Warning，6条Warning：DSP输入/输出流水线3项、两个SCL声明inout而实现仅输出三态的RPBF-3、隔离验证壳未含PS7的ZPS7-1。没有降级/屏蔽这些警告。
- report_clock_utilization另报HSR_BOUNDARY_TOP/Virtual grid初始化警告；保留原报告，BUFG位置、具体管脚和完成布线证据另行交叉核对。

仍未覆盖：板卡/模组实物版本和排线方向、供电余量及电平、电路延迟与信号完整性、真实SCCB读回/图像/FPS、异步FIFO与AXI/DDR、整板HDMI/音频资源和真实相机验收。没有正式candidate bit/HWH。

## 复跑

仓库根PowerShell：

    python -X utf8 project/scripts/ov5640/generate_pin_constraints.py --check
    python -X utf8 project/scripts/ov5640/test_pin_constraints.py
    python -X utf8 project/analysis/ov5640_stereo_20261026/pin_configuration_validation_20261027/verify_acceptance.py

Vivado MCP先核对空闲会话和工具版本。以下各行为独立Tcl调用，按顺序执行；不要对同一会话并发：

    source <仓库>/project/analysis/ov5640_stereo_20261026/pin_configuration_validation_20261027/prepare.tcl
    synth_design -top pin_validation_top -part xc7z020clg400-1
    source <仓库>/project/analysis/ov5640_stereo_20261026/pin_configuration_validation_20261027/apply_constraints.tcl
    opt_design
    place_design
    route_design
    source <仓库>/project/analysis/ov5640_stereo_20261026/pin_configuration_validation_20261027/collect_reports.tcl

prepare.tcl要求无打开工程，只建立in-memory隔离工程，避免覆盖W6。update_mapping.py是本次已完成的一次性迁移记录，重复执行会拒绝；日常只复跑生成器/check。

来源：本地TUL v1.1表22及 ../pin_map_sources_20261027/pynq_v3_0_1_base_reference.xdc；本次实际调用AMD本地库检索UG472 Clock-Capable Inputs和UG835的get_package_pins/get_iobanks/report_route_status，并查询Vivado2024.1命令帮助。管脚功能以当前器件数据库再次核验。

