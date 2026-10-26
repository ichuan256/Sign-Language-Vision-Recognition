# OV5640切换720p30验收记录

日期：2026-10-26。用户选定1280×720、标称30fps、RGB565 LE、8-bit DVP。24MHz XCLK，候选SCLK42MHz/PCLK84MHz；HTS1892/VTS740，计算29.998285812fps。PCLK比96MHz规格上限低12MHz，这只是频率规格差值，不是输入时序裕量。

## 已修改

接收核和各封装默认尺寸统一1280×720；PLL3035改为20，完整表使用固定Linux v6.12的28项720p模式、subsampling/binning和相应窗口。27项子表、308项ROM、独立读回契约、曝光/防闪烁及生成器均同步。原文件快照见before/及before_manifest.json，差异见mode_change.patch。

## 实际检查

- 配置：生成器离线--check检查ROM/JSON无漂移，按最终寄存器计算VCO、PCLK/SCLK、输出尺寸和行帧长，并检查PCLK≤96MHz。verify_mode.py另检查27项子表与独立合同一致，以及拒绝旧PLL、错误尺寸、关闭binning、错误时钟元数据、提前stream-on和写ID寄存器。
- 像素与边界：tb_ov5640_720p_frame.v在约84MHz行为激励下逐像素核对RGB565 LE，完整帧921600像素/720个EOL/一个SOF；再发送短一像素的末行确认报错，下一完整帧恢复。默认尺寸检查覆盖接收核和高层壳。此用例并不模拟真实曝光、传感器帧节拍或物理输入延迟。
- DVP：既有tb_ov5640_dvp_capture.v覆盖字节序、SOF/EOL、奇数字节、超宽抑制及恢复；tb_ov5640_stereo_capture_pair.v与startup_capture验证独立PCLK、初始化前禁止采集，以及停止PCLK后的安全复位。
- SCCB/启动：既有单路/双路写、重复START读、按位独立读改写、握手背压与延时测试；完整启动检查双相机ID、308项执行、所选寄存器读回及最后stream-on。故障覆盖两路ID/读回不匹配、单路超时、无效ROM及缺末项、忙时/终态重复启动、复位后重试恢复。SCCB模型不提供图像物理仿真。
- 时序参数：100MHz、50MHz和非整分频参数的等待/超时及SCL边沿；低频至少一周期、向上取整、64位长等待与旧位置参数兼容。

Vivado2024.1 XSim共19项全部通过，详细结果regression_results.txt及各tb目录。完整帧测试补齐未用输入连接后单独复跑通过，见full_frame_final_results.txt；RTL功能此后未变化。verification.json保存源哈希。

## 边界与警告

保留原有SYS_CLK_HZ在参数声明前使用的警告（维持旧位置参数兼容），相应换算与覆盖已实际测试。Vivado报告GCC自动探测警告，但编译、展开和仿真均成功；新测试的未连接输入警告已消除。未改板端、BD、约束或发布bit/HWH，未重新综合和布局布线。真实时钟、FPS、极性、电平、输入时序、双目同步、DDR/HDMI仍待后续验收。

同级startup_validation/、known_config_validation/、timing_defaults_validation/及旧audit/acceptance JSON是迁移前版本证据，不代表新模式硬件验收。

## 复跑

仓库根PowerShell运行python -X utf8 project/scripts/ov5640/generate_startup_table.py --check，以及python -X utf8 project/analysis/ov5640_stereo_20261026/mode_720p30_validation/verify_mode.py。XSim脚本run_regression.tcl在隔离工程project/_tmp/ov720p_sim/mode720p30.xpr中执行；Vivado工作目录须为本证据目录。
