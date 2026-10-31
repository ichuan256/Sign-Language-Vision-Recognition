# Extend the existing OV1+HDMI BD with the unchanged W6 ADAU1761 interface.
# No RTL/HLS changes, no W6 project mutation, no hardware programming.
set av_scripts [file dirname [file normalize [info script]]]
source [file join $av_scripts ov5640_snapshot_hdmi_bd.tcl]
set av_repo [file normalize [file join $av_scripts .. ip_repo]]
if {![file isfile [file join $av_repo audio_codec_ctrl_v1.0 component.xml]]} {error "Missing validated W6 audio IP"}
set_property ip_repo_paths [lsort -unique [concat [get_property ip_repo_paths [current_project]] $av_repo]] [current_project]
update_ip_catalog -rebuild
if {[llength [get_ipdefs -quiet xilinx.com:user:audio_codec_ctrl:1.0]]!=1} {error "Validated audio VLNV absent"}
# These PS/clock/IP parameters are taken from w6_audio_bd.tcl.
set_property -dict {CONFIG.PCW_EN_I2C1 1 CONFIG.PCW_EN_EMIO_I2C1 1 CONFIG.PCW_I2C1_PERIPHERAL_ENABLE 1} [get_bd_cells ps7]
create_bd_intf_port -mode Master -vlnv xilinx.com:interface:iic_rtl:1.0 IIC_1
connect_bd_intf_net [get_bd_intf_pins ps7/IIC_1] [get_bd_intf_ports IIC_1]
create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz:6.0 clk_wiz_audio
set_property -dict {CONFIG.CLKOUT1_REQUESTED_OUT_FREQ 10.000 CONFIG.PRIM_SOURCE No_buffer CONFIG.RESET_PORT resetn CONFIG.RESET_TYPE ACTIVE_LOW} [get_bd_cells clk_wiz_audio]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins clk_wiz_audio/clk_in1]
connect_bd_net [get_bd_pins rst_sys/peripheral_aresetn] [get_bd_pins clk_wiz_audio/resetn]
create_bd_port -dir O -type clk audio_clk_10MHz
connect_bd_net [get_bd_pins clk_wiz_audio/clk_out1] [get_bd_ports audio_clk_10MHz]
create_bd_cell -type ip -vlnv xilinx.com:user:audio_codec_ctrl:1.0 audio_codec_ctrl_0
set_property CONFIG.NUM_MI 4 [get_bd_cells control_bus]
connect_bd_intf_net [get_bd_intf_pins control_bus/M03_AXI] [get_bd_intf_pins audio_codec_ctrl_0/S_AXI]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins control_bus/M03_ACLK] [get_bd_pins audio_codec_ctrl_0/s_axi_aclk]
connect_bd_net [get_bd_pins rst_sys/peripheral_aresetn] [get_bd_pins control_bus/M03_ARESETN] [get_bd_pins audio_codec_ctrl_0/s_axi_aresetn]
foreach {port direction} {bclk O lrclk O sdata_o O sdata_i I} {
    create_bd_port -dir $direction $port
    connect_bd_net [get_bd_ports $port] [get_bd_pins audio_codec_ctrl_0/$port]
}
create_bd_port -dir O -from 1 -to 0 codec_addr
connect_bd_net [get_bd_ports codec_addr] [get_bd_pins audio_codec_ctrl_0/codec_address]
assign_bd_address -offset 0x43C00000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs audio_codec_ctrl_0/S_AXI/reg0]
add_files -fileset constrs_1 -norecurse [file join $av_scripts .. xdc audio_w6.xdc]
validate_bd_design
puts "OV1_AV_INTEGRATED capture=HP0 HDMI=HP2 audio=0x43C00000 I2C1=EMIO MCLK=10MHz"
