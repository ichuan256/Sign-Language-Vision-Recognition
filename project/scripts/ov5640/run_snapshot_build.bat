@echo off
setlocal
set "REPO=%~dp0../../.."
set "XPR=%~1"
if not defined XPR set "XPR=%REPO%/project/_tmp/ov5640_snapshot_20261027_v3/vivado/snapshot.xpr"
if not exist "%XPR%" (echo Snapshot project not found: "%XPR%" & exit /b 2)
call "C:/AMDDesignTools/Vivado/2024.1/bin/vivado.bat" -mode batch -source "%REPO%/project/fpga/scripts/ov5640_snapshot_build.tcl" -tclargs "%XPR%" "%REPO%/project/analysis/ov5640_snapshot_20261027/build"
exit /b %errorlevel%
