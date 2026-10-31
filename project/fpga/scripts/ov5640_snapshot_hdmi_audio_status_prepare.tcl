set av_status_scripts [file dirname [file normalize [info script]]]
if {![info exists snapshot_out]} {set snapshot_out [file normalize [file join $av_status_scripts ../../_tmp/ov1_av_status_20261031]]}
if {![info exists snapshot_bd_extension]} {set snapshot_bd_extension [file join $av_status_scripts ov5640_snapshot_hdmi_audio_status_bd.tcl]}
set snapshot_post_generate_extension [file join $av_status_scripts ov5640_snapshot_hdmi_audio_status_cache.tcl]
# First create/save the BD, then generate it in a fresh Vivado process. Native
# 2024.1 crashed twice when target generation followed catalog rebuild in the
# creating process; reopening the unchanged project completed successfully.
set f [open [file join $av_status_scripts ov5640_snapshot_prepare.tcl] r]
set prepare_source [read $f]
close $f
set boundary [string first "\ngenerate_target all \$bd\n" $prepare_source]
if {$boundary<0} {error "Snapshot preparation boundary changed; inspect before proceeding"}
eval [string range $prepare_source 0 $boundary]
puts "AV_STATUS_BD_READY [get_property DIRECTORY [current_project]]"
close_project
exit
