@echo off
REM run_w6_rebuild.bat - headless rebuild (wrapper fix), no pause; launched detached
set PROCESSOR_ARCHITECTURE=AMD64
set PROCESSOR_ARCHITEW6432=AMD64
cd /d "%~dp0"
call "F:\APP\Xilinx\Vivado\2024.1\bin\vivado.bat" -mode batch -source w6_hdmi_build.tcl -journal w6_build.jou -log w6_build.log > vivado_stdout.txt 2>&1
echo VIVADO_EXIT=%ERRORLEVEL% >> vivado_stdout.txt
