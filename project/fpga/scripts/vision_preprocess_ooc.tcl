# Independent OOC resource/timing experiment. No board I/O budgets or bitstream.
set vp_root [file normalize [file join [file dirname [info script]] ../../..]]
if {[current_project -quiet] ne ""} {error "Close the simulation project before the OOC experiment"}
if {![info exists vp_ooc_evidence]} {
    set vp_ooc_evidence [file join $vp_root project/analysis/vision_preprocess_20261028/ooc]
}
set vp_ooc_evidence [file normalize $vp_ooc_evidence]
if {[file exists [file join $vp_ooc_evidence routed.dcp]]} {error "Use a new evidence directory"}
file mkdir $vp_ooc_evidence
create_project -in_memory -part xc7z020clg400-1
set_param general.maxThreads 2
set vp_rtl_files [list \
    [file join $vp_root project/fpga/rtl/vision_preprocess/vision_preprocess_axi.v] \
    [file join $vp_root project/fpga/rtl/vision_preprocess/vision_rgb565_affine.v] \
    [file join $vp_root project/fpga/rtl/vision_preprocess/rgb888_axis_fp32_normalize.v]]
foreach vp_source $vp_rtl_files {
    if {![file isfile $vp_source]} {error "Required OOC source is missing: $vp_source"}
}
read_verilog $vp_rtl_files
set vp_xdc [file join $vp_ooc_evidence clock.xdc]
set vp_file [open $vp_xdc w]
puts $vp_file {create_clock -name preprocess_clk -period 10.000 [get_ports clk]}
close $vp_file
read_xdc $vp_xdc
synth_design -top vision_preprocess_axi -part xc7z020clg400-1 -mode out_of_context
report_utilization -file [file join $vp_ooc_evidence utilization_synth.rpt]
opt_design
place_design
route_design
report_utilization -file [file join $vp_ooc_evidence utilization_routed.rpt]
report_timing_summary -report_unconstrained -file [file join $vp_ooc_evidence timing_routed.rpt]
report_route_status -file [file join $vp_ooc_evidence route_status.rpt]
report_drc -file [file join $vp_ooc_evidence drc.rpt]
set vp_setup [get_timing_paths -max_paths 1]
set vp_hold [get_timing_paths -delay_type min -max_paths 1]
set vp_setup_pass 0
set vp_hold_pass 0
set vp_wns NA
set vp_whs NA
if {[llength $vp_setup]==1} {
    set vp_wns [get_property SLACK $vp_setup]
    if {$vp_wns>=0} {set vp_setup_pass 1}
}
if {[llength $vp_hold]==1} {
    set vp_whs [get_property SLACK $vp_hold]
    if {$vp_whs>=0} {set vp_hold_pass 1}
}
set vp_timing_pass [expr {$vp_setup_pass && $vp_hold_pass}]
set vp_file [open [file join $vp_ooc_evidence result.tcl] w]
puts $vp_file [list set wns_ns $vp_wns]
puts $vp_file [list set whs_ns $vp_whs]
puts $vp_file [list set timing_pass $vp_timing_pass]
puts $vp_file {set clock_period_ns 10.000}
puts $vp_file {set scope module_only_OOC_no_external_interface_delays}
close $vp_file
write_checkpoint -force [file join $vp_ooc_evidence routed.dcp]
if {!$vp_setup_pass} {error "OOC setup timing failed; inspect result.tcl and timing_routed.rpt"}
if {!$vp_hold_pass} {error "OOC hold timing failed; inspect result.tcl and timing_routed.rpt"}
puts "VISION_PREPROCESS_OOC_PASS"
