# Same physical pin map; both PCLK domains are active. No fabricated pad delays.
set root [file normalize [file join [file dirname [info script]] ../../..]]
source [file join $root project/fpga/scripts/load_ov5640_pins.tcl]
set commands [exec python -I [file join $root project/scripts/ov5640/snapshot_io_timing.py] [file join $root project/fpga/constraints/ov5640_snapshot_io.json]]
eval $commands
eval [string map {ov1_ ov2_ system_i/camera/ system_i/camera_right/} $commands]
foreach camera {system_i/camera/inst system_i/camera_right/inst} {
    set source [get_cells -quiet -hier -filter "NAME =~ $camera/*capture_reset_n_reg* && IS_SEQUENTIAL == 1"]
    if {[llength $source]!=1} {error "Capture reset source not unique for $camera: $source"}
    set resets [get_cells -quiet -hier -filter "NAME =~ $camera/*p_reset_reg* || NAME =~ $camera/*u_capture/reset_sync_reg*"]
    foreach cell $resets {
        set p [get_pins -quiet $cell/CLR]
        if {![llength $p]} {set p [get_pins -quiet $cell/PRE]}
        if {[llength $p]} {set_false_path -from $source -to $p}
    }
}
set arm {};set polarity {}
foreach c [get_cells -quiet -hier -filter {NAME =~ *u_packet/arm_sync_reg*}] {
    if {[file tail $c] eq {arm_sync_reg[0]}} {lappend arm $c}
}
foreach c [get_cells -quiet -hier -filter {NAME =~ *vs_inv_sync_reg* || NAME =~ *href_inv_sync_reg*}] {
    if {[file tail $c] in {{vs_inv_sync_reg[0]} {href_inv_sync_reg[0]}}} {lappend polarity $c}
}
if {[llength $arm]!=2 || [llength $polarity]!=4} {error "Dual camera CDC chains missing"}
foreach cell [concat $arm $polarity [get_cells -quiet -hier -filter {NAME =~ *flags_meta_reg*}]] {
    if {![get_property ASYNC_REG $cell]} {error "Unmarked camera synchronizer $cell"}
    set_false_path -to [get_pins $cell/D]
}
