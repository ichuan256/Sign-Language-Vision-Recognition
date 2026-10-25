@echo off
REM run_video_hls.bat - build pixel_unpack and color_convert HLS IPs (2026-10-15)
REM Logs go to hls_build.log in each IP directory.
setlocal
where vitis_hls >nul 2>nul
if errorlevel 1 (
    if exist "F:\APP\Xilinx\Vitis_HLS\2024.1\settings64.bat" call "F:\APP\Xilinx\Vitis_HLS\2024.1\settings64.bat"
)
where vitis_hls >nul 2>nul
if errorlevel 1 (
    echo [ERR] vitis_hls not found. Run this from Vitis HLS 2024.1 Command Prompt.
    pause
    exit /b 1
)
for %%I in (pixel_unpack color_convert) do (
    echo ==== Building %%I ====
    pushd "%~dp0%%I"
    call vitis_hls -f script.tcl > hls_build.log 2>&1
    if errorlevel 1 (
        popd
        exit /b 1
    )
    if exist "%%I\solution1\impl\ip\component.xml" (
        echo [OK] %%I exported
    ) else (
        echo [FAIL] %%I - see %%I\hls_build.log
    )
    popd
)
echo ==== DONE. Two [OK] lines expected, then source w6_hdmi_bd.tcl in Vivado ====
pause
