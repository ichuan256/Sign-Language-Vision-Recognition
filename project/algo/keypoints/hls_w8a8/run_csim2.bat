@echo off
set ROOT=F:\APP\Xilinx\Vitis_HLS\2024.1\bin
set PATH=%ROOT%;%ROOT%\..\tps\win64\msys64\usr\bin;%ROOT%\..\tps\win64\msys64\mingw64\bin;%PATH%
call %ROOT%\setupEnv.bat
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
%ROOT%\unwrapped\win64.o\vitis_hls.exe -f build_csim.tcl > csim_run.log 2>&1
echo TOOL_RC=%ERRORLEVEL%
type csim_run.log
