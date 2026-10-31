set scripts [file dirname [file normalize [info script]]]
set snapshot_out [file normalize [file join $scripts ../../_tmp/ov5640_stereo_20261031]]
set snapshot_bd_extension [file join $scripts ov5640_snapshot_stereo_bd.tcl]
source [file join $scripts ov5640_snapshot_prepare.tcl]
set_property STEPS.OPT_DESIGN.TCL.PRE [file join $scripts ov5640_snapshot_stereo_constraints.tcl] [get_runs impl_1]
puts "STEREO_PROJECT_READY [get_property DIRECTORY [current_project]]"
close_project
exit
