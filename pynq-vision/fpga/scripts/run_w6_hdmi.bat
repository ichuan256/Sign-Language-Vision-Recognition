@echo off
setlocal
set PROCESSOR_ARCHITECTURE=AMD64
set PROCESSOR_ARCHITEW6432=AMD64
cd /d "%~dp0"
if not defined VIVADO_BAT set "VIVADO_BAT=vivado.bat"
call "%VIVADO_BAT%" -mode batch -source w6_hdmi_batch.tcl
exit /b %ERRORLEVEL%
