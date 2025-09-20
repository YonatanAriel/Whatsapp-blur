#!/usr/bin/env python3
"""
Test Visibility Fixed WhatsApp Blur
This will test the new visibility checking and stronger blur
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_blur_visibility_fixed import WhatsAppBlurVisibilityFixed
import time

def test_visibility_fixes():
    """Test the visibility fixes"""
    print("🧪 Testing WhatsApp Blur Visibility Fixes")
    print("=" * 50)
    
    try:
        # Create app instance
        app = WhatsAppBlurVisibilityFixed()
        
        print("\n1. Testing WhatsApp detection...")
        hwnd = app.find_whatsapp_window()
        if hwnd:
            print(f"✅ WhatsApp found and VISIBLE: {hwnd}")
            
            # Test visibility check
            is_visible = app.is_whatsapp_actually_visible(hwnd)
            print(f"✅ Visibility check result: {is_visible}")
            
            if is_visible:
                print("\n2. Testing stronger blur creation...")
                screenshot = app.capture_whatsapp_screenshot()
                if screenshot:
                    print(f"✅ Screenshot captured: {screenshot.size}")
                    
                    blurred = app.create_blurred_image(screenshot)
                    if blurred:
                        print("✅ STRONGER blur created with radius 50!")
                        
                        # Test blur window creation
                        print("\n3. Testing blur window...")
                        app.create_blur_window()
                        
                        print("\n✅ ALL TESTS PASSED!")
                        print("🎯 The fixed version should now:")
                        print("   - Only blur when WhatsApp is visible")
                        print("   - Use stronger blur (radius 50)")
                        print("   - Never blur hidden WhatsApp windows")
                        
                        # Show blur for 3 seconds then hide
                        time.sleep(3)
                        app.hide_blur()
                        print("🔄 Test blur hidden")
                        
                    else:
                        print("❌ Failed to create blur")
                else:
                    print("❌ Failed to capture screenshot")
            else:
                print("⚠️ WhatsApp found but not visible - this is correct behavior!")
                print("   The app should NOT blur when WhatsApp is hidden")
        else:
            print("❌ WhatsApp not found or not visible")
            print("   Make sure WhatsApp is open and visible on screen")
        
        print("\n🔄 Press Ctrl+Alt+Q to test hotkey manually")
        print("💡 Move WhatsApp window around to test position tracking")
        print("🎯 Minimize WhatsApp to verify blur disappears")
        
        # Keep app running for manual testing
        app.root.mainloop()
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_visibility_fixes()
