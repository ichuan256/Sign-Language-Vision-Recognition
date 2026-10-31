@echo off
cd /d "%~dp0\..\..\.."
call "F:\APP\Xilinx\Vivado\2024.1\bin\vivado.bat" -mode batch -notrace -source project/fpga/scripts/ov5640_snapshot_hdmi_audio_prepare.tcl -log project/_tmp/av_prepare_20261031.log -journal project/_tmp/av_prepare_20261031.jou
exit /b %errorlevel%
