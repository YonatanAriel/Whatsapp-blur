#!/usr/bin/env python3
"""
Simple WhatsApp Blur Test - No infinite monitoring loops
Tests ONLY the hotkey and blur functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_blur_final import WhatsAppBlurFinal
import time

def simple_test():
    """Simple test without infinite monitoring output"""
    print("🧪 Simple WhatsApp Blur Test")
    print("=" * 40)
    
    try:
        # Create app but stop the monitoring to prevent spam
        app = WhatsAppBlurFinal()
        
        # Stop the monitoring thread to prevent infinite output
        print("🛑 Stopping monitoring thread to prevent spam...")
        app.shutdown_event.set()
        
        print(f"\n✅ App created successfully")
        print(f"🎯 Hotkey: {app.toggle_key}")
        print(f"📱 Blur enabled: {app.is_enabled}")
        
        # Test manual blur
        print("\n🔍 Testing manual blur activation...")
        app.show_blur()
        
        print(f"\n🎯 TEST COMPLETED!")
        print(f"📋 Now manually test:")
        print(f"   1. Make sure WhatsApp is visible on screen")
        print(f"   2. Press {app.toggle_key} to toggle blur")
        print(f"   3. The blur should appear/disappear")
        print(f"\n⚠️ If hotkey doesn't work, check:")
        print(f"   - WhatsApp is actually visible (not minimized)")
        print(f"   - No other app is using {app.toggle_key}")
        print(f"   - Try running as administrator")
        
        # Keep app running for manual testing (no monitoring spam)
        print(f"\n🔄 App running... Press Ctrl+C to exit")
        try:
            while True:
                app.root.update()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            app.quit_application()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()
