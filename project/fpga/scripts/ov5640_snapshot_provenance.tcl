set snapshot_provenance_script [file normalize [file join [file dirname [info script]] ../../scripts/ov5640/snapshot_provenance.py]]
proc snapshot_provenance {action project_dir {build_dir {}}} {
    global snapshot_provenance_script
    set cmd [list python -I $snapshot_provenance_script $action --project $project_dir]
    if {$build_dir ne {}} {lappend cmd --build $build_dir}
    puts [exec {*}$cmd]
}
proc snapshot_bind_project {} {
    global snapshot_provenance_script
    set project_dir [get_property DIRECTORY [current_project]]
    set list_path [file join $project_dir provenance_file_list.txt]
    set f [open $list_path w]; fconfigure $f -encoding utf-8
    foreach name [lsort -unique [get_files -all]] {
        # Vivado updates generated XML/status files while running. Bind actual
        # HDL/constraints and BD/IP configurations, not mutable run metadata.
        if {[file isfile $name] && [string tolower [file extension $name]] in {.v .sv .vh .svh .vhd .vhdl .xdc .bd .xci .coe .mem}} {puts $f [file normalize $name]}
    }
    close $f
    puts [exec python -I $snapshot_provenance_script project --project $project_dir --file-list $list_path]
}
