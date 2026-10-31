# Two existing snapshot modules, two independent S2MM DMA paths. No RTL edits.
set_property -dict {CONFIG.NUM_MI 4} [get_bd_cells control_bus]
set_property -dict {CONFIG.NUM_SI 2} [get_bd_cells capture_memory]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1 capture_dma_right
set_property -dict {CONFIG.c_include_sg 0 CONFIG.c_include_mm2s 0 CONFIG.c_include_s2mm 1 CONFIG.c_sg_length_width 23 CONFIG.c_m_axi_s2mm_data_width 64 CONFIG.c_s_axis_s2mm_tdata_width 32 CONFIG.c_s2mm_burst_size 16 CONFIG.c_include_s2mm_dre 0} [get_bd_cells capture_dma_right]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 camera_control_right
set_property -dict {CONFIG.C_GPIO_WIDTH 10 CONFIG.C_ALL_OUTPUTS 1 CONFIG.C_IS_DUAL 1 CONFIG.C_GPIO2_WIDTH 32 CONFIG.C_ALL_INPUTS_2 1 CONFIG.C_DOUT_DEFAULT 0x00000000} [get_bd_cells camera_control_right]
create_bd_cell -type module -reference ov5640_snapshot camera_right
set_property CONFIG.CAMERA 2 [get_bd_cells camera_right]
connect_bd_intf_net [get_bd_intf_pins control_bus/M02_AXI] [get_bd_intf_pins capture_dma_right/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins control_bus/M03_AXI] [get_bd_intf_pins camera_control_right/S_AXI]
connect_bd_intf_net [get_bd_intf_pins camera_right/M_AXIS] [get_bd_intf_pins capture_dma_right/S_AXIS_S2MM]
connect_bd_intf_net [get_bd_intf_pins capture_dma_right/M_AXI_S2MM] [get_bd_intf_pins capture_memory/S01_AXI]
connect_bd_net [get_bd_pins camera_control_right/gpio_io_o] [get_bd_pins camera_right/control]
connect_bd_net [get_bd_pins camera_right/status] [get_bd_pins camera_control_right/gpio2_io_i]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins camera_right/sys_clk]
connect_bd_net [get_bd_pins rst_sys/peripheral_aresetn] [get_bd_pins camera_right/sys_reset_n]
foreach cell {control_bus capture_memory capture_dma_right camera_control_right} {
    foreach p [get_bd_pins -of_objects [get_bd_cells $cell] -filter {TYPE == clk && DIR == I}] {
        if {![llength [get_bd_nets -quiet -of_objects $p]]} {connect_bd_net [get_bd_pins ps7/FCLK_CLK0] $p}
    }
    foreach p [get_bd_pins -of_objects [get_bd_cells $cell] -filter {TYPE == rst && DIR == I}] {
        if {![llength [get_bd_nets -quiet -of_objects $p]]} {connect_bd_net [get_bd_pins rst_sys/peripheral_aresetn] $p}
    }
}
# Move the physical OV2 ports from the inactive side of camera to camera_right.
# Never join two camera output drivers or two SCCB tristate buffers.
foreach name {ov2_pclk ov2_vsync ov2_href ov2_data ov2_scl ov2_sda ov2_reset_n ov2_pwdn} {
    set net [get_bd_nets -of_objects [get_bd_pins camera/$name]]
    disconnect_bd_net $net [get_bd_pins camera/$name]
    connect_bd_net -net $net [get_bd_pins camera_right/$name]
}
# Inactive input ports are tied low; inactive outputs/inouts stay unconnected.
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 camera_zero
set_property CONFIG.CONST_VAL 0 [get_bd_cells camera_zero]
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 camera_zero8
set_property -dict {CONFIG.CONST_VAL 0 CONFIG.CONST_WIDTH 8} [get_bd_cells camera_zero8]
foreach p {camera/ov2_pclk camera/ov2_vsync camera/ov2_href camera_right/ov1_pclk camera_right/ov1_vsync camera_right/ov1_href} {
    connect_bd_net [get_bd_pins camera_zero/dout] [get_bd_pins $p]
}
foreach p {camera/ov2_data camera_right/ov1_data} {connect_bd_net [get_bd_pins camera_zero8/dout] [get_bd_pins $p]}
assign_bd_address -offset 0x40410000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs capture_dma_right/S_AXI_LITE/Reg]
assign_bd_address -offset 0x41210000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs camera_control_right/S_AXI/Reg]
assign_bd_address -offset 0 -range 512M -target_address_space [get_bd_addr_spaces capture_dma_right/Data_S2MM] [get_bd_addr_segs ps7/S_AXI_HP0/HP0_DDR_LOWOCM]
