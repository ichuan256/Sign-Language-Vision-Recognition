# Fresh native BD creation. Target generation is a separate Vivado process.
set no_audio_scripts [file dirname [file normalize [info script]]]
set snapshot_out [file normalize [file join $no_audio_scripts ../../_tmp/ov1_hdmi_no_audio_20261101]]
set snapshot_bd_extension [file join $no_audio_scripts ov5640_snapshot_hdmi_no_audio_bd.tcl]
set snapshot_post_generate_extension [file join $no_audio_scripts w6_timing_ip_constraints.tcl]
set f [open [file join $no_audio_scripts ov5640_snapshot_prepare.tcl] r]
set prepare_source [read $f]
close $f
set boundary [string first "\ngenerate_target all \$bd\n" $prepare_source]
if {$boundary<0} {error "Preparation boundary changed"}
eval [string range $prepare_source 0 $boundary]
puts "HDMI_NO_AUDIO_BD_READY [get_property DIRECTORY [current_project]]"
close_project
exit
