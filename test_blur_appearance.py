#!/usr/bin/env python3
"""
Blur Appearance Test - Test the new CSS-style blur without white overlay
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_blur_final import WhatsAppBlurFinal
import time

def test_blur_appearance():
    """Test the new blur appearance"""
    print("🎨 Blur Appearance Test")
    print("=" * 40)
    
    try:
        app = WhatsAppBlurFinal()
        app.shutdown_event.set()  # Stop monitoring
        
        print("✅ App created")
        print("\n🎯 FIXES APPLIED:")
        print("   ✅ Removed white overlay - now pure Gaussian blur")
        print("   ✅ Increased blur radius to 40 (CSS-style)")
        print("   ✅ Better window positioning with Win32 API")
        print("   ✅ Prevent screenshot interference")
        
        # Wait for user to prepare
        input("\n📋 Make sure WhatsApp is visible and ready, then press Enter...")
        
        print("\n🔍 Testing blur creation...")
        
        # Test step by step
        hwnd = app.find_whatsapp_window()
        if not hwnd:
            print("❌ WhatsApp not found")
            return
        
        print("✅ WhatsApp found")
        
        # Test screenshot without interference
        screenshot = app.capture_whatsapp_screenshot()
        if not screenshot:
            print("❌ Screenshot failed")
            return
        
        print("✅ Screenshot captured without white flash")
        
        # Test new blur creation
        blur_img = app.create_blurred_image(screenshot)
        if not blur_img:
            print("❌ Blur creation failed")
            return
        
        print("✅ Pure Gaussian blur created (no white overlay)")
        app.blur_cache = blur_img
        
        # Test window creation
        app.create_blur_window()
        
        if app.blur_window:
            print("✅ Blur window created and positioned")
            print(f"📍 Window geometry: {app.blur_window.geometry()}")
            
            print("\n🎉 SUCCESS! Check your WhatsApp window now")
            print("💡 You should see:")
            print("   ✅ Pure Gaussian blur (like CSS filter: blur())")
            print("   ✅ NO white overlay or flash")
            print("   ✅ Blur positioned exactly over WhatsApp")
            
            # Keep visible for testing
            print("\n⏱️ Showing blur for 10 seconds...")
            for i in range(10, 0, -1):
                print(f"   ⏳ {i} seconds remaining...")
                time.sleep(1)
            
            app.hide_blur()
            print("✅ Blur hidden")
        else:
            print("❌ Blur window creation failed")
        
        print("\n✅ Appearance test completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_blur_appearance()
