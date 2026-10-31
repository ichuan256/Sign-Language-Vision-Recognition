set av_scripts [file dirname [file normalize [info script]]]
set snapshot_out [file normalize [file join $av_scripts ../../_tmp/ov1_hdmi_audio_20261031]]
set snapshot_bd_extension [file join $av_scripts ov5640_snapshot_hdmi_audio_bd.tcl]
set snapshot_post_generate_extension [file join $av_scripts w6_timing_ip_constraints.tcl]
source [file join $av_scripts ov5640_snapshot_prepare.tcl]
puts "AV_PROJECT_READY [get_property DIRECTORY [current_project]]"
close_project
exit
