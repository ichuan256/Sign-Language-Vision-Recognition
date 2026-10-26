# 已确定初始化子表的寄存器依据

日期：2026-10-26。用户要求将已确定值写入初始化表；本文记录本次表项的范围及独立数值核对。实现入口和最终检查结果由 RTL 目录 README 与 `known_config_validation/` 汇总。

## 范围

本次子表固定 24 MHz 相机 XCLK、候选 1920×1080/30 fps、RGB565 低字节先出，以及 FPGA 上升沿采样所配套的相机下降沿输出。系统控制逻辑继续使用 W6 的 100 MHz 时钟，不能将它与相机内部时钟混用。

尚未确定的全局模拟/ISP 序列、裁剪窗口、VSYNC/HREF 位值、曝光及增益上限不在本次子表中。该子表不包含 stream-on。若执行入口对相机进行硬复位，完整启动流程须在同一次复位之后加入基础初始化，随后再应用本子表；不能依赖复位之前写入的基础配置。

## 表项合同

掩码语义：`new = (old & ~mask) | (value & mask)`；`mask=0xff` 表示完整字节写入。部分掩码需要分别读回左右相机的旧值，不能用同一只相机的旧值覆盖两路。表项共 27 个，顺序以实现文件为准；下表按功能分组。

| 地址 | value | mask | 含义/依据 |
|---|---|---|---|
| 0x3034 | 0x18 | 0xff | 沿用已确定的 PLL 子表 |
| 0x3035 | 0x10 | 0xff | 同上 |
| 0x3036 | 0x54 | 0xff | 同上，乘数 84 |
| 0x3037 | 0x13 | 0xff | 同上，前分频 3、PLL root /2 |
| 0x3108 | 0x01 | 0xff | 同上，SCLK root /2、PCLK root /1 |
| 0x3808 / 0x3809 | 0x07 / 0x80 | 各 0xff | 输出宽度 1920 = 0x0780 |
| 0x380a / 0x380b | 0x04 / 0x38 | 各 0xff | 输出高度 1080 = 0x0438 |
| 0x380c / 0x380d | 0x09 / 0xc4 | 各 0xff | 候选 HTS 2500 = 0x09c4 |
| 0x380e / 0x380f | 0x04 / 0x60 | 各 0xff | 候选 VTS 1120 = 0x0460 |
| 0x4300 | 0x6f | 0xff | RGB565 低字节先出格式映射 |
| 0x501f | 0x01 | 0xff | ISP RGB 输出 mux |
| 0x4740 | 0x20 | 0x20 | 相机下降沿输出；保留其他极性和门控位 |
| 0x3503 | 0x00 | 0x03 | 开启自动曝光与自动增益 |
| 0x3406 | 0x00 | 0x01 | 开启自动白平衡 |
| 0x3c01 | 0x80 | 0x80 | 手动指定灯光频率 |
| 0x3c00 | 0x04 | 0x04 | 选择 50 Hz；此项后保留 300 ms 等待 |
| 0x3a00 | 0x20 | 0x24 | 开启 banding、关闭夜景延长帧周期 |
| 0x3a08 / 0x3a09 | 0x01 / 0x50 | 各 0xff | 50 Hz band step，336 行 |
| 0x3a0a / 0x3a0b | 0x01 / 0x18 | 各 0xff | 60 Hz band step，280 行 |
| 0x3a0d / 0x3a0e | 0x03 / 0x03 | 各 0xff | 最大 60 Hz / 50 Hz band 数，各为 3 |

RGB565、尺寸/HTS/VTS 及 AEC/AWB/灯光位操作按 [Linux 上游 OV5640 驱动](https://github.com/torvalds/linux/blob/master/drivers/media/i2c/ov5640.c) 的格式定义、`ov5640_set_timings()`、控制函数核对。PCLK bit 5 和防闪烁操作另核对本地 OmniVision DVP 指南 §4.2、§4.7.8，相关页的提取与渲染证据在 `configuration_evidence/`。0x4740 低两位在资料和驱动之间存在差异，故掩码只选 bit 5。

0x3c00 的 300 ms 来自 Linux 公共初始化表的该项延时；在本次子表中显式保留这个等待。它不是所有写寄存器事务的通用等待，也不意味着仅此一项就完成了公共初始化。

## 防闪烁数值的独立计算

本次联网核对 Linux 上游的 `ov5640_get_sysclk()` 与 `ov5640_set_bandingfilter()`，以它们使用的单位和整数截断规则进行计算。这里只记录数值和接口事实，不复制驱动实现。

```text
XCLK                  = 24 MHz
PLL VCO               = 24 MHz / 3 × 84 = 672 MHz
camera internal SCLK  = 672 MHz / 1 / 2 × 2 / 4 / 2 = 84 MHz
HTS                   = 2500
VTS                   = 1120
exposure budget       = VTS - 4 = 1116 lines
50 Hz band step       = 84,000,000 / 2500 / 100 = 336 = 0x0150
60 Hz band step       = 84,000,000 / 2500 / 120 = 280 = 0x0118
max 50 Hz bands       = floor(1116 / 336) = 3
max 60 Hz bands       = floor(1116 / 280) = 3
```

对应 Linux 的整数单位为 SCLK / 10000 = 8400；50 Hz 计算 `floor(8400×100/2500)`，60 Hz 计算 `floor(floor(8400×100/2500)×100/120)`，本组参数得到同样结果。相机内部 SCLK=84 MHz 与候选 DVP 字节 PCLK=168 MHz 是不同层级的时钟，也都不是 FPGA 控制器的 100 MHz。

以上均依赖所列 XCLK/PLL/HTS/VTS。以后改变这些值时，band step 和 max band 必须一起重算。当前没有把这些计算当成传感器寄存器已生效、图像质量已达标或板上已达到 30 fps 的证据。

## 验收关注点

- 全字节表项与按位表项分开验证，27 项均需符合本合同。
- 左右相机返回不同旧值时，未选中的位各自保留。
- 初始化控制器的末项完成不会再次拉高 `cfg_ready`，序列器须使用末项发送完成事件，避免死等 ready。
- 表项等待从该项两路发送完成之后开始，最终完成信号应包含末项等待。
- SCCB 原语没有 ACK/器件存在性检测，发送状态机完成不能证明传感器接受写入。

原始资料链接：

- [Linux 原始驱动](https://raw.githubusercontent.com/torvalds/linux/master/drivers/media/i2c/ov5640.c)，本次核对函数包括 `ov5640_get_sysclk()`、`ov5640_set_bandingfilter()`、`ov5640_set_timings()` 与自动曝光/增益/白平衡/灯光控制函数。
- [OmniVision DVP 应用指南 R2.13C](../../../backup/【正点原子】OV5640双目摄像头模块/【正点原子】OV5640双目摄像头模块资料/2，OV5640参考资料/OV5640_自动对焦照相模组应用指南(DVP_接口)__R2.13C.pdf)。
