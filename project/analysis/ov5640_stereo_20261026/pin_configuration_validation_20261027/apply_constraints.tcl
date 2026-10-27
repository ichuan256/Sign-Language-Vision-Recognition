# Run after synth_design -top pin_validation_top -part xc7z020clg400-1.
set evidence [file normalize [file dirname [info script]]]
set root [file normalize [file join $evidence ../../../..]]
source [file join $root project/fpga/scripts/load_ov5640_pins.tcl]
# This harness uses the board 125 MHz oscillator; W6 uses PS 100 MHz.
set_property -dict {PACKAGE_PIN H16 IOSTANDARD LVCMOS33} [get_ports sys_clk]
set_property -dict {PACKAGE_PIN D19 IOSTANDARD LVCMOS33} [get_ports {buttons[0]}]
set_property -dict {PACKAGE_PIN D20 IOSTANDARD LVCMOS33} [get_ports {buttons[1]}]
foreach pin {R14 P14 N16 M14} bit {0 1 2 3} {
    set_property -dict [list PACKAGE_PIN $pin IOSTANDARD LVCMOS33] [get_ports [format {leds[%d]} $bit]]
}
create_clock -name harness_sys_clk -period 8.000 [get_ports sys_clk]
# 84 MHz is configuration-derived and has not been measured.
create_clock -name ov1_pclk -period 11.904762 [get_ports ov1_pclk]
create_clock -name ov2_pclk -period 11.904762 [get_ports ov2_pclk]
# No invented sensor I/O delays, false paths or dedicated-route overrides.
report_io -file [file join $evidence post_synth_io.rpt]
set out [open [file join $evidence package_pin_properties.txt] w]
foreach p [lsort [get_ports ov*]] {
    set pad [get_property PACKAGE_PIN $p]
    set pkg [get_package_pins $pad]
    puts $out [list $p $pad [get_property PIN_FUNC $pkg] [get_iobanks -of_objects $pkg] [get_property IS_CLK_CAPABLE $pkg]]
}
close $out
puts "PIN_CONSTRAINTS_APPLIED"
