#!/usr/bin/env python3
"""
WhatsApp Blur - Auto Startup Setup
Configures the app to start automatically when Windows boots
"""

import os
import shutil
import sys
from pathlib import Path
import subprocess

def setup_auto_startup():
    """Configure WhatsApp Blur to start automatically on Windows boot"""
    
    print("🔄 Setting up auto-startup for WhatsApp Blur...")
    print("=" * 50)
    
    try:
        # Get the startup folder path
        startup_folder = os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup")
        
        # Create silent VBS startup script (no window)
        startup_script_content = '''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """C:\\Users\\yonat\\AppData\\Local\\Programs\\Python\\Python313\\pythonw.exe"" ""C:\\Users\\Public\\WhatsApp Blur\\whatsapp_blur.py""", 0, False
'''
        
        startup_script_path = os.path.join(startup_folder, "WhatsApp_Blur_Silent.vbs")
        
        # Write the startup script
        with open(startup_script_path, 'w') as f:
            f.write(startup_script_content)
        
        print(f"✅ Startup script created: {startup_script_path}")
        
        print("✅ Auto-startup configured via startup folder only (single method to prevent duplicates)")
            
        except Exception as e:
            print(f"⚠️ Registry method failed: {e}")
            print("✅ Startup folder method still active")
        
        print("\n🎉 AUTO-STARTUP CONFIGURED!")
        print("📱 WhatsApp Blur will now start automatically when you boot your laptop")
        print("\n📋 To disable auto-startup:")
        print(f"   1. Delete: {startup_script_path}")
        print("   2. Or go to Task Manager > Startup and disable 'WhatsApp Blur'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up auto-startup: {e}")
        return False

if __name__ == "__main__":
    setup_auto_startup()
    input("\nPress Enter to exit...")
