@echo off
setlocal
cd /d "%~dp0\.."
set AUDIO_BOARD_SUDO_PASSWORD=xilinx
if not exist "project\_tmp" mkdir "project\_tmp"
start "audio_line" /min cmd /c "F:\PLD\.venv-audio\Scripts\python.exe -X utf8 ASR\run_audio_line.py --model F:\PLD\asr_test\sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23 > project\_tmp\audio_line_console.log 2>&1"
echo AUDIO_LINE_LAUNCHED
