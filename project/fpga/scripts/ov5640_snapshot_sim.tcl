set root [file normalize [file join [file dirname [info script]] ../../..]]
if {![info exists snapshot_sim_evidence]} {set snapshot_sim_evidence [file join $root project/analysis/ov5640_snapshot_20261027]}
set evidence $snapshot_sim_evidence
file mkdir $evidence
if {[current_project -quiet] ne ""} {error "Close build project first"}
set sim_xpr [file join $root project/_tmp/ov5640_snapshot_sim/snapshot_sim.xpr]
if {[file exists $sim_xpr]} {open_project $sim_xpr} else {
    create_project snapshot_sim [file dirname $sim_xpr] -part xc7z020clg400-1
}
set_property target_simulator XSim [current_project]
set_property XPM_LIBRARIES {XPM_FIFO XPM_CDC} [current_project]
add_files [glob [file join $root project/fpga/rtl/ov5640_stereo/*.v]]
add_files [glob [file join $root project/fpga/rtl/ov5640_snapshot/*.v]]
add_files -fileset sim_1 [glob [file join $root project/fpga/tb/ov5640_snapshot/*.v]]
add_files -fileset sim_1 [list \
    [file join $root project/fpga/tb/ov5640_stereo/tb_ov5640_dvp_capture.v] \
    [file join $root project/fpga/tb/ov5640_stereo/tb_ov5640_stereo_capture_pair.v] \
    [file join $root project/fpga/tb/ov5640_stereo/tb_ov5640_startup_capture.v] \
    [file join $root project/fpga/tb/ov5640_stereo/tb_ov5640_stereo_top.v] \
    [file join $root project/fpga/tb/ov5640_stereo/tb_ov5640_720p_frame.v]]
add_files -fileset sim_1 [file join $root project/fpga/tb/ov5640_stereo/ov5640_startup_sensor_model.v]
add_files -fileset sim_1 [file join $root project/fpga/tb/ov5640_stereo/ov5640_sccb_sensor_model.v]
add_files -fileset sim_1 [file join $root project/fpga/tb/ov5640_stereo/tb_ov5640_sccb_register_access.v]
set simset [get_filesets sim_1]
set_property top ov5640_snapshot [get_filesets sources_1]
set_property xsim.simulate.runtime 120ms $simset
set xsimdir [file join [get_property DIRECTORY [current_project]] snapshot_sim.sim/sim_1/behav/xsim]
set summary [open [file join $evidence snapshot_regression.txt] w]
if {![info exists snapshot_sim_tops]} {
    set snapshot_sim_tops {tb_ov5640_sccb_register_access tb_snapshot_packet tb_snapshot_system tb_snapshot_720p tb_ov5640_dvp_capture tb_ov5640_stereo_capture_pair tb_ov5640_startup_capture tb_ov5640_stereo_top tb_ov5640_720p_frame}
}
foreach top $snapshot_sim_tops {
    set_property top $top $simset
    update_compile_order -fileset sources_1
    update_compile_order -fileset sim_1
    launch_simulation -simset sim_1 -mode behavioral
    close_sim -force
    set target [file join $evidence $top]
    file mkdir $target
    foreach name {xvlog.log elaborate.log simulate.log} {
        file copy -force [file join $xsimdir $name] [file join $target $name]
    }
    set f [open [file join $target simulate.log] r];set transcript [read $f];close $f
    if {![regexp {TEST_PASS:} $transcript] || [regexp {Fatal:|Error:} $transcript]} {
        puts $summary "FAIL $top";close $summary;error "Snapshot test failed $top"
    }
    puts $summary "PASS $top";flush $summary
}
close $summary
puts "SNAPSHOT_SIM_ALL_PASS"
