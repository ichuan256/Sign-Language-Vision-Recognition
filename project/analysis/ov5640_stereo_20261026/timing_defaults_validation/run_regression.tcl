set evidence [file normalize .]
set simset [get_filesets sim_1]
set xsimdir [file join [get_property DIRECTORY [current_project]] timing_defaults.sim sim_1 behav xsim]
foreach top {tb_ov5640_timing_defaults tb_ov5640_stereo_camera_init tb_ov5640_dvp_capture tb_ov5640_stereo_capture_pair tb_ov5640_sccb_write tb_ov5640_stereo_sccb_pair tb_ov5640_stereo_top tb_ov5640_sccb_read tb_ov5640_pll_config} {
    catch {close_sim -force}
    set_property top $top $simset
    set runtime [expr {$top eq "tb_ov5640_timing_defaults" ? "70ms" : "1ms"}]
    set_property xsim.simulate.runtime $runtime $simset
    update_compile_order -fileset sim_1
    launch_simulation -simset sim_1 -mode behavioral
    # XSim's runtime transcript is buffered until the simulation is closed.
    close_sim -force
    set target [file join $evidence $top]
    file mkdir $target
    foreach name {compile.log elaborate.log simulate.log} {
        if {[file exists [file join $xsimdir $name]]} {
            file copy -force [file join $xsimdir $name] [file join $target $name]
        }
    }
    foreach name [glob -nocomplain [file join $xsimdir ${top}*.tcl]] {
        file copy -force $name [file join $target [file tail $name]]
    }
    set f [open [file join $target simulate.log] r]
    set transcript [read $f]
    close $f
    if {![regexp {TEST_PASS|PASS:} $transcript] || [regexp {Fatal:|Error:} $transcript]} {
        error "Regression did not pass: $top"
    }
    puts "REGRESSION_PASS $top"
}
catch {close_sim -force}
puts "REGRESSION_ALL_PASS 9"
