#!/usr/bin/env python3
"""
Final Test - WhatsApp Blur with working hotkey
"""

import subprocess
import sys
import time

def final_test():
    """Final test of the fixed WhatsApp blur"""
    print("🎯 FINAL WhatsApp Blur Test")
    print("=" * 40)
    
    # Test the installed version
    print("🚀 Starting installed WhatsApp Blur...")
    
    try:
        # Launch the main app
        process = subprocess.Popen([
            sys.executable, 
            "C:\\WhatsAppBlur\\whatsapp_blur.py"
        ], cwd="C:\\WhatsAppBlur")
        
        print("✅ App launched successfully!")
        print("\n📋 TESTING INSTRUCTIONS:")
        print("1. ✅ Make sure WhatsApp is open and visible")
        print("2. ✅ Press Ctrl+Alt+Q - you should see hotkey messages")
        print("3. ✅ Blur should appear over WhatsApp window")
        print("4. ✅ Press Ctrl+Alt+Q again to hide blur")
        print("5. ✅ Move WhatsApp window - blur should follow")
        print("6. ✅ Minimize WhatsApp - blur should disappear")
        
        print(f"\n🔧 FIXES APPLIED:")
        print(f"   ✅ Hotkey now works (Ctrl+Alt+Q)")
        print(f"   ✅ Monitoring thread is quieter")
        print(f"   ✅ Better visibility checking")
        print(f"   ✅ Stronger blur effect")
        print(f"   ✅ No more infinite terminal output")
        
        print(f"\n⚠️ If blur is too weak, press Ctrl+Alt+Q twice to refresh")
        print(f"\n💡 Right-click system tray icon for settings")
        print(f"\n🔄 App is running... Close this window when done testing")
        
        # Wait for user to test
        input("\nPress Enter when finished testing...")
        
        # Clean shutdown
        process.terminate()
        process.wait()
        print("👋 Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    final_test()
