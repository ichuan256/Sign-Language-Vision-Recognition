# 720p30子表寄存器依据

日期：2026-10-26。当前目标1280×720、标称30fps、24MHz XCLK、RGB565低字节先出、8-bit DVP。旧1080p/168MHz候选已停用，历史日志保留。

27项子表不含完整模拟/ISP基表、窗口、binning或stream-on。308项完整启动表见 [startup_sequence.md](startup_sequence.md)。左右相机分别读改写，保留未选择位。

| 地址 | value | mask | 等待ms |
|---|---|---|---|
| 0x3034 | 0x18 | 0xff | 0 |
| 0x3035 | 0x20 | 0xff | 0 |
| 0x3036 | 0x54 | 0xff | 0 |
| 0x3037 | 0x13 | 0xff | 0 |
| 0x3108 | 0x01 | 0xff | 0 |
| 0x3808 | 0x05 | 0xff | 0 |
| 0x3809 | 0x00 | 0xff | 0 |
| 0x380a | 0x02 | 0xff | 0 |
| 0x380b | 0xd0 | 0xff | 0 |
| 0x380c | 0x07 | 0xff | 0 |
| 0x380d | 0x64 | 0xff | 0 |
| 0x380e | 0x02 | 0xff | 0 |
| 0x380f | 0xe4 | 0xff | 0 |
| 0x3a08 | 0x00 | 0xff | 0 |
| 0x3a09 | 0xdd | 0xff | 0 |
| 0x3a0a | 0x00 | 0xff | 0 |
| 0x3a0b | 0xb8 | 0xff | 0 |
| 0x4300 | 0x6f | 0xff | 0 |
| 0x501f | 0x01 | 0xff | 0 |
| 0x3a0d | 0x04 | 0xff | 0 |
| 0x3a0e | 0x03 | 0xff | 0 |
| 0x4740 | 0x20 | 0x20 | 0 |
| 0x3503 | 0x00 | 0x03 | 0 |
| 0x3406 | 0x00 | 0x01 | 0 |
| 0x3c01 | 0x80 | 0x80 | 0 |
| 0x3c00 | 0x04 | 0x04 | 300 |
| 0x3a00 | 0x20 | 0x24 | 0 |

## 时钟与曝光

- VCO=24MHz/3×84=672MHz；3035系统分频/2、3037 root/2、3034 bit divider/2、3108 PCLK root/1，PCLK=84MHz。
- SCLK root/2，内部SCLK=42MHz；FPGA控制器仍100MHz。
- HTS1892/VTS740，42,000,000/(1892×740)=29.998285812fps，标称30fps。
- 50/60Hz band step=221/184，曝光预算VTS-4=736行，max bands=3/4。完整表曝光种子221行约9.9555ms、增益1×。
- 460c bit1=0选择自动PCLK，不能将3824手动分频值再直接除到当前PCLK上。

固定来源：[Linux v6.12 OV5640驱动](https://github.com/torvalds/linux/blob/v6.12/drivers/media/i2c/ov5640.c)，SHA-256见startup_sequence.md。720p表28项，DVP窗口(0,250,2624,1456)、偏移(16,4)、HTS1892/VBLANK20；模式事实与时钟按本目标同步。

生成器检查最终寄存器计算PCLK≤96MHz、VCO范围、模式元数据、曝光及尺寸一致性。SCCB原语不提供完整I2C ACK、时钟延展或卡低恢复；完整启动使用ID及所选寄存器检查阻止部分错误后的stream-on。

本次证据见 [mode_720p30_validation/](mode_720p30_validation/)。实际图像、帧率、输入时序、双目同步、DDR与HDMI仍未验收。旧known_config_validation/、startup_validation/等日志不视为新版综合或板上验收。
