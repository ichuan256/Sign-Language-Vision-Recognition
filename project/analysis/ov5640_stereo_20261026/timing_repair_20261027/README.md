# OV5640 启动控制时序修复验收（2026-10-27）

Vivado/XSim 2024.1，xc7z020clg400-1，沿用原 pin_validation_top 和物理引脚。系统时钟 125 MHz（8 ns）；两路 PCLK 约 84 MHz（工具取整到 11.905 ns）。最终完成综合、优化、布局、布线。

| 项目 | 修复前 | 最终结果 |
|---|---:|---:|
| 系统域 WNS | -20.913 ns | +1.493 ns |
| 最差数据路径 | 28.899 ns / 35 级 | 6.242 ns / 9 级 |
| OV1 / OV2 域 WNS | +6.097 / +6.599 ns | +7.110 / +7.317 ns |
| 全局 WHS | — | +0.122 ns |
| TNS / THS | — | 0 / 0 |
| Slice LUT / FF | 1571 / 796 | 876 / 793 |

最终最差路径是 delay_cycles_reg[1] 到 FSM_onehot_state_reg[3]/CE。验收门禁确认建立/保持违例为 0、内部未约束端点为 0。1452 条可布线网络全部布通，路由错误为 0。

## 修改

- ov5640_stereo_startup.v：动态乘加除替换成 16 拍逐位商/余数递推，再用 1 拍向上取整。每步维持 processed_ms * SYS_CLK_HZ = 1000*q + r、0<=r<1000。保留完整 16 位毫秒范围；零延时直接跳过转换。非零项在 SCCB 事务前增加 17 个系统时钟（125 MHz 下 136 ns），事务完成后的等待长度不变。ms_cycles 函数仅保留作既有测试的参考，不再参与运行时 RTL 数据路径。
- 计数器宽度按完整输入范围和参数计算：125 MHz 下等待/延时为 33 位、超时为 21 位；常量运算在 elaboration 完成。
- ov5640_stereo_startup_capture.v：将 init_done && !init_error 在系统域寄存为 capture_reset_n，再交由两个采集器各自的复位同步链异步置位、同步释放。外部复位异步清除源寄存器；停 PCLK 时仍保持复位，恢复时两个 PCLK 边沿后释放。完成/失败状态保持到复位，失败不会在成功后无复位地改变状态。
- ov5640_dvp_capture.v：reset_sync 两级加 ASYNC_REG 和 SHREG_EXTRACT 属性。
- project/fpga/scripts/ov5640_startup_cdc.tcl：仅从 capture_reset_n 源寄存器到四个复位同步器 CLR 脚设置例外；检查层级、数量和 ASYNC_REG。支持综合自动反相后的 *_reg_inv 名称。没有整个时钟域的 false path 或 multicycle。

最终 cdc.rpt 仅有两条 CDC-9 Info，无 Warning/Critical。exceptions.rpt 显示两项例外、每项两个端点，覆盖率均为 100%。check_timing.tcl 确认同步器 Q→D 仍计时，余量 +11.167/+11.177 ns；第二级到采集逻辑的复位 recovery 仍计时，余量 +7.477/+7.465 ns。

## 实际功能验证

9 个 XSim 测试全部通过，完整 compile/elaborate/simulate 日志在各 tb_* 子目录，统一核验结果及源码 SHA256 在 verification.json。

- tb_ov5640_delay_conversion：6 种频率（1、999、1001、125000000、125000003、2000000000 Hz）各 14 个输入，含 0/1/20/300/999/1000/1001/32767/32768/65534/65535 及交错位型；实际驱动控制器，比较硬件换算寄存器与独立 64 位参考。低频用例逐拍验证 SCCB 完成后的真实等待周期，另测转换中复位及重启。高频最大延时检查转换值，不模拟等待 65 秒。
- tb_ov5640_startup_defaults/controller：参数取整及低频钳位、两颗相机分别完成、单路超时、无效 ROM/缺终止项、错误保持、复位恢复和延时。
- tb_ov5640_sccb_register_access/stereo_startup：只读、掩码读改写、零/全掩码、忙时锁存、完整 308 项双路初始化、ID/读回/stream 检查失败、错误相机掩码、stream 顺序及故障后复位重启。
- tb_ov5640_startup_capture：初始化前禁止采集，两路独立 PCLK；一路停钟时保持复位，恢复的第 1 边沿仍复位、第 2 边沿释放；再次停钟时全局复位立即清除输出。
- tb_ov5640_dvp_capture/stereo_capture_pair/720p_frame：RGB565 低字节在前、SOF/EOL、独立双路帧计数、奇数字节及超宽行拒绝、异常后恢复；720p 三帧核对 921600 像素/720 EOL/1 SOF、短末行错误及下一正常帧恢复。

第一次复用旧脚本时，720p 测试在 10 ms 截止而未完成，并非断言失败；原日志保留在 720p_initial_10ms_incomplete.log。新脚本对此测试采用其 watchdog 对应的 100 ms 上限，实际在 65.953409664 ms 完成。增强后的 capture 测试已单独重编重跑。initial_regression_results.txt 保留初轮状态；最终按每个测试完整日志核验，不能只看最后两项复跑的 regression_results.txt。

## 复跑

通过 Vivado MCP 复用空闲的 2024.1 Tcl 会话。关闭当前隔离工程后，以本目录为 E，逐条独立执行：

```tcl
source $E/prepare.tcl
synth_design -top pin_validation_top -part xc7z020clg400-1
source $E/apply_constraints.tcl
opt_design
place_design
route_design
source $E/collect_reports.tcl
source $E/check_timing.tcl
```

仿真首次用 prepare_sim.tcl 建立专用 startup.xpr，然后 source 本目录 run_regression.tcl。重跑已有工程时打开 xsim_project/startup.xpr，cd 到本目录，并 unset -nocomplain startup_tops 以恢复全部测试列表，再运行该脚本。最后在仓库根执行：

```powershell
python project/analysis/ov5640_stereo_20261026/timing_repair_20261027/verify_results.py
```

原引脚验证报告保持为修复前基线；before/ 为本次修改前源码，first_route/ 是完成延时修复但复位组合逻辑尚未清理的中间报告。最终证据只使用本目录根报告及 routed.dcp。

## 边界与资料

这是独立顶层已约束内部路径的时序验收，不是完整 W6、bit/HWH 发布或板上相机验收。24 个输入和 12 个输出仍无外部 I/O delay，未补造传感器电气参数。report_cdc 不覆盖没有 input delay 的外部端口；验证顶层按键复位也不构成生产复位方案验收。DRC 保留 2 条 SCL 输入缓冲缺失警告（只驱动、不读 SCL）和 1 条独立顶层未使用 PS7 警告。

综合仍报告历史非实例化 camera_init/camera_top 参数声明顺序警告；clock_utilization 仍有原先的 HSR_BOUNDARY_TOP/Virtual grid 警告。实际引脚检查、布线、时序报告均另行通过。没有生成/部署固件，也没有修改 W6 工程或物理引脚。未来集成必须调用上述 CDC 约束过程并重新验收整板。

本次实际检索 AMD 本地库：
- [UG903 Asynchronous Clock Domain Crossings](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints/Asynchronous-Clock-Domain-Crossings)：异步跨域需要同步结构及对应例外；不能信任无相位关系的跨域 slack。
- [UG949 Valid Startpoints and Endpoints](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Valid-Startpoints-and-Endpoints)：例外起点使用 sequential cell，避免 Q pin 作为非法起点及路径分段。

子代理未交付实现；用户要求后由主代理独立完成。无可核算的完整模型用量和价格记录，费用未知。

