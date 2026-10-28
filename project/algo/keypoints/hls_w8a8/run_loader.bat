@echo off
call F:\APP\Xilinx\Vitis_HLS\2024.1\settings64.bat >nul 2>&1
set PATH=F:\APP\Xilinx\Vitis\2024.1\lib\win64.o;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin\server;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin;%PATH%
set RDI_PROG=vitis_hls
set RDI_BINROOT=F:\APP\Xilinx\Vitis_HLS\2024.1\bin
set HOME=%USERPROFILE%
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
%WINDIR%\System32\cmd.exe /c call "%RDI_BINROOT%\loader.bat" -exec vitis_hls -f build_csim.tcl > loader_out.txt 2>&1
