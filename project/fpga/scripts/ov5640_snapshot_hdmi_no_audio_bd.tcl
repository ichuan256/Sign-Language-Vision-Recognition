# Regression isolation: same camera/video/HPD diagnostics, no audio hardware.
# Only used by a fresh project; does not modify any deployed package.
set no_audio_scripts [file dirname [file normalize [info script]]]
source [file join $no_audio_scripts ov5640_snapshot_hdmi_audio_hpd_bd.tcl]
current_bd_instance /
set diagnostic_bus [get_bd_intf_nets -of_objects [get_bd_intf_pins video_status_gpio/S_AXI]]
disconnect_bd_intf_net $diagnostic_bus [get_bd_intf_pins video_status_gpio/S_AXI]
delete_bd_objs [get_bd_cells audio_codec_ctrl_0] [get_bd_cells clk_wiz_audio]
set iic_net [get_bd_intf_nets -of_objects [get_bd_intf_ports IIC_1]]
delete_bd_objs $iic_net [get_bd_intf_ports IIC_1]
foreach name {audio_clk_10MHz bclk lrclk sdata_o sdata_i codec_addr} {
    delete_bd_objs [get_bd_ports $name]
}
set_property -dict {CONFIG.PCW_EN_I2C1 0 CONFIG.PCW_EN_EMIO_I2C1 0 CONFIG.PCW_I2C1_PERIPHERAL_ENABLE 0} [get_bd_cells ps7]
set_property CONFIG.NUM_MI 4 [get_bd_cells control_bus]
connect_bd_intf_net [get_bd_intf_pins control_bus/M03_AXI] [get_bd_intf_pins video_status_gpio/S_AXI]
remove_files [get_files */audio_w6.xdc]
validate_bd_design
if {[llength [get_bd_cells -quiet audio_codec_ctrl_0]] || [llength [get_bd_cells -quiet clk_wiz_audio]]} {error "Audio removal incomplete"}
if {[get_property DIR [get_bd_ports hdmi_out_hpd]] ne "I"} {error "HPD must remain input"}
puts "HDMI_NO_AUDIO_DIAGNOSTIC camera/video unchanged; HPD=input; status=0x41210000; no audio IP or MCLK"
