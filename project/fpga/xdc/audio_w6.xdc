# audio_w6.xdc —— 合一 BD 音频通路引脚约束（2026-10-15）
# 移植自 PYNQ v3.0.1 boards/Pynq-Z2/base/vivado/constraints/base.xdc，勿改引脚

# ADAU1761 codec 配置 I2C（PS I2C1 经 EMIO 走 PL 引脚）
set_property -dict {PACKAGE_PIN U9 IOSTANDARD LVCMOS33} [get_ports IIC_1_scl_io]
set_property PULLUP true [get_ports IIC_1_scl_io]
set_property -dict {PACKAGE_PIN T9 IOSTANDARD LVCMOS33} [get_ports IIC_1_sda_io]
set_property PULLUP true [get_ports IIC_1_sda_io]

# I2S 音频数据 + 主时钟
set_property -dict { PACKAGE_PIN U5   IOSTANDARD LVCMOS33 } [get_ports audio_clk_10MHz]
set_property -dict { PACKAGE_PIN R18  IOSTANDARD LVCMOS33 } [get_ports bclk]
set_property -dict { PACKAGE_PIN T17  IOSTANDARD LVCMOS33 } [get_ports lrclk]
set_property -dict { PACKAGE_PIN G18  IOSTANDARD LVCMOS33 } [get_ports sdata_o]
set_property -dict { PACKAGE_PIN F17  IOSTANDARD LVCMOS33 } [get_ports sdata_i]
set_property -dict { PACKAGE_PIN M17  IOSTANDARD LVCMOS33 } [get_ports {codec_addr[0]}]
set_property -dict { PACKAGE_PIN M18  IOSTANDARD LVCMOS33 } [get_ports {codec_addr[1]}]
