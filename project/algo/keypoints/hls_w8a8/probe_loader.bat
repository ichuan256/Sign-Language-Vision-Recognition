@echo off
set ROOT=F:\APP\Xilinx\Vitis_HLS\2024.1\bin
set PATH=%ROOT%;%ROOT%\..\tps\win64\msys64\usr\bin;%ROOT%\..\tps\win64\msys64\mingw64\bin;%PATH%
call %ROOT%\setupEnv.bat
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
%ROOT%\loader.bat -exec vitis_hls -version
echo TOOL_RC=%ERRORLEVEL%
