@echo off
call F:\APP\Xilinx\Vitis_HLS\2024.1\settings64.bat >nul 2>&1
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\unwrapped\win64.o\vitis_hls.exe -version > probe4.txt 2>&1
echo TOOL_RC=%ERRORLEVEL%
type probe4.txt
