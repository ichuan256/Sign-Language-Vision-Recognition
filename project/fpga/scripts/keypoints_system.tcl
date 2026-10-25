# Fresh W6 + hand-landmark compute project. Never program hardware here.
# Usage: vivado -mode batch -source keypoints_system.tcl -tclargs prepare|synth|impl <new-output>
set repo [file normalize [file join [file dirname [info script]] ../../..]]
if {[llength $argv] != 2} { error "Expected mode and output directory" }
set mode [lindex $argv 0]
set out [file normalize [lindex $argv 1]]
if {![string match "${repo}/*" $out]} {error "Output must remain in workspace"}
if {![string match "${repo}/project/_tmp/*" $out]} {error "Builds must use isolated project/_tmp directories"}
set part xc7z020clg400-1
set_param general.maxThreads 2

proc connect_clock_reset {cell clk reset} {
    foreach pin [get_bd_pins -quiet -of_objects [get_bd_cells $cell] -filter {TYPE == clk && DIR == I}] {
        if {[llength [get_bd_nets -quiet -of_objects $pin]]==0} {connect_bd_net $clk $pin}
    }
    foreach pin [get_bd_pins -quiet -of_objects [get_bd_cells $cell] -filter {TYPE == rst && DIR == I}] {
        if {[llength [get_bd_nets -quiet -of_objects $pin]]==0} {connect_bd_net $reset $pin}
    }
}

