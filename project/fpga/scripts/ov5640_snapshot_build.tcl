# Native batch fallback: argv = existing XPR, report output. Never programs hardware.
if {[llength $argv]!=2} {error "Expected project and evidence directory"}
set xpr [lindex $argv 0]
set evidence [file normalize [lindex $argv 1]]
file mkdir $evidence
set_param general.maxThreads 2
open_project $xpr
source [file join [file dirname [info script]] ov5640_snapshot_provenance.tcl]
snapshot_provenance check [get_property DIRECTORY [current_project]]
if {[get_property PART [current_project]] ne "xc7z020clg400-1"} {error "Wrong part"}
foreach r [get_runs *_synth_1] {
    if {[get_property PROGRESS $r] ne "100%"} {reset_run $r}
}
if {[get_property STATUS [get_runs synth_1]] ne "synth_design Complete!"} {
    reset_run synth_1
    launch_runs synth_1 -jobs 1
    wait_on_run synth_1
}
if {[get_property STATUS [get_runs synth_1]] ne "synth_design Complete!"} {error "Snapshot synthesis failed"}
reset_run impl_1
launch_runs impl_1 -to_step route_design -jobs 1
wait_on_run impl_1
if {[get_property STATUS [get_runs impl_1]] ne "route_design Complete!"} {error "Snapshot implementation failed"}
open_run impl_1
source [file join [file dirname [info script]] ov5640_snapshot_emit.tcl]
close_project
exit
