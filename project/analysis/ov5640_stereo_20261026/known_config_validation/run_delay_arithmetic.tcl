set evidence [file normalize .]
set simset [get_filesets sim_1]
set xsimdir [file join [get_property DIRECTORY [current_project]] known_config.sim sim_1 behav xsim]
set tops {tb_ov5640_known_config_sequence}
set summary [open [file join $evidence delay_arithmetic_results.txt] w]
foreach top $tops {
    catch {close_sim -force}
    set_property top $top $simset
    set runtime [expr {$top eq "tb_ov5640_timing_defaults" ? "70ms" : "1ms"}]
    set_property xsim.simulate.runtime $runtime $simset
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
    if {![regexp {TEST_PASS|PASS:} $transcript] || [regexp {Fatal:|Error:} $transcript]} {
        puts $summary "FAIL $top"
        close $summary
        error "Regression did not pass: $top"
    }
    puts $summary "PASS $top"
    flush $summary
    puts "REGRESSION_PASS $top"
}
puts $summary "REGRESSION_ALL_PASS [llength $tops]"
close $summary
puts "REGRESSION_ALL_PASS [llength $tops]"


