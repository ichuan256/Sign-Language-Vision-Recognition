# 2026-10-27 用户最新版双目引脚复核

2026-10-27 更新：Pmod A/B 的外部 SPI 端口、12 根管脚约束及两组 SPI 时序约束已从工程源码移除；内部保留的两路 MISO 接 const_zero。Vivado 2024.1 BD 校验和新 wrapper 生成通过。旧传感器/DMA/KWS 内部链路仍保留，完整 M0b 裁剪未完成。已发布及板上 bit/HWH 未重建或替换，实物引脚须在新固件成对构建、部署并冷启动后才按新接口生效。记录：project/analysis/pmod_spi_release_20261027/README.md。

按第一组为 OV1、第二组为 OV2 理解。DO:w8 规范为 D0:W8，VSNC 规范为 VSYNC，RST 规范为 RESET。本文记录用户候选和最小修正建议；原 physical_pin_map_20261027.json、活动 XDC、RTL 和板上固件未更改。

## 用户候选与建议

括号内为 PYNQ-Z2 Raspberry Pi 接头物理脚号，依据 TUL 手册 v1.1 表22；不是摄像头 P1 脚号。

| 信号 | OV1 用户候选 | OV1 建议（RPi脚） | OV2 用户候选 | OV2 建议（RPi脚） |
|---|---|---|---|---|
| SCL | W9 | W9（37） | V10 | V10（21） |
| SDA | Y8 | Y8（35） | V8 | V8（19） |
| VSYNC | Y9 | W10（23） | U19 | U19（26） |
| HREF | A20 | A20（38） | U18 | U18（31） |
| RESET | B19 | B19（36） | U8 | U8（15） |
| D0 | W8 | W8（33） | V7 | V7（13） |
| D1 | B20 | B20（32） | W6 | W6（16） |
| D2 | Y7 | Y7（18） | U7 | W18（3） |
| D3 | Y17 | Y17（28） | C20 | C20（12） |
| D4 | Y6 | Y6（10） | V6 | V6（8） |
| D5 | F20 | F20（22） | Y19 | Y19（29） |
| D6 | Y16 | Y16（27） | W19 | W19（5） |
| D7 | F19 | F19（24） | Y18 | Y18（7） |
| PCLK | W10 | Y9（40） | W18 | U7（11） |
| PWDN | 未列出 | 沿用 Arduino D6 / R16 | 未列出 | 沿用 Arduino D7 / U17 |

## 必须处理的问题

1. 用户候选的28根信号没有封装脚重复，且覆盖RPi全部28个IO。但W10=IO_L16P_T2_13、W18=IO_L22P_T3_34均为普通IO，不适合作为当前直接使用PCLK采集的时钟输入。最小修改是OV1交换PCLK/VSYNC，OV2交换PCLK/D2，共改四个条目。Y9=IO_L14P_T2_SRCC_13、U7=IO_L11P_T1_SRCC_13均为时钟能力P端。UG472规定单端时钟应使用P端；不通过CLOCK_DEDICATED_ROUTE=FALSE绕过专用时钟布线检查。
2. 候选未列两路PWDN，建议沿用既有Arduino D6=R16、D7=U17分配。28根RPi信号加两根PWDN合计30根，不重复。
3. 旧project/fpga/xdc/sign_glove_master.xdc第20～30行仍把Y18、Y19、Y16、Y17、U18、U19分给spia端口；新相机工程需要移除或重分配对应旧端口和约束。功能闲置不代表IO已释放。
4. v1.0手册的RPi映射有误，按v1.1表22核对：Y7=18、Y6=10、F20=22、U19=26、U18=31、Y19=29。因此这版跨越先前OV1=23～40、OV2=1～22的分区；如果仍要求保持两端分区，需另外重排。
5. SCCB仍使用开漏/三态；供电、共地、IO电平和上拉按interface_and_pin_map.md的电气边界复核。PCLK与数据跨IO bank，时钟脚正确不代表布局布线和输入时序通过；84MHz仍是配置计算值，未实测。

## 核对范围

静态检查范围：每组完整14信号、两组封装脚唯一性、RPi覆盖、推荐仅四项变化、两路PWDN唯一性及旧SPI占用。未执行Vivado综合/布局布线、板上接线或相机采图。

## 依据

- TUL PYNQ-Z2 Reference Manual v1.1，第18节表22，PDF第30页：https://dpoauwgwqsy2x.cloudfront.net/Download/PYNQ_Z2_User_Manual_v1.1.pdf
- Xilinx/PYNQ v3.0.1 base.xdc：https://raw.githubusercontent.com/Xilinx/PYNQ/v3.0.1/boards/Pynq-Z2/base/vivado/constraints/base.xdc
- AMD UG472，Clock-Capable Inputs：https://docs.amd.com/v/u/en-US/ug472_7Series_Clocking
- backup/pynq-z2/PYNQ-Z2 v1.0.xdc，仅采用核对过的封装功能注释，不采用其中过期的RPi映射。
- 当前旧SPI约束：project/fpga/xdc/sign_glove_master.xdc第20～30行。
