# Source after vision_preprocess_prepare.tcl. Each TB must finish before watchdog.
set vp_root [file normalize [file join [file dirname [info script]] ../../..]]
if {![info exists vp_evidence]} {set vp_evidence [file join $vp_root project/analysis/vision_preprocess_20261028/xsim]}
file mkdir $vp_evidence
set vp_xsim [file join [get_property DIRECTORY [current_project]] vision_preprocess.sim/sim_1/behav/xsim]
set vp_summary [open [file join $vp_evidence regression.txt] w]
foreach vp_top {tb_rgb888_axis_fp32_normalize tb_vision_rgb565_affine tb_vision_preprocess_axi} {
    set_property top $vp_top [get_filesets sim_1]
    update_compile_order -fileset sim_1
    launch_simulation -simset sim_1 -mode behavioral
    close_sim -force
    set vp_target [file join $vp_evidence $vp_top]
    file mkdir $vp_target
    foreach vp_log {xvlog.log elaborate.log simulate.log} {
        file copy -force [file join $vp_xsim $vp_log] [file join $vp_target $vp_log]
    }
    set vp_file [open [file join $vp_target simulate.log] r]
    set vp_transcript [read $vp_file]
    close $vp_file
    if {![regexp {TEST_PASS} $vp_transcript] || [regexp -nocase {Fatal:|Error:|TEST_FAIL} $vp_transcript]} {
        puts $vp_summary "FAIL $vp_top"
        close $vp_summary
        error "XSim failed $vp_top; inspect the preserved complete transcript"
    }
    puts $vp_summary "PASS $vp_top"
    flush $vp_summary
}
close $vp_summary
puts "VISION_PREPROCESS_XSIM_ALL_PASS"
