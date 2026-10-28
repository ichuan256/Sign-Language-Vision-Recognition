@echo off
call F:\APP\Xilinx\Vitis_HLS\2024.1\bin\setupEnv.bat
echo SETUP_RC=%ERRORLEVEL%
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\unwrapped\win64.o\vitis_hls.exe -version
echo TOOL_RC=%ERRORLEVEL%
