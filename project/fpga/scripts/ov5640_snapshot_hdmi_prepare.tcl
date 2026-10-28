# Independent camera + HDMI project. Never open/mutate W6 or program the FPGA.
# Source in an idle Vivado Tcl session. Optional snapshot_out selects a NEW root.
set snapshot_hdmi_scripts [file dirname [file normalize [info script]]]
if {![info exists snapshot_out]} {
    set snapshot_out [file normalize [file join $snapshot_hdmi_scripts ../../_tmp/ov5640_snapshot_hdmi_20261028]]
}
set snapshot_bd_extension [file join $snapshot_hdmi_scripts ov5640_snapshot_hdmi_bd.tcl]
set snapshot_post_generate_extension [file join $snapshot_hdmi_scripts w6_timing_ip_constraints.tcl]
try {
    source [file join $snapshot_hdmi_scripts ov5640_snapshot_prepare.tcl]
} finally {
    unset snapshot_bd_extension snapshot_post_generate_extension
}
puts "SNAPSHOT_HDMI_PREPARED $snapshot_out"
