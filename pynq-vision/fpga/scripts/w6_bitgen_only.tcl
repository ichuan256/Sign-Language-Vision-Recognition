# w6_bitgen_only.tcl - resume from routed checkpoint: write_bitstream + export
# (full impl finished routing; bitgen OOM'd, so rerun bitgen standalone)
set w6_script_dir [file dirname [file normalize [info script]]]
set w6_repo_root [file normalize [file join $w6_script_dir ../..]]
set w6_project_path [file join $w6_repo_root fpga project glove glove.xpr]
proc logmsg {s} { puts "[clock format [clock seconds] -format %H:%M:%S] $s" }

open_project $w6_project_path
open_run impl_1
logmsg "routed checkpoint loaded"

set impl_dir [get_property DIRECTORY [get_runs impl_1]]
write_bitstream -force [file join $impl_dir system_wrapper.bit]
logmsg "write_bitstream done"

set outdir [file dirname $w6_project_path]
set bit [file join $impl_dir system_wrapper.bit]
set hwh [lindex [concat \
    [glob -nocomplain [file join $outdir glove.gen sources_1 bd system hw_handoff system.hwh]] \
    [glob -nocomplain [file join $outdir glove.srcs sources_1 bd system hw_handoff system.hwh]]] 0]
set dest [file join $w6_repo_root board_validation w6]
file copy -force $bit [file join $dest kws_hdmi.bit]
file copy -force $hwh [file join $dest kws_hdmi.hwh]
logmsg "exported: $dest/kws_hdmi.bit + .hwh"
exit
