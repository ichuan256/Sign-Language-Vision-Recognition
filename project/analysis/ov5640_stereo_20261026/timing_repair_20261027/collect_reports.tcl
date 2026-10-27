# Run only after successful route_design in this isolated harness.
set evidence [file normalize [file dirname [info script]]]
report_route_status -file $evidence/route_status.rpt
report_clock_utilization -file $evidence/clock_utilization.rpt
report_drc -file $evidence/drc.rpt
report_timing_summary -report_unconstrained -file $evidence/timing_summary.rpt
report_timing -from [get_clocks harness_sys_clk] -to [get_clocks harness_sys_clk] -max_paths 3 -file $evidence/system_clock_timing.rpt
report_io -file $evidence/post_route_io.rpt
report_utilization -file $evidence/utilization.rpt
set out [open $evidence/pad_and_clock_checks.txt w]
set camera_ports [get_ports ov*]
if {[llength $camera_ports] != 30} {error "Expected 30 camera ports"}
puts $out "CAMERA_PORT_COUNT 30"
set assigned {}
foreach p $camera_ports {
    set pad [get_property PACKAGE_PIN $p]
    if {$pad eq "" || [lsearch -exact $assigned $pad] >= 0} {error "Missing/duplicate pad $p"}
    if {[get_property IOSTANDARD $p] ne "LVCMOS33"} {error "Incorrect IO standard $p"}
    lappend assigned $pad
}
puts $out "UNIQUE_CAMERA_PADS 30"
foreach p {ov1_pclk ov2_pclk} expected {Y9 U7} {
    set port [get_ports $p]
    if {[get_property PACKAGE_PIN $port] ne $expected} {error "Incorrect PCLK pad"}
    set pkg [get_package_pins $expected]
    if {![get_property IS_CLK_CAPABLE $pkg]} {error "PCLK not clock capable"}
    set function [get_property PIN_FUNC $pkg]
    if {![string match {*P_*_SRCC_*} $function]} {error "PCLK not SRCC P side"}
    puts $out [list PCLK $p $expected $function]
}
foreach c [get_cells -hier -filter {REF_NAME == BUFG}] {
    puts $out [list BUFG $c [get_property LOC $c]]
}
# Each SCCB output buffer must have a grounded data input; only T toggles.
set count 0
# The IOBUF's internal OBUFT also appears in hierarchical queries: count
# the four actual pad buffers explicitly, not those nested subprimitives.
foreach name {ov1_scl_OBUFT_inst ov2_scl_OBUFT_inst u_camera/ov1_sda_IOBUF_inst u_camera/ov2_sda_IOBUF_inst} {
    set c [get_cells $name]
    if {[llength $c] != 1} {error "Missing SCCB pad buffer: $name"}
    set input [get_pins $c/I]
    set net [get_nets -of_objects $input]
    # Hierarchical constant net segments need not expose the root GND cell.
    if {[get_property TYPE $net] ne "GROUND"} {
        error "SCCB buffer data input is not grounded: $c"
    }
    puts $out [list OPEN_DRAIN $c [get_property REF_NAME $c] $net [get_property TYPE $net]]
    incr count
}
if {$count != 4} {error "Expected four open-drain SCCB buffers, got $count"}
puts $out "PIN_AND_PAD_CHECKS_PASS"
close $out
puts "PIN_REPORTS_AND_PAD_CHECKS_SAVED"
report_cdc -details -file $evidence/cdc.rpt
report_exceptions -coverage -file $evidence/exceptions.rpt
report_timing -delay_type min -max_paths 5 -file $evidence/hold_timing.rpt
write_checkpoint -force $evidence/routed.dcp
