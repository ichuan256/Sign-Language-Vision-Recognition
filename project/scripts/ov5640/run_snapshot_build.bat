@echo off
setlocal
set "REPO=%~dp0../../.."
set "XPR=%~1"
if not defined XPR (echo Explicit prepared project path required & exit /b 2)
if not exist "%XPR%" (echo Snapshot project not found: "%XPR%" & exit /b 2)
set "EVIDENCE=%~2"
if not defined EVIDENCE (echo Explicit new evidence directory required & exit /b 2)
call "C:/AMDDesignTools/Vivado/2024.1/bin/vivado.bat" -mode batch -source "%REPO%/project/fpga/scripts/ov5640_snapshot_build.tcl" -tclargs "%XPR%" "%EVIDENCE%"
exit /b %errorlevel%
