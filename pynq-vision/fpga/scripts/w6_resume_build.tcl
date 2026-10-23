# w6_resume_build.tcl - rerun failed OOC IP synths (serial, low mem), then impl+bitgen
set w6_script_dir [file dirname [file normalize [info script]]]
set w6_repo_root [file normalize [file join $w6_script_dir ../..]]
set w6_project_path [file join $w6_repo_root fpga project glove glove.xpr]
source [file join $w6_script_dir vivado_build_common.tcl]
proc logmsg {s} { puts "[clock format [clock seconds] -format %H:%M:%S] $s" }
set start_time [clock seconds]

open_project $w6_project_path
logmsg "project opened"

foreach r {system_axis_register_slice_0_0_synth_1 system_v_axi4s_vid_out_0_0_synth_1} {
    reset_run $r
}
launch_runs system_axis_register_slice_0_0_synth_1 system_v_axi4s_vid_out_0_0_synth_1 -jobs 2
foreach r {system_axis_register_slice_0_0_synth_1 system_v_axi4s_vid_out_0_0_synth_1} {
    wait_on_run $r
    logmsg "$r => [get_property STATUS [get_runs $r]]"
    if {![string match "*Complete*" [get_property STATUS [get_runs $r]]]} { error "$r failed" }
}

reset_run synth_1
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
vivado_build::require_bitstream

set s [get_property STATUS [get_runs impl_1]]
set wns [get_property STATS.WNS [get_runs impl_1]]
logmsg "impl_1 STATUS=$s WNS=$wns"

set outdir [file dirname $w6_project_path]
set impl_dir [get_property DIRECTORY [get_runs impl_1]]
set bit [file join $impl_dir system_wrapper.bit]
set hwh [lindex [concat \
    [glob -nocomplain [file join $outdir glove.gen sources_1 bd system hw_handoff system.hwh]] \
    [glob -nocomplain [file join $outdir glove.srcs sources_1 bd system hw_handoff system.hwh]]] 0]
set dest [file join $w6_repo_root board_validation w6]
file mkdir $dest
file copy -force $bit [file join $dest kws_hdmi.bit]
file copy -force $hwh [file join $dest kws_hdmi.hwh]
logmsg "exported: $dest/kws_hdmi.bit + .hwh"
set mins [expr {([clock seconds] - $start_time) / 60}]
logmsg "==== W6 resume build done, ${mins} min ===="
exit
