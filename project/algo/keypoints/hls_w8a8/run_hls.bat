@echo off
rem Vitis HLS 2024.1 launcher: official wrapper + the two PATH additions this
rem machine needs (Vitis lib for xv_*.dll, bundled JRE for jvm.dll).
rem NOTE: loader.bat ends with a bare `exit`, so the wrapper must be the last
rem command in this bat. Usage: run_hls.bat <tcl absolute path>
call F:\APP\Xilinx\Vitis_HLS\2024.1\settings64.bat >nul 2>&1
set PATH=F:\APP\Xilinx\Vitis\2024.1\lib\win64.o;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin\server;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin;%PATH%
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\vitis_hls.bat -f %1 > wrapper_out.txt 2>&1
