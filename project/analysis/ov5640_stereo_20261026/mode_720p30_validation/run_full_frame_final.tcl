# Use within the dedicated startup.xpr project. Self-checking watchdogs bound
# each test; only a flushed transcript containing TEST_PASS passes the gate.
set evidence [file normalize .]
set simset [get_filesets sim_1]
set xsimdir [file join [get_property DIRECTORY [current_project]] mode720p30.sim sim_1 behav xsim]
set startup_tops {tb_ov5640_720p_frame}
set summary [open [file join $evidence full_frame_final_results.txt] w]
foreach top $startup_tops {
    catch {close_sim -force}
    set_property top $top $simset
    set_property xsim.simulate.runtime 100ms $simset
    update_compile_order -fileset sim_1
    launch_simulation -simset sim_1 -mode behavioral
    close_sim -force
    set target [file join $evidence $top]
    file mkdir $target
    foreach name {compile.log xvlog.log elaborate.log simulate.log} {
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
    if {![regexp {TEST_PASS:|TEST_PASS |PASS:} $transcript] || [regexp {Fatal:|Error:} $transcript]} {
        puts $summary "FAIL $top"
        close $summary
        error "Startup regression did not pass: $top"
    }
    puts $summary "PASS $top"
    flush $summary
    puts "MODE720P_REGRESSION_PASS $top"
}
puts $summary "MODE720P_REGRESSION_ALL_PASS [llength $startup_tops]"
close $summary
puts "MODE720P_REGRESSION_ALL_PASS [llength $startup_tops]"
