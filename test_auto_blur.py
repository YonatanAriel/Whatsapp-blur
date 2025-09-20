#!/usr/bin/env python3
"""
Simple Test for Auto-Blur Functionality
Tests if blur automatically appears when WhatsApp becomes visible
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_blur_visibility_fixed import WhatsAppBlurVisibilityFixed
import time

def test_auto_blur():
    """Test automatic blur when WhatsApp becomes visible"""
    print("🧪 Testing AUTO-BLUR when WhatsApp becomes visible")
    print("=" * 55)
    
    try:
        # Create app instance
        app = WhatsAppBlurVisibilityFixed()
        
        print(f"\n✅ App started with hotkey: {app.toggle_key}")
        print("\n🎯 TEST INSTRUCTIONS:")
        print("1. Make sure WhatsApp is open but minimized/hidden")
        print("2. Use Alt+Tab to bring WhatsApp to foreground")
        print("3. Blur should AUTOMATICALLY appear")
        print("4. Press Ctrl+Alt+Q to toggle blur manually")
        print("5. Minimize WhatsApp - blur should disappear")
        print("\n📝 Watch the console for status messages...")
        print("🔄 App is now monitoring for WhatsApp visibility changes")
        
        # Run the app - it will auto-blur when WhatsApp becomes visible
        app.root.mainloop()
        
    except KeyboardInterrupt:
        print("\n👋 Test stopped by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auto_blur()
