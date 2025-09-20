#!/usr/bin/env python3
"""
WhatsApp Blur - Final Test & Launch
Complete test and launch script
"""

import sys
import os
from pathlib import Path
import subprocess
import time

def test_screenshot_capability():
    """Test if we can take screenshots"""
    print("🧪 Testing screenshot capability...")
    
    try:
        from PIL import ImageGrab
        test_img = ImageGrab.grab(bbox=(0, 0, 100, 100))
        if test_img and test_img.size == (100, 100):
            print("✅ Screenshot test PASSED!")
            return True
        else:
            print("❌ Screenshot test failed - invalid image")
            return False
    except Exception as e:
        print(f"❌ Screenshot test failed: {e}")
        return False

def check_whatsapp_running():
    """Check if WhatsApp is running"""
    print("🔍 Checking for WhatsApp...")
    
    try:
        import psutil
        whatsapp_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if 'whatsapp' in proc.info['name'].lower():
                    whatsapp_processes.append(proc.info)
            except:
                pass
        
        if whatsapp_processes:
            print("✅ WhatsApp processes found:")
            for proc in whatsapp_processes:
                print(f"   - {proc['name']} (PID: {proc['pid']})")
            return True
        else:
            print("⚠️ No WhatsApp processes found")
            print("   Please start WhatsApp Desktop first")
            return False
            
    except Exception as e:
        print(f"❌ Error checking WhatsApp: {e}")
        return False

def launch_whatsapp_blur():
    """Launch the WhatsApp Blur app"""
    print("🚀 Launching WhatsApp Blur...")
    
    app_path = Path("C:/WhatsAppBlur/whatsapp_blur.py")
    bat_path = Path("C:/WhatsAppBlur/WhatsAppBlur.bat")
    
    if bat_path.exists():
        print(f"✅ Using batch file: {bat_path}")
        try:
            subprocess.Popen(str(bat_path), cwd=app_path.parent)
            return True
        except Exception as e:
            print(f"❌ Failed to launch via batch: {e}")
    
    if app_path.exists():
        print(f"✅ Using Python script: {app_path}")
        try:
            subprocess.Popen([sys.executable, str(app_path)], cwd=app_path.parent)
            return True
        except Exception as e:
            print(f"❌ Failed to launch Python script: {e}")
    
    print("❌ Could not find WhatsApp Blur executable")
    return False

def show_usage_instructions():
    """Show how to use the app"""
    print("\n" + "=" * 50)
    print("🎉 WhatsApp Blur - READY TO USE!")
    print("=" * 50)
    print()
    print("🎮 HOW TO USE:")
    print("1. ✅ App is now running in system tray (blue icon)")
    print("2. ✅ Press Ctrl+Alt+Q to toggle blur on/off")
    print("3. ✅ Hover over blur to temporarily reveal content")
    print("4. ✅ Right-click tray icon for options")
    print()
    print("🔧 SHORTCUTS:")
    print("   Ctrl+Alt+Q  = Toggle blur on/off")
    print("   Hover       = Temporarily show content")
    print("   Tray Menu   = Access all options")
    print()
    print("🐛 TROUBLESHOOTING:")
    print("   • If no blur appears: Check WhatsApp is open")
    print("   • If wrong window: Close other apps with 'WhatsApp' in name")
    print("   • If permissions fail: Run grant_permissions.py as admin")
    print()
    print("🎯 The app will auto-start with Windows!")
    print("   Just press Ctrl+Alt+Q whenever you need privacy! 🔒")

def main():
    """Main test and launch function"""
    print("🔧 WhatsApp Blur - Final Test & Launch")
    print("=" * 45)
    
    # Test 1: Screenshot capability
    screenshot_ok = test_screenshot_capability()
    
    # Test 2: WhatsApp detection
    whatsapp_ok = check_whatsapp_running()
    
    print("\n📋 TEST RESULTS:")
    print(f"   Screenshot Capability: {'✅ PASS' if screenshot_ok else '❌ FAIL'}")
    print(f"   WhatsApp Detection:    {'✅ PASS' if whatsapp_ok else '⚠️ WARNING'}")
    
    if not screenshot_ok:
        print("\n❌ SCREENSHOT PERMISSIONS NEEDED!")
        print("Please run: python grant_permissions.py")
        print("OR manually enable in Settings > Privacy & security > Screenshots and apps")
        return
    
    if not whatsapp_ok:
        print("\n⚠️ WhatsApp not detected, but app will work when you open it")
    
    # Launch the app
    print(f"\n🚀 LAUNCHING...")
    if launch_whatsapp_blur():
        print("✅ WhatsApp Blur started successfully!")
        
        # Wait a moment for app to initialize
        time.sleep(2)
        
        # Show instructions
        show_usage_instructions()
    else:
        print("❌ Failed to launch WhatsApp Blur")
        print("Try running manually: C:\\WhatsAppBlur\\WhatsAppBlur.bat")

if __name__ == "__main__":
    main()
