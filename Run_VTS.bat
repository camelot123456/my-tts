@echo off
title my_VTS - Video to Script and Subtitles
cd /d "%~dp0"
python vts_gui.py
if %errorlevel% neq 0 (
    echo.
    echo [!] An error occurred while launching the VTS application.
    pause
)
