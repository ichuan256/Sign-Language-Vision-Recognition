@echo off
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
start /wait /b cmd /d /c "F:\APP\Xilinx\Vitis_HLS\2024.1\bin\vitis_hls.bat -f build_csim.tcl > start_out.txt 2>&1"
echo AFTER_START
