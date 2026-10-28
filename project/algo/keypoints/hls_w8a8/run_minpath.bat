@echo off
set PATH=C:\Windows\System32;C:\Windows;F:\APP\Xilinx\Vitis_HLS\2024.1\bin;F:\APP\Xilinx\Vitis\2024.1\lib\win64.o;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin\server;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\msys64\usr\bin
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\vitis_hls.bat -f build_csim.tcl
