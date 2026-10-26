# Post-synthesis/pre-opt hook. Sensor external I/O delays remain unverified.
set root [file normalize [file join [file dirname [info script]] ../../..]]
source [file join $root project/fpga/scripts/load_ov5640_pins.tcl]
create_clock -name ov1_pclk -period 11.904762 [get_ports ov1_pclk]
# Only OV1 is sampled. OV2 stays held in reset/power-down in this build.
set camera system_i/camera/inst
set source [get_cells -quiet -hier -filter {NAME =~ *camera*/*capture_reset_n_reg* && IS_SEQUENTIAL == 1}]
if {[llength $source]!=1} {error "Capture reset source not found uniquely: $source"}
set resets [get_cells -quiet -hier -filter {NAME =~ *camera*/*p_reset_reg* || NAME =~ *camera*/*u_capture/reset_sync_reg*}]
foreach cell $resets {
    set p [get_pins -quiet $cell/CLR]
    if {[llength $p]==0} {set p [get_pins -quiet $cell/PRE]}
    if {[llength $p]} {set_false_path -from $source -to $p}
}
# Each asynchronous single-bit crossing has explicit two-flop ASYNC_REG chain.
set first_arm {}
foreach c [get_cells -quiet -hier -filter {NAME =~ *u_packet/arm_sync_reg*}] {
    if {[file tail $c] eq {arm_sync_reg[0]}} {lappend first_arm $c}
}
if {[llength $first_arm] != 1} {error "Expected exactly one first arm synchronizer: $first_arm"}
set first_flags [get_cells -quiet -hier -filter {NAME =~ *flags_meta_reg*}]
foreach cell [concat $first_arm $first_flags] {
    if {![get_property ASYNC_REG $cell]} {error "Unmarked snapshot synchronizer $cell"}
    set_false_path -to [get_pins $cell/D]
}
# XPM FIFO generates its own Gray-pointer CDC constraints; do not mask domains.
puts "SNAPSHOT_CONSTRAINTS_APPLIED"
