# Independent module verification project. Does not edit W6 or program hardware.
set vp_root [file normalize [file join [file dirname [info script]] ../../..]]
if {[current_project -quiet] ne ""} {error "Use an idle Vivado session"}
if {![info exists vp_project_dir]} {
    set vp_project_dir [file join $vp_root project/_tmp/vision_preprocess_20261028]
}
set vp_project_dir [file normalize $vp_project_dir]
if {![string match "${vp_root}/project/_tmp/*" $vp_project_dir]} {error "Keep project in project/_tmp"}
if {[file exists [file join $vp_project_dir vision_preprocess.xpr]]} {error "Use a new project directory"}
create_project vision_preprocess $vp_project_dir -part xc7z020clg400-1
set_property target_language Verilog [current_project]
set_property target_simulator XSim [current_project]
set_param general.maxThreads 2
set vp_rtl_files [list \
    [file join $vp_root project/fpga/rtl/vision_preprocess/vision_preprocess_axi.v] \
    [file join $vp_root project/fpga/rtl/vision_preprocess/vision_rgb565_affine.v] \
    [file join $vp_root project/fpga/rtl/vision_preprocess/rgb888_axis_pack32.v]]
set vp_tb_files [list \
    [file join $vp_root project/fpga/tb/vision_preprocess/tb_vision_preprocess_axi.sv] \
    [file join $vp_root project/fpga/tb/vision_preprocess/tb_vision_rgb565_affine.sv] \
    [file join $vp_root project/fpga/tb/vision_preprocess/tb_rgb888_axis_pack32.sv]]
foreach vp_source [concat $vp_rtl_files $vp_tb_files] {
    if {![file isfile $vp_source]} {error "Required verification source is missing: $vp_source"}
}
add_files -norecurse $vp_rtl_files
add_files -fileset sim_1 -norecurse $vp_tb_files
set_property top vision_preprocess_axi [get_filesets sources_1]
set_property top tb_vision_rgb565_affine [get_filesets sim_1]
set_property xsim.simulate.runtime 600ms [get_filesets sim_1]
set_property xsim.simulate.log_all_signals false [get_filesets sim_1]
if {![info exists vp_vectors]} {
    set vp_vectors [file join $vp_root project/_tmp/vision_preprocess_vectors_20261028]
}
set vp_vectors [file normalize $vp_vectors]
if {![file exists [file join $vp_vectors case_count.mem]]} {error "Generate the independent vectors first"}
set_property -dict [list xsim.simulate.xsim.more_options [list -testplusarg VECTORS=$vp_vectors]] [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
puts "VISION_PREPROCESS_PREPARED $vp_project_dir"
