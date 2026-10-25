@echo off
setlocal
set PROCESSOR_ARCHITECTURE=AMD64
set PROCESSOR_ARCHITEW6432=AMD64
cd /d "%~dp0"
if not defined VIVADO_BAT set "VIVADO_BAT=F:\APP\Xilinx\Vivado\2024.1\bin\vivado.bat"
call "%VIVADO_BAT%" -mode batch -source fixup_rtl.tcl
exit /b %ERRORLEVEL%
