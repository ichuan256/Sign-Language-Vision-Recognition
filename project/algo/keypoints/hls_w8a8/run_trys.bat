@echo off
call F:\APP\Xilinx\Vitis_HLS\2024.1\settings64.bat >nul 2>&1
set PATH=F:\APP\Xilinx\Vitis\2024.1\lib\win64.o;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin\server;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin;%PATH%
set RDI_DATADIR=F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8\data
set TCL_LIBRARY=F:\APP\Xilinx\Vitis\2024.1\tps\tcl\tcl8.6
set RDI_PROG=vitis_hls
set HOME=%USERPROFILE%
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
echo === TRY1 -mode tcl -f ===
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\unwrapped\win64.o\vitis_hls.exe -mode tcl -f build_csim.tcl 2>&1 | findstr /C:"source" /C:"ERROR" /C:"HLS_LAYER" /C:"hls_csim"
echo === TRY2 -mode batch -source ===
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\unwrapped\win64.o\vitis_hls.exe -mode batch -source build_csim.tcl 2>&1 | findstr /C:"source" /C:"ERROR" /C:"HLS_LAYER" /C:"hls_csim"
echo === TRY3 -source only ===
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\unwrapped\win64.o\vitis_hls.exe -source build_csim.tcl 2>&1 | findstr /C:"source" /C:"ERROR" /C:"HLS_LAYER" /C:"hls_csim"
