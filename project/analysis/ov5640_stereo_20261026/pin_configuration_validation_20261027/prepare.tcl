# Isolated feasibility project; never opens or edits glove.xpr.
set evidence [file normalize [file dirname [info script]]]
set root [file normalize [file join $evidence ../../../..]]
if {[current_project -quiet] ne ""} {error "Close the current project before preparation"}
create_project -in_memory -part xc7z020clg400-1
set_param general.maxThreads 2
set_property target_language Verilog [current_project]
read_verilog [glob [file join $root project/fpga/rtl/ov5640_stereo/*.v]]
read_verilog [file join $evidence pin_validation_top.v]
puts "PIN_VALIDATION_PREPARED $root"
