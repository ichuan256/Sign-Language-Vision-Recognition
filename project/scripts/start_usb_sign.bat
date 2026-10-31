@echo off
cd /d "%~dp0\..\.."
"F:\PLD\.venv-vision\Scripts\python.exe" -X utf8 project\scripts\start_usb_sign.py
if errorlevel 1 pause
