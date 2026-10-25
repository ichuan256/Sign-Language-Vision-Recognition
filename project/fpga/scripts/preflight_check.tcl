# preflight_check.tcl —— 移植工程开箱体检（只读，不改工程）
# 用法: vivado -mode batch -source preflight_check.tcl
set d [file dirname [file normalize [info script]]]
set proj [file join $d .. project glove glove.xpr]
open_project $proj
puts "=== 工程已打开: [get_property PART [current_project]]"
puts "=== ip_repo_paths: [get_property ip_repo_paths [current_project]]"
set bd [get_files -quiet */system.bd]
puts "=== BD: $bd"
open_bd_design $bd
foreach pat {*audio_codec_ctrl* *rgb2dvi* *axi_dynclk* *color_convert* *pixel_unpack*} {
    puts "=== cells $pat : [llength [get_bd_cells -quiet $pat]]"
}
set slice [get_bd_cells -quiet video/hdmi_out/axis_register_slice_0]
if {[llength $slice]} {
    puts "=== SOF slice TUSER_WIDTH = [get_property CONFIG.TUSER_WIDTH $slice]"
} else {
    puts "=== SOF slice 不存在"
}
puts "=== 约束文件: [get_files -of_objects [get_filesets constrs_1]]"
close_project
puts "=== PREFLIGHT OK"
