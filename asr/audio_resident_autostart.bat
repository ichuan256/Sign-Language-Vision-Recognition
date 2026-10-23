@echo off
rem Autostart entry: resident audio service (ASR model preloaded, waits for board BTN0).
rem Install: copy this file into shell:startup
cd /d "F:\PLD_new\Sign-Language-Vision-Recognition"
start "audio_resident" /min cmd /c "F:\PLD\.venv-audio\Scripts\python.exe -X utf8 asr\audio_resident.py --model F:\PLD\asr_test\sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23 > _tmp\audio_resident_console.log 2>&1"
