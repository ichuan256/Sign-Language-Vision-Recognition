# Both cameras checked. External I/O remains unverified.
# Requires completed impl_1 in the isolated snapshot project; never programs hardware.
if {![info exists evidence]} {error "Set evidence directory before sourcing"}
if {[file exists [file join $evidence ov5640_snapshot.bit]]} {
    error "Refusing to overwrite existing firmware evidence; select a new evidence directory"
}
file mkdir $evidence
source [file join [file dirname [info script]] ov5640_snapshot_provenance.tcl]
snapshot_provenance check [get_property DIRECTORY [current_project]]
set repo [file normalize [file join [file dirname [info script]] ../../..]]
exec python -I [file join $repo project/scripts/ov5640/snapshot_io_timing.py] [file join $repo project/fpga/constraints/ov5640_snapshot_io.json] --status [file join $evidence external_io_status.json]
foreach synth_run [get_runs -filter {IS_SYNTHESIS == 1}] {
    set synth_log [file join [get_property DIRECTORY $synth_run] runme.log]
    if {[file exists $synth_log]} {
        set f [open $synth_log r]; set synth_text [read $f]; close $f
        if {[regexp {CRITICAL WARNING:.*Synth 8-5799} $synth_text]} {
            error "Tristate converted to logic in $synth_log"
        }
    }
}
source [file join [file dirname [info script]] ov5640_snapshot_stereo_sccb_gate.tcl]
set sccb_result [snapshot_check_sccb]
set sccb_file [open [file join $evidence sccb_structure.txt] w]
puts $sccb_file $sccb_result
close $sccb_file
report_timing_summary -report_unconstrained -file [file join $evidence timing_routed.rpt]
report_cdc -details -file [file join $evidence cdc.rpt]
report_drc -file [file join $evidence drc.rpt]
report_route_status -file [file join $evidence route_status.rpt]
report_utilization -file [file join $evidence utilization.rpt]
report_methodology -file [file join $evidence methodology.rpt]
set f [open [file join $evidence methodology.rpt]]; set method_text [read $f]; close $f
if {[regexp {LUT cell system_i/(camera|camera_right)/[^\n]*drives asynchronous} $method_text]} {error "Camera LUT-driven asynchronous reset remains"}
set f [open [file join $evidence drc.rpt]]; set drc_text [read $f]; close $f
if {[regexp {RAMB[0-9A-Z]* system_i/(camera|camera_right)/[^\n]*active asychronous} $drc_text]} {error "Camera BRAM asynchronous control remains"}
report_bus_skew -file [file join $evidence bus_skew.rpt]
set setup [get_timing_paths -max_paths 1]
set hold [get_timing_paths -delay_type min -max_paths 1]
if {[llength $setup]!=1 || [get_property SLACK $setup]<0} {error "Negative/absent setup timing"}
if {[llength $hold]!=1 || [get_property SLACK $hold]<0} {error "Negative/absent hold timing"}
foreach name {timing_routed cdc drc route_status bus_skew} {
    set f [open [file join $evidence $name.rpt] r];set text [read $f];close $f
    if {$name eq "cdc" && [regexp {Critical} $text]} {error "Unresolved critical CDC"}
    if {$name eq "drc" && [regexp {Error} $text]} {error "DRC error"}
    if {$name eq "route_status" && ![regexp {# of nets with routing errors[. ]+:[ ]+0} $text]} {error "Routing errors or missing route result"}
    if {$name eq "bus_skew" && [string first {Slack (VIOLATED)} $text]>=0} {error "FIFO pointer bus skew failed"}
    if {$name eq "timing_routed"} {
        foreach check {no_clock unconstrained_internal_endpoints} {
            if {[string first [format {checking %s (0)} $check] $text]<0} {error "Unconstrained internal timing"}
        }
    }
}
# write_bitstream also runs its built-in DRC, with original severities preserved.
write_checkpoint -force [file join $evidence routed.dcp]
write_bitstream -force [file join $evidence ov5640_snapshot.bit]
set project_dir [get_property DIRECTORY [current_project]]
file copy -force [file join $project_dir snapshot.gen/sources_1/bd/system/hw_handoff/system.hwh] [file join $evidence ov5640_snapshot.hwh]
set f [open [file join $evidence build_result.tcl] w]
puts $f [list set snapshot_wns [get_property SLACK $setup]]
puts $f [list set snapshot_whs [get_property SLACK $hold]]
puts $f {set snapshot_build_complete 1}
puts $f {set snapshot_sccb_structure_pass 1}
close $f
snapshot_provenance seal [get_property DIRECTORY [current_project]] $evidence
puts "SNAPSHOT_BUILD_COMPLETE"
