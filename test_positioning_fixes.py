# Test positioning and visibility fixes
import sys
import os
import time

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testing WhatsApp Blur positioning and visibility fixes...")

def test_positioning_and_visibility():
    print("\n=== Testing Positioning and Visibility Fixes ===")
    
    # Import the blur app
    from whatsapp_blur_final import WhatsAppBlurFinal
    
    # Create app instance
    print("📱 Creating WhatsApp Blur app...")
    app = WhatsAppBlurFinal()
    
    print("✅ App created successfully!")
    
    # Test 1: Check if WhatsApp is visible
    print("\n🔍 Test 1: Checking WhatsApp visibility...")
    whatsapp_hwnd = app.find_whatsapp_window()
    if whatsapp_hwnd:
        print(f"✅ WhatsApp found: {whatsapp_hwnd}")
        print(f"📍 Visibility check: {app.is_whatsapp_currently_visible(whatsapp_hwnd)}")
    else:
        print("❌ WhatsApp not found or not visible")
        return
    
    # Test 2: Test blur creation with current positioning
    print("\n🌀 Test 2: Testing blur with current positioning...")
    
    # Enable the app
    app.is_enabled = True
    
    # Try to show blur
    print("🎯 Attempting to show blur...")
    app.show_blur()
    
    if app.is_blurred and app.blur_window:
        print("✅ Blur window created successfully!")
        print(f"📐 Blur window geometry: {app.blur_window.geometry()}")
        
        # Get current WhatsApp position for comparison
        import win32gui
        current_rect = win32gui.GetWindowRect(whatsapp_hwnd)
        print(f"📍 WhatsApp current position: {current_rect}")
        print(f"📍 Cached position: {app.whatsapp_rect}")
        
        # Wait a moment then hide
        print("⏳ Waiting 3 seconds then hiding blur...")
        time.sleep(3)
        
        app.hide_blur()
        print("✅ Blur hidden successfully!")
        
    else:
        print("❌ Blur creation failed")
    
    # Test 3: Test visibility monitoring
    print("\n👀 Test 3: Testing visibility monitoring...")
    print("📝 Now minimize WhatsApp and see if blur is properly hidden...")
    print("📝 Then restore WhatsApp and check if blur positioning is correct...")
    
    # Start monitoring for a short time
    print("⏳ Monitoring for 10 seconds...")
    start_time = time.time()
    while time.time() - start_time < 10:
        app.process_ui_queue()
        time.sleep(0.1)
    
    print("✅ Monitoring test completed!")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    app.shutdown_event.set()
    if app.blur_window:
        app.blur_window.destroy()
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    try:
        test_positioning_and_visibility()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 Test script finished!")
    input("Press Enter to exit...")
