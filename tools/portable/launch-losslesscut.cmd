@echo off
rem Launch the workspace-local portable LosslessCut.
rem Usage:  launch-losslesscut.cmd [media files ...]
rem From repo root: tools\portable\launch-losslesscut.cmd "video\raw\BV1Hs411E7aP\BV1Hs411E7aP_p01.mp4"

setlocal
set "LLC=%~dp0losslesscut\LosslessCut.exe"

if not exist "%LLC%" (
  echo [ERROR] LosslessCut.exe not found at:
  echo         %LLC%
  exit /b 1
)

start "" "%LLC%" %*
endlocal
