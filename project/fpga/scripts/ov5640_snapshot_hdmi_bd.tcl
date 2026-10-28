# Extension called by snapshot_prepare before validation/target generation.
# Capture keeps HP0; the standard PYNQ output-only video hierarchy reads HP2.
set snapshot_hdmi_scripts [file dirname [file normalize [info script]]]
# Interface definitions are registered explicitly, as in the W6 XPR.
set snapshot_hdmi_if_repo [file normalize [file join $snapshot_hdmi_scripts ../ip_repo/if]]
set_property ip_repo_paths [concat [get_property ip_repo_paths [current_project]] \
    [list $snapshot_hdmi_if_repo]] [current_project]
set ::w6h_procedures_only 1
try {
    source [file join $snapshot_hdmi_scripts w6_hdmi_bd.tcl]
} finally {
    unset ::w6h_procedures_only
}
current_bd_instance /
if {[llength [get_bd_cells -quiet video]]} {error "HDMI extension requires a fresh snapshot BD"}
set_property -dict {
    CONFIG.PCW_USE_S_AXI_HP2 1
    CONFIG.PCW_S_AXI_HP2_DATA_WIDTH 64
    CONFIG.PCW_USE_FABRIC_INTERRUPT 1
    CONFIG.PCW_IRQ_F2P_INTR 1
} [get_bd_cells ps7]
w6h_create_video / video
# The old name clk_142M is preserved for driver/hierarchy compatibility. Both
# AXI domains use FCLK0=100 MHz, as in the working W6 post-patch design.
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] \
    [get_bd_pins video/clk_100M] [get_bd_pins video/clk_142M] \
    [get_bd_pins ps7/S_AXI_HP2_ACLK]
connect_bd_net [get_bd_pins rst_sys/peripheral_aresetn] \
    [get_bd_pins video/periph_resetn_clk100M] [get_bd_pins video/periph_resetn_clk142M]
connect_bd_net [get_bd_pins rst_sys/interconnect_aresetn] \
    [get_bd_pins video/ic_resetn_clk100M] [get_bd_pins video/ic_resetn_clk142M]
set_property CONFIG.TUSER_WIDTH 1 [get_bd_cells video/hdmi_out/axis_register_slice_0]
set_property CONFIG.NUM_MI 3 [get_bd_cells control_bus]
connect_bd_intf_net [get_bd_intf_pins control_bus/M02_AXI] [get_bd_intf_pins video/S_AXI]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins control_bus/M02_ACLK]
connect_bd_net [get_bd_pins rst_sys/peripheral_aresetn] [get_bd_pins control_bus/M02_ARESETN]
connect_bd_intf_net [get_bd_intf_pins video/M_AXI] [get_bd_intf_pins ps7/S_AXI_HP2]
# Preserve interrupt connectivity in the HWH metadata for pynq.lib.video.
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlconcat_irq
set_property CONFIG.NUM_PORTS 1 [get_bd_cells xlconcat_irq]
connect_bd_net [get_bd_pins video/video_irq] [get_bd_pins xlconcat_irq/In0]
connect_bd_net [get_bd_pins xlconcat_irq/dout] [get_bd_pins ps7/IRQ_F2P]
create_bd_intf_port -mode Master -vlnv digilentinc.com:interface:tmds_rtl:1.0 hdmi_out
connect_bd_intf_net [get_bd_intf_ports hdmi_out] [get_bd_intf_pins video/TMDS_out]
create_bd_port -dir O -from 0 -to 0 hdmi_out_hpd
connect_bd_net [get_bd_ports hdmi_out_hpd] [get_bd_pins video/hdmi_out_hpd]
# W6-compatible fixed control addresses; camera addresses remain unchanged.
foreach {segment offset} {
    video/axi_vdma/S_AXI_LITE/Reg 0x44A00000
    video/hdmi_out/frontend/axi_dynclk/s00_axi/reg0 0x44A10000
    video/hdmi_out/frontend/vtc_out/ctrl/Reg 0x44A20000
    video/hdmi_out/color_convert/s_axi_control/Reg 0x40010000
    video/hdmi_out/frontend/hdmi_out_hpd_video/S_AXI/Reg 0x40020000
    video/hdmi_out/pixel_unpack/s_axi_control/Reg 0x40030000
} {
    assign_bd_address -offset $offset -range 64K -target_address_space \
        [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs $segment]
}
assign_bd_address -offset 0 -range 512M -target_address_space \
    [get_bd_addr_spaces video/axi_vdma/Data_MM2S] [get_bd_addr_segs ps7/S_AXI_HP2/HP2_DDR_LOWOCM]
set snapshot_hdmi_fpga [file normalize [file join $snapshot_hdmi_scripts ..]]
add_files -fileset constrs_1 -norecurse [file join $snapshot_hdmi_fpga xdc/hdmi_w6.xdc]
set snapshot_hdmi_xdc [file join $snapshot_hdmi_fpga xdc/ov5640_snapshot_hdmi.xdc]
add_files -fileset constrs_1 -norecurse $snapshot_hdmi_xdc
set_property PROCESSING_ORDER LATE [get_files $snapshot_hdmi_xdc]
puts "SNAPSHOT_HDMI_BD_ATTACHED AXI=100MHz capture=HP0 display=HP2"
