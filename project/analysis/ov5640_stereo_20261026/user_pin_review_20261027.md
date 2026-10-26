# 2026-10-27 最新版摄像头引脚修改记录

状态：已完成统一JSON和物理XDC落地，取代原建议。旧候选只改四项：

| 相机/信号 | 用户候选 | 本次采用 | RPi物理脚 |
|---|---|---|---:|
| OV1 PCLK | W10 | Y9 | 40 |
| OV1 VSYNC | Y9 | W10 | 23 |
| OV2 PCLK | W18 | U7 | 11 |
| OV2 D2 | U7 | W18 | 3 |

其余26根含两路沿用的PWDN保持原安排。W10/W18是普通IO；Y9=IO_L14P_T2_SRCC_13、U7=IO_L11P_T1_SRCC_13满足单端时钟P侧要求。没有专用时钟布线绕过。DO、VSNC、RST分别规范为D0、VSYNC、RESET。

完整表见[当前接线](interface_and_pin_map.md)，唯一机读来源[JSON](physical_pin_map_20261027.json)，生成结果[物理XDC](../../fpga/xdc/ov5640_stereo_pins.xdc)。旧分区版本保存在本次验证目录before/，已被取代。

Pmod A/B旧SPI外部端口及约束已释放，内部传感器/DMA/KWS仍保留，见[SPI释放记录](../pmod_spi_release_20261027/README.md)。camera XDC不自动加入没有这些端口的W6。

实际检查及未覆盖边界见[本次验收](pin_configuration_validation_20261027/README.md)。未修改已发布bit/HWH，未部署/运行中加载固件。真实接线、电平、采图及外部输入时序仍待验收。

依据：本目录保留的TUL v1.1表22、PYNQ v3.0.1 base.xdc，以及AMD本地库UG472 Clock-Capable Inputs。
