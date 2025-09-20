@echo off
echo 🔄 Running WhatsApp Blur Auto-Updater with Admin Rights
echo ==================================================

cd /d "%~dp0"
python auto_update.py

echo.
echo ✅ Admin update completed!
pause
