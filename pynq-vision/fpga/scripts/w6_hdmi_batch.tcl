set w6_script_dir [file dirname [file normalize [info script]]]
set w6_repo_root [file normalize [file join $w6_script_dir ../..]]
open_project [file join $w6_repo_root fpga project glove glove.xpr]
open_bd_design [get_files */system.bd]
source [file join $w6_script_dir w6_hdmi_bd.tcl]
puts "BATCH_DONE_OK"
