# Run after routing and collect_reports.tcl; do not accept empty timing paths.
set evidence [file normalize [file dirname [info script]]]
set f [open $evidence/timing_acceptance.txt w]
foreach delay {max min} {
    set p [get_timing_paths -delay_type $delay -max_paths 1]
    if {[llength $p] != 1 || [get_property SLACK $p] < 0} {error "Timing failed: $delay"}
    puts $f [list $delay SLACK [get_property SLACK $p] FROM [get_property STARTPOINT_PIN $p] TO [get_property ENDPOINT_PIN $p]]
}
foreach camera {1 2} {
    set stage0 [get_cells [format {u_camera/u_capture%d/reset_sync_reg[0]} $camera]]
    set stage1 [get_cells [format {u_camera/u_capture%d/reset_sync_reg[1]} $camera]]
    set p [get_timing_paths -from $stage0 -to $stage1 -max_paths 1]
    if {[llength $p] != 1 || [get_property SLACK $p] < 0} {error "Reset synchronizer chain is not timed"}
    puts $f [list RESET_CHAIN $camera SLACK [get_property SLACK $p]]
    set endpoints [get_pins -hier -filter [format {NAME =~ u_camera/u_capture%d/*/CLR} $camera]]
    set p [get_timing_paths -from $stage1 -to $endpoints -max_paths 1]
    if {[llength $p] != 1 || [get_property SLACK $p] < 0} {error "Reset release recovery is not timed"}
    puts $f [list RESET_RECOVERY $camera SLACK [get_property SLACK $p]]
}
puts $f TIMING_ACCEPTANCE_PASS
close $f
puts TIMING_ACCEPTANCE_PASS
