@echo off
rem Launch the workspace-local portable LosslessCut.
rem Usage:  launch-losslesscut.cmd [media files ...]
rem Example: launch-losslesscut.cmd "..\video\BV1Hs411E7aP_p01.mp4"

setlocal
set "LLC=%~dp0losslesscut\LosslessCut.exe"

if not exist "%LLC%" (
  echo [ERROR] LosslessCut.exe not found at:
  echo         %LLC%
  exit /b 1
)

start "" "%LLC%" %*
endlocal
