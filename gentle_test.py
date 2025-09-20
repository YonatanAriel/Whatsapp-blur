#!/usr/bin/env python3
"""
Gentle Test - WhatsApp Blur without freezing WhatsApp
"""

import subprocess
import sys
import time

def gentle_test():
    """Test the blur without causing WhatsApp to freeze"""
    print("🌟 GENTLE WhatsApp Blur Test")
    print("=" * 40)
    
    print("⚠️ IMPORTANT: This test is designed to NOT freeze WhatsApp")
    print("   - Uses safe screenshot methods")
    print("   - Adds delays between operations")
    print("   - Validates WhatsApp is responsive")
    
    try:
        # Launch the app normally (not debug mode)
        print("\n🚀 Starting WhatsApp Blur (normal mode)...")
        
        process = subprocess.Popen([
            sys.executable, 
            "whatsapp_blur_final.py"
        ])
        
        print("✅ App launched!")
        print("\n📋 SAFE TESTING STEPS:")
        print("1. ✅ Wait for app to fully start (5 seconds)")
        
        # Wait for app to fully initialize
        for i in range(5, 0, -1):
            print(f"   ⏳ Starting in {i}...")
            time.sleep(1)
        
        print("\n2. ✅ Make sure WhatsApp is fully loaded and responsive")
        print("   - Check that WhatsApp is not showing loading spinner")
        print("   - Make sure you can click and interact with WhatsApp normally")
        
        input("Press Enter when WhatsApp is fully loaded and working...")
        
        print("\n3. ✅ Now press Ctrl+Alt+Q to test blur")
        print("   - The app will wait 2+ seconds between blur attempts")
        print("   - This prevents overwhelming WhatsApp with requests")
        
        print("\n4. ✅ Testing guidance:")
        print("   - Press Ctrl+Alt+Q once and wait for result")
        print("   - If blur appears, press Ctrl+Alt+Q again to hide")
        print("   - Don't press the hotkey rapidly")
        
        print("\n⚠️ If WhatsApp freezes:")
        print("   - Wait 10 seconds for it to recover")
        print("   - If still frozen, restart WhatsApp")
        print("   - The new safety checks should prevent this")
        
        print(f"\n💡 Safety features enabled:")
        print(f"   ✅ 2-second minimum between blur attempts")
        print(f"   ✅ WhatsApp responsiveness checking")
        print(f"   ✅ Gentle screenshot capture")
        print(f"   ✅ Better error handling")
        
        print(f"\n🔄 App is running safely...")
        input("Press Enter when finished testing...")
        
        # Clean shutdown
        process.terminate()
        process.wait()
        print("👋 Test completed safely!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    gentle_test()
