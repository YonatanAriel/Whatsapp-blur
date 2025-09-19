@echo off
title WhatsApp Blur Launcher

echo Starting WhatsApp Blur...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import win32gui, pystray, keyboard" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Run the application
echo Starting WhatsApp Blur application...
python whatsapp_blur.py

pause