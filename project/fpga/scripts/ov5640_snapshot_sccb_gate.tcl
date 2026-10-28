# Structural acceptance on the integrated synthesized/routed design.
# SCL can legitimately lose its unused input buffer; SDA must retain readback.
proc snapshot_check_sccb {} {
    set result {}
    foreach port {ov1_scl ov1_sda} pad {W9 Y8} {
        set p [get_ports $port]
        if {[get_property PACKAGE_PIN $p] ne $pad} {error "SCCB pin mismatch: $port"}
        set nets [get_nets -segments -of_objects $p]
        set cells [lsort -unique [get_cells -of_objects [get_pins -leaf -of_objects $nets]]]
        set outputs {}
        foreach c $cells {
            if {[get_property REF_NAME $c] in {IOBUF OBUFT}} {lappend outputs $c}
        }
        if {[llength $outputs]!=1} {error "SCCB $port requires one tristate buffer; found $cells"}
        set c [lindex $outputs 0]
        set input_net [get_nets -of_objects [get_pins $c/I]]
        if {[get_property TYPE $input_net] ne "GROUND"} {error "SCCB $port must only drive zero"}
        set tristate_net [get_nets -of_objects [get_pins $c/T]]
        if {[get_property TYPE $tristate_net] in {GROUND POWER}} {error "SCCB $port tristate is constant"}
        set roots [all_fanin -flat -startpoints_only -to [get_pins $c/T]]
        if {[llength $roots]==0} {error "SCCB $port tristate has no control"}
        if {$port eq "ov1_sda"} {
            # Implemented IOBUFs may be decomposed into OBUFT + IBUF.
            set inputs {}
            foreach input_cell $cells {
                if {[get_property REF_NAME $input_cell] in {IOBUF IBUF}} {lappend inputs $input_cell}
            }
            if {[llength $inputs]!=1} {error "SDA requires one input buffer; found $inputs"}
            set ends [all_fanout -flat -endpoints_only -from [get_pins [lindex $inputs 0]/O]]
            if {[llength $ends]==0 || ![string match *u_read* $ends]} {error "SDA readback does not reach read engine"}
            append result "SDA_READBACK_ENDPOINTS=$ends\n"
        }
        append result "PASS $port $pad [get_property REF_NAME $c] I=GND T=dynamic\n"
    }
    return $result
}
