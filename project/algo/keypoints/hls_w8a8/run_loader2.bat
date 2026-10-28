@echo off
call F:\APP\Xilinx\Vitis_HLS\2024.1\settings64.bat >nul 2>&1
set PATH=F:\APP\Xilinx\Vitis\2024.1\lib\win64.o;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin\server;F:\APP\Xilinx\Vitis_HLS\2024.1\tps\win64\jre11.0.16_1\bin;%PATH%
set HOME=%USERPROFILE%
call F:\APP\Xilinx\Vitis_HLS\2024.1\bin\setupEnv.bat
echo SETUPENV_RC=%ERRORLEVEL%
set RDI_PROG=vitis_hls
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\loader.bat -exec vitis_hls -f build_csim.tcl > loader_run.log 2>&1
echo LOADER_RC=%ERRORLEVEL%
