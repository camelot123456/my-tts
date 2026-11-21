@echo off
title my_VTS - Video sang Kich Ban va Phu De
cd /d "%~dp0"
python vts_gui.py
if %errorlevel% neq 0 (
    echo.
    echo [!] Da xay ra loi khi khoi chay ung dung VTS.
    pause
)
