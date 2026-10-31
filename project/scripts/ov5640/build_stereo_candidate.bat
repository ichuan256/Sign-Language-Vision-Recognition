@echo off
cd /d "%~dp0\..\..\.."
if "%~1"=="" exit /b 2
if "%~2"=="" exit /b 2
call "F:\APP\Xilinx\Vivado\2024.1\bin\vivado.bat" -mode batch -notrace -source project/fpga/scripts/ov5640_snapshot_stereo_build.tcl -tclargs "%~1" "%~2"
exit /b %errorlevel%
