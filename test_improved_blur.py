#!/usr/bin/env python3
"""
Quick test of the improved blur
"""

import tkinter as tk
import win32gui
import win32process
import psutil
from PIL import Image, ImageTk, ImageFilter, ImageGrab
import time

def find_whatsapp_window():
    """Find WhatsApp window"""
    def enum_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            try:
                window_text = win32gui.GetWindowText(hwnd)
                exe_name = ""
                
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    exe_name = process.name().lower()
                except:
                    pass
                
                is_whatsapp = False
                priority = 0
                
                if exe_name == "whatsapp.exe":
                    is_whatsapp = True
                    priority = 100
                elif exe_name == "applicationframehost.exe" and "whatsapp" in window_text.lower():
                    is_whatsapp = True
                    priority = 90
                elif window_text.lower() == "whatsapp" and exe_name not in ["windowsterminal.exe", "explorer.exe", "python.exe", "code.exe"]:
                    is_whatsapp = True
                    priority = 80
                
                if any(keyword in window_text.lower() for keyword in 
                       ["visual studio", "terminal", "explorer", "python", "blur", "cmd"]):
                    is_whatsapp = False
                    priority = 0
                
                if is_whatsapp and priority > 0:
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    if width > 200 and height > 200:
                        windows.append((hwnd, window_text, rect, exe_name, priority))
                    
            except Exception:
                pass
        return True
    
    windows = []
    win32gui.EnumWindows(enum_callback, windows)
    if windows:
        windows.sort(key=lambda w: w[4], reverse=True)
        best = windows[0]
        return best[0], best[2], best[1]  # hwnd, rect, title
    return None, None, None

def test_improved_blur():
    """Test the improved blur with better intensity and tracking"""
    print("🧪 Testing Improved Blur (Higher Intensity + Position Tracking)")
    print("=" * 60)
    
    # Find WhatsApp
    hwnd, rect, title = find_whatsapp_window()
    if not hwnd:
        print("❌ No WhatsApp window found")
        return
    
    print(f"✅ Found WhatsApp: '{title}'")
    print(f"   Position: {rect}")
    
    root = tk.Tk()
    root.withdraw()
    
    blur_window = None
    
    def create_blur():
        nonlocal blur_window
        
        try:
            # Take screenshot
            screenshot = ImageGrab.grab(bbox=rect)
            
            # Apply STRONGER blur (radius=25 instead of 12)
            blurred = screenshot.filter(ImageFilter.GaussianBlur(radius=25))
            
            # Add privacy overlay
            overlay = Image.new('RGBA', blurred.size, (220, 220, 220, 80))
            result = Image.alpha_composite(blurred.convert('RGBA'), overlay)
            
            # Create blur window
            blur_window = tk.Toplevel(root)
            blur_window.title("Improved Blur Test")
            blur_window.geometry(f"{rect[2]-rect[0]}x{rect[3]-rect[1]}+{rect[0]}+{rect[1]}")
            blur_window.overrideredirect(True)
            blur_window.attributes('-topmost', True)
            blur_window.attributes('-alpha', 0.95)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(result)
            
            # Create label
            label = tk.Label(blur_window, image=photo)
            label.image = photo
            label.pack()
            
            print("✅ Improved blur created!")
            print("🔍 Notice the much stronger blur effect!")
            print("📍 Position tracking test:")
            
            return blur_window
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def update_position():
        """Simulate position tracking"""
        if blur_window:
            try:
                # Get current WhatsApp position
                current_rect = win32gui.GetWindowRect(hwnd)
                if current_rect != rect:
                    x, y, x2, y2 = current_rect
                    blur_window.geometry(f"{x2-x}x{y2-y}+{x}+{y}")
                    print(f"📍 Position updated: {current_rect}")
                
                # Schedule next update
                root.after(500, update_position)  # Update every 500ms
                
            except:
                pass  # Window might be closed
    
    # Create the blur
    blur_window = create_blur()
    
    if blur_window:
        # Start position tracking
        root.after(500, update_position)
        
        # Auto-close after 10 seconds
        def auto_close():
            print("⏰ Test complete - closing blur")
            if blur_window:
                blur_window.destroy()
            root.quit()
        
        root.after(10000, auto_close)
        
        print("🎯 Test running for 10 seconds...")
        print("💡 Try moving WhatsApp window to see position tracking!")
        
        root.mainloop()
    
    root.destroy()

if __name__ == "__main__":
    test_improved_blur()
