# Shared run validation and artifact export. Board/BD creation stays in W2/W3.
namespace eval vivado_build {
    proc require_complete {run} {
        set run_obj [get_runs $run]
        set status [get_property STATUS $run_obj]
        if {[get_property PROGRESS $run_obj] ne "100%" ||
            [regexp -nocase {error|fail} $status]} {
            error "$run did not complete successfully: $status"
        }
        if {[get_property NEEDS_REFRESH $run_obj]} {
            error "$run is stale and must be rerun."
        }
    }

    proc require_bitstream {} {
        require_complete impl_1
        set status [get_property STATUS [get_runs impl_1]]
        if {![string match *write_bitstream*Complete* $status]} {
            error "impl_1 did not reach write_bitstream: $status"
        }
    }

    proc synth {jobs} {
        reset_run synth_1
        launch_runs synth_1 -jobs $jobs
        wait_on_run synth_1
        require_complete synth_1
    }

    proc impl {jobs} {
        require_complete synth_1
        reset_run impl_1
        launch_runs impl_1 -to_step write_bitstream -jobs $jobs
        wait_on_run impl_1
        require_bitstream
    }

    proc export_project {project_dir project_name} {
        require_bitstream
        set impl_dir [get_property DIRECTORY [get_runs impl_1]]
        set bit [file join $impl_dir system_wrapper.bit]
        set candidates [concat \
            [glob -nocomplain [file join $project_dir ${project_name}.gen sources_1 bd system hw_handoff system.hwh]] \
            [glob -nocomplain [file join $project_dir ${project_name}.srcs sources_1 bd system hw_handoff system.hwh]]]
        if {![file isfile $bit] || ![llength $candidates]} {
            error "Cannot export: bitstream or system.hwh is missing."
        }
        set out [file join $project_dir export]
        file mkdir $out
        open_run impl_1
        write_hw_platform -fixed -include_bit -force [file join $out ${project_name}.xsa]
        file copy -force $bit [file join $out ${project_name}.bit]
        file copy -force [lindex $candidates 0] [file join $out ${project_name}.hwh]
        return $out
    }
}
