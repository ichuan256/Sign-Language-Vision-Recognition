# btns_w6.xdc —— BTN0-3 按键（PYNQ-Z2 part0_pins.xml 核对：D19/D20/L20/L19）
# 配套 BD 端口 btn[3:0]（axi_gpio_btns，4 位输入）
set_property -dict {PACKAGE_PIN D19 IOSTANDARD LVCMOS33} [get_ports {btn[0]}]
set_property -dict {PACKAGE_PIN D20 IOSTANDARD LVCMOS33} [get_ports {btn[1]}]
set_property -dict {PACKAGE_PIN L20 IOSTANDARD LVCMOS33} [get_ports {btn[2]}]
set_property -dict {PACKAGE_PIN L19 IOSTANDARD LVCMOS33} [get_ports {btn[3]}]
