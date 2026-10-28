@echo off
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
call F:\APP\Xilinx\Vitis_HLS\2024.1\bin\vitis_hls.bat -f build_csim.tcl > csim_run.log 2>&1
echo EXITCODE=%ERRORLEVEL%
type csim_run.log
