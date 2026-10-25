# fixup_rtl.tcl —— 移植一次性修正②：.v 源码引用从旧工作区相对路径换到本仓库
# 用法: run_fixup2.bat
set d [file dirname [file normalize [info script]]]
set root [file normalize [file join $d ../..]]
set proj [file join $root fpga project glove glove.xpr]
open_project $proj

set moved 0
foreach f [get_files -quiet *.v] {
    if {[string match "*pld-sign-glove/fpga/rtl/*" $f]} {
        set name [file tail $f]
        set fs [lindex [get_filesets -quiet -of_objects [get_files $f]] 0]
        if {$fs eq ""} { set fs sources_1 }
        remove_files -fileset $fs $f
        add_files -fileset $fs -norecurse [file join $root fpga rtl $name]
        puts "RTL 重定位: $name ($fs)"
        incr moved
    }
    if {[string match "*pld-sign-glove/fpga/tb/*" $f]} {
        set name [file tail $f]
        set fs [lindex [get_filesets -quiet -of_objects [get_files $f]] 0]
        if {$fs eq ""} { set fs sim_1 }
        remove_files -fileset $fs $f
        add_files -fileset $fs -norecurse [file join $root fpga tb $name]
        puts "TB 重定位: $name ($fs)"
        incr moved
    }
}
puts "共重定位 $moved 个文件"
close_project
puts "=== FIXUP2 OK"
