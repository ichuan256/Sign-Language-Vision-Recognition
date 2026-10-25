set root [file normalize [file join [file dirname [info script]] ../..]]
set out [file join $root analysis timing_20261018]
file mkdir $out
open_project [file join $root fpga project glove glove.xpr]
open_run impl_1
report_clocks -file [file join $out baseline_clocks.rpt]
check_timing -verbose -file [file join $out baseline_check_timing.rpt]
report_timing -from [get_ports {spia_miso spib_miso sdata_i}] -max_paths 12 -file [file join $out baseline_inputs.rpt]
set f [open [file join $out clock_files.txt] w]
foreach x [get_files -all -filter {FILE_TYPE == XDC}] {
    puts $f "$x scope=[get_property SCOPED_TO_REF $x] order=[get_property PROCESSING_ORDER $x]"
}
close $f
exit
