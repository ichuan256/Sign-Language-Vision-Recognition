@echo off
set PROCESSOR_ARCHITECTURE=AMD64
set PROCESSOR_ARCHITEW6432=AMD64
cd /d "%~dp0"
call "F:\APP\Xilinx\Vivado\2024.1\bin\vivado.bat" -mode batch -source w6_resume_build.tcl -journal w6_resume.jou -log w6_resume.log > resume_stdout.txt 2>&1
echo VIVADO_EXIT=%ERRORLEVEL% >> resume_stdout.txt
