# fixup_paths.tcl —— 移植一次性修正：旧工作区绝对路径 → 本仓库路径
# 内容：KWS HLS IP 仓库路径；sign_glove_master.xdc 约束文件位置
# 用法: run_fixup.bat（vivado -mode batch -source fixup_paths.tcl）
set d [file dirname [file normalize [info script]]]
set root [file normalize [file join $d ../..]]
set proj [file join $root fpga project glove glove.xpr]
open_project $proj

# 1) IP 仓库：把指向 F:/PLD 旧仓库的 KWS HLS 路径换成本仓库副本
set newkws [file join $root algo kws hls kws_prj sol1 impl ip]
set repos [get_property ip_repo_paths [current_project]]
set fixed {}
foreach r $repos {
    if {[string match "*pld-sign-glove/algo/kws*" $r]} {
        lappend fixed $newkws
        puts "REPO 替换: $r -> $newkws"
    } else {
        lappend fixed $r
    }
}
set_property ip_repo_paths $fixed [current_project]
puts "ip_repo_paths 现为: [get_property ip_repo_paths [current_project]]"

# 2) 约束：剔除旧工作区 master xdc，换入本仓库副本
set oldxdc [get_files -quiet -of_objects [get_filesets constrs_1] *sign_glove_master.xdc]
if {[llength $oldxdc]} {
    remove_files -fileset constrs_1 $oldxdc
    puts "已剔除旧约束: $oldxdc"
}
set newxdc [file join $root fpga xdc sign_glove_master.xdc]
if {![llength [get_files -quiet -of_objects [get_filesets constrs_1] sign_glove_master.xdc]]} {
    add_files -fileset constrs_1 -norecurse $newxdc
    puts "已加入新约束: $newxdc"
}

close_project
puts "=== FIXUP OK"
