# Run with glove.xpr open, before generate_target / synthesis.
open_bd_design [get_files */system.bd]
# Existing fabric BUFG drives clk_in1; local clk_wiz metadata explicitly
# omits create_clock when PRIM_SOURCE=No_buffer. Preserve the PS master clock.
set_property CONFIG.PRIM_SOURCE {No_buffer} [get_bd_cells clk_wiz_audio]
validate_bd_design
save_bd_design
set w6_io_xdc [file join $w6_repo_root fpga xdc w6_interfaces.xdc]
if {![llength [get_files -quiet $w6_io_xdc]]} {
    add_files -fileset constrs_1 -norecurse $w6_io_xdc
}
set_property PROCESSING_ORDER LATE [get_files $w6_io_xdc]
