# w6_hdmi_build.tcl - full build for unified BD with HDMI output
# Adds hdmi_w6.xdc, regenerates BD outputs, synth/impl/bitstream, exports kws_hdmi.bit/.hwh
set w6_script_dir [file dirname [file normalize [info script]]]
set w6_repo_root [file normalize [file join $w6_script_dir ../..]]
set w6_project_path [file join $w6_repo_root fpga project glove glove.xpr]
set w6_jobs 8
source [file join $w6_script_dir vivado_build_common.tcl]
set start_time [clock seconds]
proc logmsg {s} { puts "[clock format [clock seconds] -format %H:%M:%S] $s" }

open_project $w6_project_path
logmsg "project opened"
source [file join $w6_script_dir w6_timing_prepare.tcl]

# HDMI pin constraints
set xdc [file join $w6_repo_root fpga xdc hdmi_w6.xdc]
if {[file isfile $xdc]} {
    if {![llength [get_files -quiet -of_objects [get_filesets constrs_1] hdmi_w6.xdc]]} {
        add_files -fileset constrs_1 -norecurse $xdc
        logmsg "hdmi_w6.xdc added"
    } else {
        logmsg "hdmi_w6.xdc already in project"
    }
} else {
    error "missing $xdc"
}

set bdfile [get_files */system.bd]
open_bd_design $bdfile
# Refuse a stale/pre-fix BD before spending time on implementation.
set sof_slice [get_bd_cells -quiet video/hdmi_out/axis_register_slice_0]
if {[llength $sof_slice] != 1 || [get_property CONFIG.TUSER_WIDTH $sof_slice] != 1} {
    error "HDMI SOF path is disabled. Source w6_hdmi_bd.tcl before rebuilding."
}
generate_target all $bdfile
source [file join $w6_script_dir w6_timing_ip_constraints.tcl]
set w6_sof_netlist [file join $w6_repo_root fpga project glove glove.gen sources_1 bd system synth system.v]
source [file join $w6_script_dir w6_check_sof.tcl]
logmsg "BD outputs generated"

# 2026-10-17 fix: drop stale imported wrapper (Sep-22 imports/hdl copy has no
# hdmi/audio ports; it shadowed the generated one so XDC found no ports)
set stale [get_files -quiet -of_objects [get_filesets sources_1] {*/imports/hdl/system_wrapper.v}]
if {[llength $stale]} {
    remove_files -fileset sources_1 $stale
    logmsg "removed stale wrapper: $stale"
}

set wrapper [make_wrapper -files [get_files $bdfile] -top]
if {[lsearch [get_files] $wrapper] < 0} { add_files -norecurse $wrapper }
set_property top system_wrapper [current_fileset]
update_compile_order -fileset sources_1
# verify the regenerated wrapper actually carries the new ports
set wchan [open $wrapper r]
set wtext [read $wchan]
close $wchan
if {[regexp {spia_|spib_} $wtext]} {
    error "Pmod SPI ports remain in wrapper: $wrapper"
}
foreach pat {hdmi_out hdmi_out_hpd bclk sdata_i} {
    if {![string match "*$pat*" $wtext]} {
        error "wrapper still missing port: $pat ($wrapper)"
    }
}
logmsg "wrapper ready (ports verified: hdmi_out/bclk/sdata_i present)"

reset_run synth_1
launch_runs impl_1 -to_step write_bitstream -jobs $w6_jobs
wait_on_run impl_1
vivado_build::require_bitstream

set s [get_property STATUS [get_runs impl_1]]
set wns [get_property STATS.WNS [get_runs impl_1]]
logmsg "impl_1 STATUS=$s WNS=$wns"
set outdir [file dirname $w6_project_path]
open_run impl_1
report_utilization -file [file join $outdir w6_hdmi_utilization.rpt]
report_timing_summary -file [file join $outdir w6_hdmi_timing.rpt]
set auditdir [file join $w6_repo_root analysis timing_20261018]
file mkdir $auditdir
report_methodology -file [file join $auditdir methodology_routed.rpt]
check_timing -verbose -file [file join $auditdir check_timing.rpt]
report_clocks -file [file join $auditdir clocks.rpt]
report_clock_interaction -file [file join $auditdir clock_interaction.rpt]
report_exceptions -file [file join $auditdir exceptions.rpt]
report_bus_skew -file [file join $auditdir bus_skew.rpt]
report_timing -delay_type min_max -from [get_ports sdata_i] \
    -max_paths 12 -file [file join $auditdir input_timing.rpt]
set mf [open [file join $auditdir methodology_routed.rpt] r]
set methodology [read $mf]
close $mf
if {[regexp {TIMING-(4|27|36)#[0-9]} $methodology]} {
    error "Clock methodology gate failed: see $auditdir/methodology_routed.rpt"
}
foreach delay {max min} {
    set paths [get_timing_paths -quiet -delay_type $delay -max_paths 1]
    if {![llength $paths] || [get_property SLACK $paths] < 0} {
        error "Timing $delay gate failed; do not promote this build."
    }
}

# export paired bit/hwh as kws_hdmi
set impl_dir [get_property DIRECTORY [get_runs impl_1]]
set bit [file join $impl_dir system_wrapper.bit]
set hwh [lindex [concat \
    [glob -nocomplain [file join $outdir glove.gen sources_1 bd system hw_handoff system.hwh]] \
    [glob -nocomplain [file join $outdir glove.srcs sources_1 bd system hw_handoff system.hwh]]] 0]
set dest [file join $w6_repo_root board_validation w6 timing_candidate]
file mkdir $dest
file copy -force $bit [file join $dest kws_hdmi.bit]
file copy -force $hwh [file join $dest kws_hdmi.hwh]
logmsg "exported: $dest/kws_hdmi.bit + .hwh"

set mins [expr {([clock seconds] - $start_time) / 60}]
logmsg "==== W6 HDMI build done, ${mins} min ===="
exit
