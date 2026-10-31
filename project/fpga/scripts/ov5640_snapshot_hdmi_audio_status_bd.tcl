# Diagnostic-only addition to the existing AV design. No functional video,
# camera, audio, model, or external-pin wiring changes.
set av_status_scripts [file dirname [file normalize [info script]]]
source [file join $av_status_scripts ov5640_snapshot_hdmi_audio_bd.tcl]
current_bd_instance /
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 video_status_gpio
set_property -dict {CONFIG.C_IS_DUAL 1 CONFIG.C_GPIO_WIDTH 32 CONFIG.C_ALL_INPUTS 1 CONFIG.C_GPIO2_WIDTH 8 CONFIG.C_ALL_INPUTS_2 1 CONFIG.C_INTERRUPT_PRESENT 0} [get_bd_cells video_status_gpio]
set_property CONFIG.NUM_MI 5 [get_bd_cells control_bus]
connect_bd_intf_net [get_bd_intf_pins control_bus/M04_AXI] [get_bd_intf_pins video_status_gpio/S_AXI]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins control_bus/M04_ACLK] [get_bd_pins video_status_gpio/s_axi_aclk]
connect_bd_net [get_bd_pins rst_sys/peripheral_aresetn] [get_bd_pins control_bus/M04_ARESETN] [get_bd_pins video_status_gpio/s_axi_aresetn]
assign_bd_address -offset 0x41210000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs video_status_gpio/S_AXI/Reg]
# Official XPM IPI parameters were queried in the local 2024.1 catalog first.
# Independent bit synchronizers: observational only, not a coherent bus or
# cycle-accurate waveform. Read repeated stable states when interpreting it.
foreach {name width input_reg} {video_status_cdc 32 true video_flags_cdc 8 false} {
    create_bd_cell -type ip -vlnv xilinx.com:ip:xpm_cdc_gen:1.0 $name
    set_property -dict [list CONFIG.CDC_TYPE xpm_cdc_array_single CONFIG.WIDTH $width CONFIG.DEST_SYNC_FF 4 CONFIG.SRC_INPUT_REG $input_reg CONFIG.SRC_CLK_PERIOD 10000 CONFIG.DEST_CLK_PERIOD 10000] [get_bd_cells $name]
    connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins $name/dest_clk]
    set source_clock [get_bd_pins -quiet $name/src_clk]
    if {[llength $source_clock]} {connect_bd_net [get_bd_pins video/hdmi_out/frontend/axi_dynclk/PXL_CLK_O] $source_clock}
}
connect_bd_net [get_bd_pins video/hdmi_out/frontend/v_axi4s_vid_out_0/status] [get_bd_pins video_status_cdc/src_in]
connect_bd_net [get_bd_pins video_status_cdc/dest_out] [get_bd_pins video_status_gpio/gpio_io_i]
# The output core also synchronizes locked internally. Register the diagnostic
# tap in the source domain so it does not create a second direct CDC fan-out
# from the original locked flop (CDC-11). This is observational only.
create_bd_cell -type ip -vlnv xilinx.com:ip:xpm_cdc_gen:1.0 video_locked_cdc
set_property -dict {CONFIG.CDC_TYPE xpm_cdc_array_single CONFIG.WIDTH 1 CONFIG.DEST_SYNC_FF 4 CONFIG.SRC_INPUT_REG true CONFIG.SRC_CLK_PERIOD 10000 CONFIG.DEST_CLK_PERIOD 10000} [get_bd_cells video_locked_cdc]
connect_bd_net [get_bd_pins video/hdmi_out/frontend/axi_dynclk/PXL_CLK_O] [get_bd_pins video_locked_cdc/src_clk]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins video_locked_cdc/dest_clk]
connect_bd_net [get_bd_pins video/hdmi_out/frontend/v_axi4s_vid_out_0/locked] [get_bd_pins video_locked_cdc/src_in]
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 video_flags_concat
set_property CONFIG.NUM_PORTS 8 [get_bd_cells video_flags_concat]
set flag_sources {
    video/hdmi_out/frontend/axi_dynclk/LOCKED_O
    video_locked_cdc/dest_out
    video/hdmi_out/frontend/v_axi4s_vid_out_0/underflow
    video/hdmi_out/frontend/v_axi4s_vid_out_0/overflow
    video/hdmi_out/frontend/v_axi4s_vid_out_0/sof_state_out
    video/hdmi_out/frontend/v_axi4s_vid_out_0/vtg_ce
    video/hdmi_out/frontend/hdmi_out_hpd_video/gpio_io_o
    rst_sys/peripheral_aresetn
}
set index 0
foreach source $flag_sources {
    connect_bd_net [get_bd_pins $source] [get_bd_pins video_flags_concat/In$index]
    incr index
}
connect_bd_net [get_bd_pins video_flags_concat/dout] [get_bd_pins video_flags_cdc/src_in]
connect_bd_net [get_bd_pins video_flags_cdc/dest_out] [get_bd_pins video_status_gpio/gpio2_io_i]
validate_bd_design
puts "AV_STATUS_DIAGNOSTIC GPIO=0x41210000 status=offset0 flags=offset8 CDC=4FF observational_only"
