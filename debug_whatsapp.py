#!/usr/bin/env python3
"""
Debug WhatsApp Window Detection
"""

import win32gui
import win32process
import psutil
import sys

def check_whatsapp_windows():
    """Check all WhatsApp windows and their properties"""
    print("🔍 Checking for WhatsApp windows...")
    print("=" * 50)
    
    def enum_window_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if 'whatsapp' in title.lower() or 'WhatsApp' in title:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    rect = win32gui.GetWindowRect(hwnd)
                    print(f'✅ Found: "{title}"')
                    print(f'   HWND: {hwnd}')
                    print(f'   PID: {pid}')
                    print(f'   Process: {process.name()}')
                    print(f'   Window Rect: {rect}')
                    print(f'   Size: {rect[2]-rect[0]}x{rect[3]-rect[1]}')
                    
                    # Check if window is minimized
                    if win32gui.IsIconic(hwnd):
                        print(f'   ⚠️ Window is minimized!')
                    
                    print('---')
                    return True
                except Exception as e:
                    print(f'   ❌ Error getting process info: {e}')
                    return False
        return False

    windows = []
    win32gui.EnumWindows(enum_window_callback, windows)
    
    print("\n🔍 Checking WhatsApp processes...")
    whatsapp_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if 'whatsapp' in proc.info['name'].lower():
                whatsapp_processes.append(proc)
                print(f"✅ Process: {proc.info['name']} (PID: {proc.info['pid']})")
        except:
            pass
    
    if not whatsapp_processes:
        print("❌ No WhatsApp processes found!")
        return False
    
    return True

def test_screenshot():
    """Test screenshot capability"""
    print("\n🧪 Testing screenshot capability...")
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        print(f"✅ Screenshot successful! Size: {screenshot.size}")
        return True
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return False

def main():
    print("🔧 WhatsApp Blur - Debug Tool")
    print("=" * 40)
    
    # Test screenshot first
    if not test_screenshot():
        print("\n❌ Screenshot capability failed - check privacy permissions!")
        sys.exit(1)
    
    # Check WhatsApp windows
    if not check_whatsapp_windows():
        print("\n❌ No WhatsApp windows found - make sure WhatsApp is open!")
        sys.exit(1)
    
    print("\n🎯 Debug complete!")
    print("If windows are found but blur isn't working, the issue might be:")
    print("1. Multiple WhatsApp windows causing conflicts")
    print("2. Window is minimized or hidden")
    print("3. DPI scaling issues")
    print("4. Blur overlay not being created properly")

if __name__ == "__main__":
    main()
