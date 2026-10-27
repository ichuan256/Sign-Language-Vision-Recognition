# Independent snapshot test project. No W6 mutation or programming.
set snapshot_repo [file normalize [file join [file dirname [info script]] ../../..]]
set snapshot_out [file join $snapshot_repo project/_tmp/ov5640_snapshot_20261027]
if {[current_project -quiet] ne ""} {error "Close prior project first"}
set snapshot_base $snapshot_out
set snapshot_version 1
while {[file exists [file join $snapshot_out vivado/snapshot.xpr]]} {
    incr snapshot_version
    set snapshot_out ${snapshot_base}_v${snapshot_version}
}
file mkdir $snapshot_out
set_param general.maxThreads 2
create_project snapshot [file join $snapshot_out vivado] -part xc7z020clg400-1
set_property target_language Verilog [current_project]
set_property XPM_LIBRARIES {XPM_FIFO} [current_project]
add_files -norecurse [glob [file join $snapshot_repo project/fpga/rtl/ov5640_stereo/*.v]]
add_files -norecurse [glob [file join $snapshot_repo project/fpga/rtl/ov5640_snapshot/*.v]]
update_compile_order -fileset sources_1
create_bd_design system
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7
source [file join $snapshot_repo project/analysis/ov5640_snapshot_20261027/ps_config.tcl]
set_property -dict $snapshot_ps_config [get_bd_cells ps7]
make_bd_intf_pins_external [get_bd_intf_pins ps7/DDR] [get_bd_intf_pins ps7/FIXED_IO]
set_property name DDR [get_bd_intf_ports DDR_0]
set_property name FIXED_IO [get_bd_intf_ports FIXED_IO_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 rst_sys
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 one
set_property CONFIG.CONST_VAL 1 [get_bd_cells one]
connect_bd_net [get_bd_pins one/dout] [get_bd_pins rst_sys/dcm_locked]
connect_bd_net [get_bd_pins ps7/FCLK_RESET0_N] [get_bd_pins rst_sys/ext_reset_in]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 control_bus
set_property -dict {CONFIG.NUM_SI 1 CONFIG.NUM_MI 2} [get_bd_cells control_bus]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 capture_memory
set_property -dict {CONFIG.NUM_SI 1 CONFIG.NUM_MI 1} [get_bd_cells capture_memory]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1 capture_dma
set_property -dict {CONFIG.c_include_sg 0 CONFIG.c_include_mm2s 0 CONFIG.c_include_s2mm 1 CONFIG.c_sg_length_width 23 CONFIG.c_m_axi_s2mm_data_width 64 CONFIG.c_s_axis_s2mm_tdata_width 32 CONFIG.c_s2mm_burst_size 16 CONFIG.c_include_s2mm_dre 0} [get_bd_cells capture_dma]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 camera_control
set_property -dict {CONFIG.C_GPIO_WIDTH 3 CONFIG.C_ALL_OUTPUTS 1 CONFIG.C_IS_DUAL 1 CONFIG.C_GPIO2_WIDTH 32 CONFIG.C_ALL_INPUTS_2 1 CONFIG.C_DOUT_DEFAULT 0x00000000} [get_bd_cells camera_control]
create_bd_cell -type module -reference ov5640_snapshot camera
connect_bd_intf_net [get_bd_intf_pins ps7/M_AXI_GP0] [get_bd_intf_pins control_bus/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins control_bus/M00_AXI] [get_bd_intf_pins capture_dma/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins control_bus/M01_AXI] [get_bd_intf_pins camera_control/S_AXI]
connect_bd_intf_net [get_bd_intf_pins camera/M_AXIS] [get_bd_intf_pins capture_dma/S_AXIS_S2MM]
connect_bd_intf_net [get_bd_intf_pins capture_dma/M_AXI_S2MM] [get_bd_intf_pins capture_memory/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins capture_memory/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP0]
connect_bd_net [get_bd_pins camera_control/gpio_io_o] [get_bd_pins camera/control]
connect_bd_net [get_bd_pins camera/status] [get_bd_pins camera_control/gpio2_io_i]
set clk [get_bd_pins ps7/FCLK_CLK0]
connect_bd_net $clk [get_bd_pins ps7/M_AXI_GP0_ACLK] [get_bd_pins ps7/S_AXI_HP0_ACLK] [get_bd_pins rst_sys/slowest_sync_clk] [get_bd_pins camera/sys_clk]
connect_bd_net [get_bd_pins rst_sys/peripheral_aresetn] [get_bd_pins camera/sys_reset_n]
foreach cell {control_bus capture_memory capture_dma camera_control} {
    foreach p [get_bd_pins -of_objects [get_bd_cells $cell] -filter {TYPE == clk && DIR == I}] {
        if {[llength [get_bd_nets -quiet -of_objects $p]]==0} {connect_bd_net $clk $p}
    }
    foreach p [get_bd_pins -of_objects [get_bd_cells $cell] -filter {TYPE == rst && DIR == I}] {
        if {[llength [get_bd_nets -quiet -of_objects $p]]==0} {connect_bd_net [get_bd_pins rst_sys/peripheral_aresetn] $p}
    }
}
foreach name {ov1_pclk ov1_vsync ov1_href ov1_data ov1_scl ov1_sda ov1_reset_n ov1_pwdn ov2_pclk ov2_vsync ov2_href ov2_data ov2_scl ov2_sda ov2_reset_n ov2_pwdn} {
    make_bd_pins_external [get_bd_pins camera/$name]
    set_property name $name [get_bd_ports [format {%s_0} $name]]
}
assign_bd_address -offset 0x40400000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs capture_dma/S_AXI_LITE/Reg]
assign_bd_address -offset 0x41200000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs camera_control/S_AXI/Reg]
assign_bd_address -offset 0 -range 512M -target_address_space [get_bd_addr_spaces capture_dma/Data_S2MM] [get_bd_addr_segs ps7/S_AXI_HP0/HP0_DDR_LOWOCM]
validate_bd_design
save_bd_design
write_bd_tcl -force [file join $snapshot_out system.tcl]
set bd [get_files */system.bd]
generate_target all $bd
set wrapper [make_wrapper -files $bd -top]
add_files -norecurse $wrapper
set_property top system_wrapper [get_filesets sources_1]
update_compile_order -fileset sources_1
set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY none [get_runs synth_1]
set_property STEPS.OPT_DESIGN.TCL.PRE [file join $snapshot_repo project/fpga/scripts/ov5640_snapshot_constraints.tcl] [get_runs impl_1]
puts "SNAPSHOT_PREPARED $snapshot_out"
