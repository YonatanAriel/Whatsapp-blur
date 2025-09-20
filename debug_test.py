#!/usr/bin/env python3
"""
Debug Test - Find out exactly what's happening with blur creation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_blur_final import WhatsAppBlurFinal
import time

def debug_test():
    """Debug the blur creation issue"""
    print("🔍 DEBUG: WhatsApp Blur Creation")
    print("=" * 40)
    
    try:
        app = WhatsAppBlurFinal()
        
        # Stop monitoring to prevent interference
        app.shutdown_event.set()
        time.sleep(0.5)
        
        print("✅ App created")
        print(f"🎯 is_enabled: {app.is_enabled}")
        print(f"🎯 is_blurred: {app.is_blurred}")
        
        # Test manual blur ONE step at a time
        print("\n🔍 Step 1: Find WhatsApp...")
        hwnd = app.find_whatsapp_window()
        if hwnd:
            print(f"✅ WhatsApp found: {hwnd}")
            print(f"📍 WhatsApp rect: {app.whatsapp_rect}")
        else:
            print("❌ WhatsApp not found")
            return
        
        print("\n🔍 Step 2: Capture screenshot...")
        screenshot = app.capture_whatsapp_screenshot()
        if screenshot:
            print(f"✅ Screenshot captured: {screenshot.size}")
        else:
            print("❌ Screenshot failed")
            return
        
        print("\n🔍 Step 3: Create blur image...")
        blur_img = app.create_blurred_image(screenshot)
        if blur_img:
            print(f"✅ Blur image created: {blur_img.size}")
            app.blur_cache = blur_img
        else:
            print("❌ Blur image creation failed")
            return
        
        print("\n🔍 Step 4: Create blur window...")
        app.create_blur_window()
        
        if app.blur_window:
            print("✅ Blur window object exists")
            try:
                exists = app.blur_window.winfo_exists()
                print(f"✅ Window exists check: {exists}")
                visible = app.blur_window.winfo_viewable()
                print(f"✅ Window visible check: {visible}")
                geometry = app.blur_window.geometry()
                print(f"✅ Window geometry: {geometry}")
            except Exception as e:
                print(f"❌ Window check error: {e}")
        else:
            print("❌ No blur window object created")
        
        print(f"\n🎯 Final state:")
        print(f"   is_blurred: {app.is_blurred}")
        print(f"   blur_window exists: {app.blur_window is not None}")
        
        if app.blur_window:
            print("\n🎉 SUCCESS! Blur window should be visible")
            print("💡 Look for a gray overlay on your WhatsApp window")
            
            # Keep it visible for a few seconds
            print("⏱️ Showing blur for 5 seconds...")
            time.sleep(5)
            
            print("❌ Hiding blur...")
            app.hide_blur()
        
        print("\n✅ Debug test completed")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_test()
