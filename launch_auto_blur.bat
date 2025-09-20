@echo off
echo.
echo ========================================
echo    WhatsApp Auto-Blur Launcher
echo ========================================
echo.
echo 🚀 Starting WhatsApp Auto-Blur...
echo 📝 Press Ctrl+Alt+Q to toggle auto-blur
echo 🖱️ Hover over blur to reveal content
echo ⚠️ Make sure WhatsApp Desktop is open
echo.

cd /d "%~dp0"
python whatsapp_blur_no_white.py

echo.
echo 👋 WhatsApp Auto-Blur stopped
pause
