#!/usr/bin/env python3
"""
Test the exact blur functionality
"""

import tkinter as tk
import win32gui
import win32process
import psutil
from PIL import Image, ImageTk, ImageFilter, ImageGrab
import time

def find_whatsapp_window():
    """Find WhatsApp window using the same logic as the main app"""
    def enum_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            try:
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                exe_name = ""
                
                # Get process name
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    exe_name = process.name().lower()
                except:
                    pass
                
                # PRIORITY DETECTION
                is_whatsapp = False
                priority = 0
                
                # HIGHEST PRIORITY: WhatsApp.exe process
                if exe_name == "whatsapp.exe":
                    is_whatsapp = True
                    priority = 100
                
                # HIGH PRIORITY: ApplicationFrameHost with WhatsApp title (Microsoft Store WhatsApp)
                elif exe_name == "applicationframehost.exe" and "whatsapp" in window_text.lower():
                    is_whatsapp = True
                    priority = 90
                    
                # MEDIUM PRIORITY: Exact WhatsApp title match (but not terminals/browsers)
                elif window_text.lower() == "whatsapp" and exe_name not in ["windowsterminal.exe", "explorer.exe", "python.exe", "code.exe"]:
                    is_whatsapp = True
                    priority = 80
                
                # EXCLUDE known false positives
                if any(keyword in window_text.lower() for keyword in 
                       ["visual studio", "terminal", "explorer", "python", "blur", "cmd"]):
                    is_whatsapp = False
                    priority = 0
                
                if is_whatsapp and priority > 0:
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    # Ignore minimized or tiny windows
                    if width > 200 and height > 200:
                        windows.append((hwnd, window_text, class_name, rect, exe_name, priority))
                    
            except Exception:
                pass
        return True
    
    windows = []
    try:
        win32gui.EnumWindows(enum_callback, windows)
        if windows:
            # Sort by priority (highest first)
            windows.sort(key=lambda w: w[5], reverse=True)
            best = windows[0]
            hwnd, title, class_name, rect, exe_name, priority = best
            print(f"✅ Found WhatsApp: '{title}' (process: {exe_name}, priority: {priority})")
            print(f"   HWND: {hwnd}")
            print(f"   Rect: {rect}")
            print(f"   Size: {rect[2]-rect[0]}x{rect[3]-rect[1]}")
            return hwnd, rect, title
        else:
            print("❌ No WhatsApp window found")
            return None, None, None
    except Exception as e:
        print(f"❌ Error finding WhatsApp: {e}")
        return None, None, None

def test_blur_creation():
    """Test creating a blur overlay"""
    print("🧪 Testing blur overlay creation...")
    
    # Find WhatsApp window
    hwnd, rect, title = find_whatsapp_window()
    if not hwnd:
        print("❌ Cannot test blur - no WhatsApp window found")
        return
    
    try:
        # Take screenshot of the area
        print(f"📸 Taking screenshot of area: {rect}")
        screenshot = ImageGrab.grab(bbox=rect)
        print(f"✅ Screenshot taken: {screenshot.size}")
        
        # Apply blur
        print("🌫️ Applying blur...")
        blurred = screenshot.filter(ImageFilter.GaussianBlur(radius=15))
        print("✅ Blur applied")
        
        # Create tkinter window for blur overlay
        print("🖼️ Creating blur overlay window...")
        blur_window = tk.Toplevel()
        blur_window.title("Blur Test")
        blur_window.geometry(f"{rect[2]-rect[0]}x{rect[3]-rect[1]}+{rect[0]}+{rect[1]}")
        blur_window.overrideredirect(True)
        blur_window.attributes('-topmost', True)
        blur_window.attributes('-alpha', 0.9)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(blurred)
        
        # Create label with blurred image
        label = tk.Label(blur_window, image=photo)
        label.image = photo  # Keep a reference
        label.pack()
        
        print("✅ Blur overlay created!")
        print("🎯 You should see a blurred overlay over WhatsApp")
        print("⏰ Overlay will disappear in 5 seconds...")
        
        # Show for 5 seconds
        blur_window.after(5000, blur_window.destroy)
        blur_window.mainloop()
        
    except Exception as e:
        print(f"❌ Error creating blur: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🧪 WhatsApp Blur - Functionality Test")
    print("=" * 40)
    
    # Create a root window (required for tkinter)
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Test the blur
    test_blur_creation()
    
    root.destroy()

if __name__ == "__main__":
    main()
