@echo off
call F:\APP\Xilinx\Vitis_HLS\2024.1\settings64.bat >nul 2>&1
set PATH=F:\APP\Xilinx\Vitis\2024.1\lib\win64.o;%PATH%
set RDI_DATADIR=F:\APP\Xilinx\Vitis_HLS\2024.1\data
set TCL_LIBRARY=F:\APP\Xilinx\Vitis\2024.1\tps\tcl\tcl8.6
set TK_LIBRARY=F:\APP\Xilinx\Vitis\2024.1\tps\tcl\tk8.6
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\unwrapped\win64.o\vitis_hls.exe -version > probe7.txt 2>&1
echo TOOL_RC=%ERRORLEVEL%
type probe7.txt
