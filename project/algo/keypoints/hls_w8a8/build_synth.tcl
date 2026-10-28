# Bounded feasibility synthesis: dw_3 / pw_3 / stem (Vitis HLS 2024.1).
# Usage (interactive console): vitis_hls -f build_synth.tcl
set src_dir [file dirname [file normalize [info script]]]
set vec_dir "F:/PLD_new/Sign-Language-Vision-Recognition/project/_tmp/kp_vectors_c_20261028"
open_project -reset [file join $src_dir kp_hls_feasibility]
add_files [file join $src_dir kp_hls_kernels.cpp]
add_files -tb [file join $src_dir kp_hls_tb.cpp] -cflags "-DVECTORS_DIR=$vec_dir"

open_solution -reset "sol_dw3"
set_part {xc7z020clg400-1}
create_clock -period 10 -name default
set_top kp_hls_dw3
csynth_design

open_solution -reset "sol_pw3"
set_part {xc7z020clg400-1}
create_clock -period 10 -name default
set_top kp_hls_pw3
csynth_design

open_solution -reset "sol_stem"
set_part {xc7z020clg400-1}
create_clock -period 10 -name default
set_top kp_hls_stem
csynth_design
exit
