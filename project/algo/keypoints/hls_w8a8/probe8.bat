@echo off
call F:\APP\Xilinx\Vitis_HLS\2024.1\settings64.bat >nul 2>&1
call F:\APP\Xilinx\Vitis_HLS\2024.1\bin\setupEnv.bat >nul 2>&1
set PATH=F:\APP\Xilinx\Vitis\2024.1\lib\win64.o;%PATH%
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\loader.bat -exec vitis_hls -version > probe8.txt 2>&1
echo TOOL_RC=%ERRORLEVEL%
type probe8.txt
