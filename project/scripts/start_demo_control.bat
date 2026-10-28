@echo off
cd /d "%~dp0\..\.."
"F:\PLD\.venv-vision\Scripts\python.exe" -X utf8 project\scripts\demo_control.py
if errorlevel 1 pause
