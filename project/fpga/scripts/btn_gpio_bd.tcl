# btn_gpio_bd.tcl —— 给合一 BD 加 BTN0-3 按键 GPIO（2026-10-23）
# 目的：通电后按 BTN0 启动音频演示（板端按键监听读 0x43C10000）
# 幂等：已存在 axi_gpio_btns 则直接跳过。用法：run_btn_gpio.bat
set d [file dirname [file normalize [info script]]]
set root [file normalize [file join $d ../..]]
open_project [file join $root fpga project glove glove.xpr]
open_bd_design [get_files */system.bd]

if {[llength [get_bd_cells -quiet axi_gpio_btns]]} {
    puts "axi_gpio_btns 已存在，跳过"
} else {
    set g [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_btns]
    set_property -dict [list CONFIG.C_GPIO_WIDTH {4} CONFIG.C_ALL_INPUTS {1} \
                            CONFIG.C_IS_DUAL {0}] $g
    # S_AXI 挂 M_AXI_GP0 互连（与 audio_codec_ctrl 同一模式）
    apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
        -config {Master "/ps7/M_AXI_GP0" Clk "Auto"} \
        [get_bd_intf_pins axi_gpio_btns/S_AXI]
    # 按键输入引脚外引，端口名 btn（与 xdc 对应）
    make_bd_pins_external [get_bd_pins axi_gpio_btns/gpio_io_i]
    set_property name btn [lindex [get_bd_ports -quiet gpio_io_i*] 0]
    assign_bd_address
    assign_bd_address -offset 0x43C10000 -range 0x00010000 \
        -target_address_space [get_bd_addr_spaces ps7/Data] \
        [get_bd_addr_segs axi_gpio_btns/S_AXI/Reg] -force
    puts "axi_gpio_btns @ 0x43C10000，端口 btn[3:0]"
}

# 约束：BTN0-3 引脚（PYNQ-Z2 part0 核对：D19/D20/L20/L19）
set xdc [file join $root fpga xdc btns_w6.xdc]
if {[file isfile $xdc] && ![llength [get_files -quiet -of_objects [get_filesets constrs_1] btns_w6.xdc]]} {
    add_files -fileset constrs_1 -norecurse $xdc
    puts "btns_w6.xdc 已加入"
}

validate_bd_design
save_bd_design
close_project
puts "=== BTN_GPIO OK"