if {$mode eq "inspect"} {
    if {[file exists $out]} {error "Fresh output directory required"}
    file mkdir $out
    open_project -read_only [file join $repo project fpga project glove glove.xpr]
    if {[get_property PART [current_project]] ne $part} {error "Unexpected original part"}
    set repos [get_property IP_REPO_PATHS [current_project]]
    set sources {}
    foreach source [get_files -of_objects [get_filesets sources_1]] {
        set path [file normalize $source]
        if {[string match "*/project/fpga/rtl/*.v" $path]} {lappend sources $path}
    }
    set constraints [get_files -of_objects [get_filesets constrs_1]]
    set bds [get_files -quiet */system.bd]
    if {[llength $bds]!=1} {error "Expected one original system.bd"}
    open_bd_design [lindex $bds 0]
    write_bd_tcl -force [file join $out base_bd.tcl]
    set f [open [file join $out inventory.tcl] w]
    puts $f [list set frozen_sources $sources]
    puts $f [list set frozen_constraints $constraints]
    puts $f [list set original_ip_repos $repos]
    close $f
    close_project
    puts "KEYPOINTS_INSPECT_COMPLETE $out"
} elseif {$mode eq "prepare"} {
    if {![file exists [file join $out inventory.tcl]] || [file exists [file join $out vivado]]} {
        error "Inspect first; then use a fresh native-project directory"
    }
    source [file join $out inventory.tcl]
    set sources $frozen_sources
    set constraints $frozen_constraints
    set repos $original_ip_repos
    set mac_repo [file join $repo project _tmp kp_mac_ip_v1 tile_prj solution1 impl ip]
    set vec_repo [file join $repo project _tmp kp_vector_ip_v1 vector_prj solution1 impl ip]
    foreach r [list $mac_repo $vec_repo] {
        if {![file exists [file join $r component.xml]]} {error "Missing validated HLS IP: $r"}
    }
    create_project kp_hand [file join $out vivado] -part $part
    set_property target_language Verilog [current_project]
    set_property ip_repo_paths [concat $repos [list $mac_repo $vec_repo]] [current_project]
    update_ip_catalog -rebuild
    add_files -norecurse $sources
    add_files -fileset constrs_1 -norecurse $constraints
    set_property PROCESSING_ORDER LATE [get_files */w6_interfaces.xdc]
    source [file join $out base_bd.tcl]
    current_bd_design system

    foreach pair {{kp_mac kp_gemm_tile} {kp_vector kp_vector}} {
        lassign $pair instance name
        set definitions [get_ipdefs -quiet xilinx.com:hls:${name}:1.0]
        if {[llength $definitions]!=1} {error "Expected exactly one validated $name IP definition"}
        create_bd_cell -type ip -vlnv [lindex $definitions 0] $instance
    }
    set clk [get_bd_pins ps7/FCLK_CLK0]
    set reset [get_bd_pins rst_ps7_100M/peripheral_aresetn]
    set periph [get_bd_cells ps7_axi_periph]
    set original_mi [get_property CONFIG.NUM_MI $periph]
    if {$original_mi!=4} {error "Original GP0 crossbar differs; inspect before modifying"}
    set_property CONFIG.NUM_MI 6 $periph
    connect_bd_intf_net [get_bd_intf_pins ps7_axi_periph/M04_AXI] [get_bd_intf_pins kp_mac/s_axi_control]
    connect_bd_intf_net [get_bd_intf_pins ps7_axi_periph/M05_AXI] [get_bd_intf_pins kp_vector/s_axi_control]
    connect_clock_reset ps7_axi_periph $clk $reset
    connect_clock_reset kp_mac $clk $reset
    connect_clock_reset kp_vector $clk $reset

    if {[get_property CONFIG.PCW_USE_S_AXI_HP3 [get_bd_cells ps7]]!=0} {error "HP3 is not free"}
    set_property CONFIG.PCW_USE_S_AXI_HP3 1 [get_bd_cells ps7]
    connect_bd_net $clk [get_bd_pins ps7/S_AXI_HP3_ACLK]
    create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 kp_ddr
    set f [open [file join $out kp_ddr_default_audit.tcl] w]
    foreach prop [lsort [list_property [get_bd_cells kp_ddr]]] {
        if {[string match CONFIG.* $prop]} {puts $f [list $prop [get_property $prop [get_bd_cells kp_ddr]]]}
    }
    close $f
    set_property -dict [list CONFIG.NUM_SI 7 CONFIG.NUM_MI 1] [get_bd_cells kp_ddr]
    set interfaces {kp_mac/m_axi_activ kp_mac/m_axi_weights kp_mac/m_axi_params kp_mac/m_axi_output_data kp_vector/m_axi_input_a kp_vector/m_axi_input_b kp_vector/m_axi_output_data}
    set index 0
    foreach intf $interfaces {
        connect_bd_intf_net [get_bd_intf_pins $intf] [get_bd_intf_pins [format "kp_ddr/S%02d_AXI" $index]]
        incr index
    }
    connect_bd_intf_net [get_bd_intf_pins kp_ddr/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP3]
    connect_clock_reset kp_ddr $clk $reset
    foreach pair {{kp_mac 0x43C20000} {kp_vector 0x43C30000}} {
        lassign $pair instance address
        set segments [get_bd_addr_segs -of_objects [get_bd_intf_pins ${instance}/s_axi_control]]
        if {[llength $segments]!=1} {error "Unexpected control address map on $instance"}
        assign_bd_address -target_address_space [get_bd_addr_spaces ps7/Data] -offset $address -range 64K [lindex $segments 0]
        foreach master [get_bd_intf_pins -of_objects [get_bd_cells $instance] -filter {MODE == Master}] {
            set spaces [get_bd_addr_spaces -of_objects $master]
            if {[llength $spaces]!=1} {error "Expected one address space on $master"}
            assign_bd_address -target_address_space [lindex $spaces 0] -offset 0 -range 512M [get_bd_addr_segs ps7/S_AXI_HP3/HP3_DDR_LOWOCM]
        }
    }
    validate_bd_design
    save_bd_design
    write_bd_tcl -force [file join $out integrated_bd.tcl]
    set bd [get_files */system.bd]
    generate_target all $bd
    source [file join $repo project fpga scripts w6_timing_ip_constraints.tcl]
    set wrapper [make_wrapper -files $bd -top]
    add_files -norecurse $wrapper
    set_property top system_wrapper [get_filesets sources_1]
    update_compile_order -fileset sources_1
    puts "KEYPOINTS_PREPARE_COMPLETE [get_property NAME [current_project]]"
    close_project
} elseif {$mode eq "constraints_resume"} {
    open_project [file join $out vivado kp_hand.xpr]
    source [file join $repo project fpga scripts w6_timing_ip_constraints.tcl]
    set_property PROCESSING_ORDER LATE [get_files */w6_interfaces.xdc]
    reset_run impl_1
    reset_run synth_1
    close_project
} elseif {$mode eq "synth" || $mode eq "synth_resume"} {
    open_project [file join $out vivado kp_hand.xpr]
    if {$mode eq "synth_resume"} {
        foreach run [get_runs *_synth_1] {
            if {![string match "*Complete*" [get_property STATUS $run]]} {reset_run $run}
        }
        reset_run synth_1
    }
    launch_runs synth_1 -jobs 1
    wait_on_run synth_1
    set status [get_property STATUS [get_runs synth_1]]
    puts "KEYPOINTS_SYNTH_STATUS=$status"
    if {$status ne "synth_design Complete!"} {error "Synthesis did not complete"}
    open_run synth_1
    report_utilization -file [file join $out utilization_synth.rpt]
    report_timing_summary -file [file join $out timing_synth.rpt]
    close_project
} elseif {$mode eq "impl"} {
    open_project [file join $out vivado kp_hand.xpr]
    if {[get_property STATUS [get_runs synth_1]] ne "synth_design Complete!"} {error "Synthesis gate missing"}
    launch_runs impl_1 -to_step write_bitstream -jobs 1
    wait_on_run impl_1
    set status [get_property STATUS [get_runs impl_1]]
    puts "KEYPOINTS_IMPL_STATUS=$status"
    if {$status ne "write_bitstream Complete!"} {error "Implementation/bitstream did not complete"}
    open_run impl_1
    report_utilization -file [file join $out utilization_routed.rpt]
    report_timing_summary -file [file join $out timing_routed.rpt]
    report_route_status -file [file join $out route_status.rpt]
    report_methodology -file [file join $out methodology_routed.rpt]
    report_bus_skew -file [file join $out bus_skew.rpt]
    set audit [open [file join $out methodology_routed.rpt] r]
    set methodology [read $audit]
    close $audit
    if {[regexp {TIMING-(4|27|36)#[0-9]} $methodology]} {error "Clock methodology gate failed; do not deploy"}
    set paths [get_timing_paths -max_paths 1 -nworst 1]
    if {[llength $paths]!=1 || [get_property SLACK [lindex $paths 0]]<0} {error "Negative or absent routed setup timing"}
    set hold_paths [get_timing_paths -delay_type min -max_paths 1 -nworst 1]
    if {[llength $hold_paths]!=1 || [get_property SLACK [lindex $hold_paths 0]]<0} {error "Negative or absent routed hold timing"}
    set release [file join $out release]
    file mkdir $release
    file copy [file join $out vivado kp_hand.runs impl_1 system_wrapper.bit] [file join $release hand_hdmi.bit]
    file copy [file join $out vivado kp_hand.gen sources_1 bd system hw_handoff system.hwh] [file join $release hand_hdmi.hwh]
    puts "KEYPOINTS_RELEASE_READY $release"
    close_project
} else {error "Unknown mode: $mode"}
exit
