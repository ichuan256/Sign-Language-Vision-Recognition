@echo off
REM run_w6_bitgen.bat - standalone bitgen from routed checkpoint, no pause
set PROCESSOR_ARCHITECTURE=AMD64
set PROCESSOR_ARCHITEW6432=AMD64
cd /d F:\PLD\pld-sign-glove\fpga\scripts
call "F:\APP\Xilinx\Vivado\2024.1\bin\vivado.bat" -mode batch -source w6_bitgen_only.tcl -journal w6_bitgen.jou -log w6_bitgen.log > bitgen_stdout.txt 2>&1
echo VIVADO_EXIT=%ERRORLEVEL% >> bitgen_stdout.txt
