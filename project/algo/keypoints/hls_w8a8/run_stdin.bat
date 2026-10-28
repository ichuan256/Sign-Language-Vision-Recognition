@echo off
set PATH=C:\Windows\System32;C:\Windows;F:\APP\Xilinx\Vitis_HLS\2024.1\bin;F:\APP\Xilinx\Vitis\2024.1\lib\win64.o;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin\server;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin
set RDI_DATADIR=F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8\data
set TCL_LIBRARY=F:\APP\Xilinx\Vitis\2024.1\tps\tcl\tcl8.6
set RDI_PROG=vitis_hls
set HOME=%USERPROFILE%
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
type build_csim.tcl | F:\APP\Xilinx\Vitis_HLS\2024.1\bin\unwrapped\win64.o\vitis_hls.exe -exec vitis_hls -mode tcl
