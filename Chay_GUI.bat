@echo off
title my_TTS - Text to Speech Converter
cd /d "%~dp0"
python gui.py
if %errorlevel% neq 0 (
    echo.
    echo [!] Co loi xay ra khi khoi chay ung dung.
    pause
)
