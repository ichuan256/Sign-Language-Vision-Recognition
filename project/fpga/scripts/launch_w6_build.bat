@echo off
setlocal
set PROCESSOR_ARCHITECTURE=AMD64
set PROCESSOR_ARCHITEW6432=AMD64
cd /d "%~dp0"
set VIVADO_BAT=F:\APP\Xilinx\Vivado\2024.1\bin\vivado.bat
start "w6_build" /min cmd /c "run_w6_hdmi_build.bat > w6_build_console.log 2>&1"
echo BUILD_LAUNCHED
