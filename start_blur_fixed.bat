@echo off
title WhatsApp Blur - Auto Start

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    timeout /t 5
    exit /b 1
)

REM Run the fixed WhatsApp Blur application
echo Starting WhatsApp Blur (Fixed Version)...
python whatsapp_blur_fixed.py

REM If the script exits, wait before closing
if errorlevel 1 (
    echo Error occurred. Check the application logs.
    timeout /t 10
)
