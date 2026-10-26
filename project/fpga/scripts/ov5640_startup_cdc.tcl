# Call after synthesis for each ov5640_stereo_startup_capture instance.
# UG903 async CDC: narrow exceptions, no blanket asynchronous clock groups.
proc constrain_ov5640_startup_cdc {instance} {
    # Synthesis may absorb reset polarity into an FDPE named *_reg_inv.
    set reset_source [get_cells -quiet -filter {IS_SEQUENTIAL == 1} ${instance}/capture_reset_n_reg*]
    if {[llength $reset_source] != 1} {
        error "OV5640 registered capture reset missing at $instance"
    }
    foreach camera {1 2} {
        set reset_clr {}
        foreach bit {0 1} {
            set cell [get_cells -quiet [format {%s/u_capture%d/reset_sync_reg[%d]} $instance $camera $bit]]
            if {[llength $cell] != 1 || ![get_property ASYNC_REG $cell]} {
                error "Missing marked OV5640 reset synchronizer: camera $camera bit $bit"
            }
            lappend reset_clr [get_pins $cell/CLR]
        }
        if {[llength $reset_clr] != 2} {
            error "OV5640 CDC endpoint count mismatch: camera $camera"
        }
        # Registered source asserts reset asynchronously. PCLK chain releases
        # synchronously. Q->D and Q->downstream CLR remain timed.
        set_false_path -from $reset_source -to $reset_clr
        puts "OV5640_CDC_CONSTRAINED camera=$camera reset_clr=$reset_clr"
    }
}
