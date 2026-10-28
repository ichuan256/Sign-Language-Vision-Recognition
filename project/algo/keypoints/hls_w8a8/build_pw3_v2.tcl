# Dataflow v2 feasibility: pw_3 only (batch=1, int32 shared accumulator).
# Usage (interactive console): vitis_hls -f build_pw3_v2.tcl
set src_dir [file dirname [file normalize [info script]]]
set vec_dir "F:/PLD_new/Sign-Language-Vision-Recognition/project/_tmp/kp_vectors_c_20261028"
open_project -reset [file join $src_dir kp_hls_v2]
add_files [file join $src_dir kp_hls_kernels.cpp]
add_files -tb [file join $src_dir kp_hls_tb.cpp] -cflags "-DVECTORS_DIR=$vec_dir"
open_solution -reset "sol_pw3_v2d"
set_part {xc7z020clg400-1}
create_clock -period 10 -name default
set_top kp_hls_pw3_v2
csim_design
csynth_design
exit
