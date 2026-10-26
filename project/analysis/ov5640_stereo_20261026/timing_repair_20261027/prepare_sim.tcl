set evidence [file normalize [file dirname [info script]]]
set root [file normalize [file join $evidence ../../../..]]
if {[current_project -quiet] ne ""} {error "Close prior project first"}
create_project startup [file join $evidence xsim_project] -part xc7z020clg400-1
set_property target_simulator XSim [current_project]
add_files [glob [file join $root project/fpga/rtl/ov5640_stereo/*.v]]
add_files -fileset sim_1 [glob [file join $root project/fpga/tb/ov5640_stereo/*.v]]
set_property top ov5640_stereo_startup_capture [get_filesets sources_1]
set_property top tb_ov5640_delay_conversion [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
cd $evidence
set startup_tops {tb_ov5640_delay_conversion tb_ov5640_sccb_register_access tb_ov5640_startup_defaults tb_ov5640_startup_controller tb_ov5640_stereo_startup tb_ov5640_startup_capture tb_ov5640_dvp_capture tb_ov5640_stereo_capture_pair tb_ov5640_720p_frame}
