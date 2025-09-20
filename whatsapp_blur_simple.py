#!/usr/bin/env python3
"""
WhatsApp Blur - SIMPLIFIED AUTO-BLUR VERSION
Fixed visibility detection and auto-blur logic
"""

import tkinter as tk
from tkinter import messagebox
import win32gui
import win32con
import win32api
import win32process
import ctypes
from ctypes import wintypes
import psutil
import threading
import time
import sys
import os
from PIL import Image, ImageTk, ImageFilter, ImageGrab
import pystray
from pystray import MenuItem as item
import keyboard
import queue
import logging

# Set up QUIET logging (only errors)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhatsAppAutoBlur:
    def __init__(self):
        # Fix DPI awareness FIRST
        self.fix_dpi_awareness()
        
        self.whatsapp_hwnd = None
        self.blur_window = None
        self.is_blurred = False
        self.is_enabled = True  # Auto-blur enabled by default
        self.hover_remove_blur = True
        self.toggle_key = 'ctrl+alt+q'
        
        # Hover state tracking
        self.is_hovering = False
        self.hover_timer = None
        
        # Safety: prevent rapid blur attempts
        self.last_blur_attempt = 0
        self.min_blur_interval = 0.5  # Fast response
        self.capturing_screenshot = False
        
        # Main tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Cache for blurred images
        self.blur_cache = None
        self.whatsapp_rect = None
        
        # UI queue for thread-safe operations
        self.ui_queue = queue.Queue()
        
        # Start monitoring and auto-blur
        self.setup_hotkey()
        self.start_monitoring()
        self.create_system_tray()
        
        print("🚀 WhatsApp Auto-Blur (Simplified) initialized!")
        print(f"📝 Press {self.toggle_key} to toggle auto-blur on/off")
        print("🔄 Auto-blur activates when WhatsApp is visible")
        print("🖱️ Hover to reveal, stop hovering to blur again")
    
    def fix_dpi_awareness(self):
        """Fix DPI awareness to prevent blurry window positioning"""
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass
    
    def test_screenshot_permission(self):
        """Test if we can take screenshots"""
        try:
            test_shot = ImageGrab.grab(bbox=(0, 0, 100, 100))
            if test_shot and test_shot.size == (100, 100):
                print("✅ Screenshot permissions working")
                return True
            else:
                print("❌ Screenshot failed")
                return False
        except Exception as e:
            print(f"❌ Screenshot test failed: {e}")
            messagebox.showerror("Permission Error", 
                "Screenshot permission denied!\n\n"
                "Windows 11/10 Privacy Settings:\n"
                "1. Go to Settings > Privacy & Security\n"
                "2. Click 'Desktop app graphics capture'\n"
                "3. Turn ON the main toggle\n"
                "4. Restart this app")
            return False
    
    def is_whatsapp_visible_simple(self, hwnd):
        """Simple and reliable visibility check"""
        try:
            # Basic checks
            if not hwnd or not win32gui.IsWindowVisible(hwnd):
                return False
            
            if win32gui.IsIconic(hwnd):  # Minimized
                return False
            
            # Get window rect
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            # Must have reasonable size
            if width < 300 or height < 300:
                return False
            
            # Must be on screen
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            
            if x2 <= 0 or y2 <= 0 or x >= screen_width or y >= screen_height:
                return False
            
            # Store rect and return true
            self.whatsapp_rect = rect
            return True
            
        except Exception:
            return False
    
    def find_whatsapp_window(self):
        """Find WhatsApp window - simplified"""
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    
                    # Simple check for WhatsApp in title
                    if "whatsapp" in window_text.lower():
                        # Get process name to verify
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            process = psutil.Process(pid)
                            exe_name = process.name().lower()
                            
                            # Prioritize desktop WhatsApp
                            if exe_name == "whatsapp.exe":
                                windows.append((hwnd, 100, window_text))
                            elif "applicationframehost.exe" in exe_name:
                                windows.append((hwnd, 90, window_text))
                            else:
                                windows.append((hwnd, 50, window_text))
                        except:
                            windows.append((hwnd, 50, window_text))
                            
                except Exception:
                    pass
            return True
        
        windows = []
        try:
            win32gui.EnumWindows(enum_callback, windows)
            
            if windows:
                # Sort by priority and get the best match
                windows.sort(key=lambda x: x[1], reverse=True)
                best_hwnd = windows[0][0]
                
                # Verify it's actually visible
                if self.is_whatsapp_visible_simple(best_hwnd):
                    return best_hwnd
                    
        except Exception as e:
            logger.error(f"Error finding WhatsApp: {e}")
        
        return None
    
    def capture_screenshot(self, hwnd):
        """Capture WhatsApp screenshot"""
        if self.capturing_screenshot:
            return None
            
        try:
            self.capturing_screenshot = True
            
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            
            width = x2 - x
            height = y2 - y
            if width < 100 or height < 100:
                return None
            
            time.sleep(0.05)  # Small delay
            screenshot = ImageGrab.grab(bbox=(x, y, x2, y2))
            
            if screenshot and screenshot.size == (width, height):
                return screenshot
            else:
                return None
                
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
        finally:
            self.capturing_screenshot = False
    
    def create_blur_image(self, image):
        """Create blurred version"""
        if not image:
            return None
            
        try:
            blurred = image.filter(ImageFilter.GaussianBlur(radius=40))
            return blurred
        except Exception as e:
            logger.error(f"Blur error: {e}")
            return None
    
    def create_blur_window(self, x, y, width, height):
        """Create blur window without white screen"""
        try:
            # Destroy existing
            if self.blur_window:
                self.blur_window.destroy()
                self.blur_window = None
                self.root.update_idletasks()
                time.sleep(0.05)
            
            # Create new window
            self.blur_window = tk.Toplevel(self.root)
            
            # CRITICAL: Hide window first
            self.blur_window.withdraw()
            
            # Configure while hidden
            self.blur_window.overrideredirect(True)
            self.blur_window.configure(bg='black')
            self.blur_window.attributes('-topmost', True)
            self.blur_window.attributes('-alpha', 1.0)
            self.blur_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create canvas
            canvas = tk.Canvas(self.blur_window, 
                             width=width, height=height,
                             bg='black', highlightthickness=0)
            canvas.pack(fill='both', expand=True)
            
            # Add content while hidden
            if self.blur_cache:
                try:
                    if self.blur_cache.size != (width, height):
                        resized = self.blur_cache.resize((width, height), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(resized)
                    else:
                        photo = ImageTk.PhotoImage(self.blur_cache)
                    
                    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                    canvas.image = photo
                    
                except Exception:
                    canvas.create_text(width//2, height//2, 
                                     text="🔒 WhatsApp Blurred\nHover to reveal", 
                                     font=('Arial', 16, 'bold'), 
                                     fill='white', justify='center')
            else:
                canvas.create_text(width//2, height//2, 
                                 text="🔒 WhatsApp Blurred\nHover to reveal", 
                                 font=('Arial', 16, 'bold'), 
                                 fill='white', justify='center')
            
            # Bind hover events
            if self.hover_remove_blur:
                self.blur_window.bind('<Enter>', self.on_hover_enter)
                self.blur_window.bind('<Leave>', self.on_hover_leave)
                canvas.bind('<Enter>', self.on_hover_enter)
                canvas.bind('<Leave>', self.on_hover_leave)
            
            # Update while hidden
            self.blur_window.update_idletasks()
            self.blur_window.update()
            
            # NOW show the window
            self.blur_window.deiconify()
            
            # Position using Win32
            try:
                time.sleep(0.05)
                hwnd = self.blur_window.winfo_id()
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 
                                    x, y, width, height,
                                    win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE)
            except Exception:
                pass
            
            self.blur_window.update_idletasks()
            print("✅ Blur window created successfully")
            
        except Exception as e:
            print(f"❌ Error creating blur: {e}")
            if self.blur_window:
                try:
                    self.blur_window.destroy()
                except:
                    pass
                self.blur_window = None
    
    def show_blur(self):
        """Show blur overlay"""
        if not self.is_enabled or self.is_hovering:
            return
            
        current_time = time.time()
        if current_time - self.last_blur_attempt < self.min_blur_interval:
            return
        
        self.last_blur_attempt = current_time
        
        if self.is_blurred:
            return
        
        # Find WhatsApp
        hwnd = self.find_whatsapp_window()
        if not hwnd or not self.is_whatsapp_visible_simple(hwnd):
            return
        
        self.whatsapp_hwnd = hwnd
        x, y, x2, y2 = self.whatsapp_rect
        width = x2 - x
        height = y2 - y
        
        # Capture and blur
        screenshot = self.capture_screenshot(hwnd)
        if screenshot:
            self.blur_cache = self.create_blur_image(screenshot)
        else:
            self.blur_cache = None
        
        # Create blur window
        self.create_blur_window(x, y, width, height)
        
        if self.blur_window:
            self.is_blurred = True
            print("🔒 Auto-blur activated")
    
    def hide_blur(self):
        """Hide blur overlay"""
        if self.blur_window:
            self.blur_window.destroy()
            self.blur_window = None
        
        self.is_blurred = False
        self.blur_cache = None
    
    def toggle_auto_blur(self):
        """Toggle auto-blur mode"""
        self.is_enabled = not self.is_enabled
        if self.is_enabled:
            print("🔄 Auto-blur ENABLED")
        else:
            print("⏸️ Auto-blur DISABLED")
            self.hide_blur()
    
    def on_hover_enter(self, event):
        """Hover enter - remove blur"""
        self.is_hovering = True
        if self.is_blurred:
            self.hide_blur()
    
    def on_hover_leave(self, event):
        """Hover leave - restore blur"""
        self.is_hovering = False
        
        if self.hover_timer:
            self.hover_timer.cancel()
        
        def restore_blur():
            if not self.is_hovering and self.is_enabled:
                self.ui_queue.put(('show_blur', None))
        
        self.hover_timer = threading.Timer(0.3, restore_blur)
        self.hover_timer.start()
    
    def setup_hotkey(self):
        """Setup keyboard hotkey"""
        def hotkey_handler():
            self.ui_queue.put(('toggle_auto_blur', None))
        
        try:
            keyboard.add_hotkey(self.toggle_key, hotkey_handler)
            print(f"⌨️ Hotkey {self.toggle_key} registered")
        except Exception as e:
            logger.error(f"Hotkey error: {e}")
    
    def start_monitoring(self):
        """Simple monitoring loop"""
        def monitor():
            last_check = 0
            
            while True:
                try:
                    # Process UI queue
                    try:
                        action, data = self.ui_queue.get_nowait()
                        if action == 'toggle_auto_blur':
                            self.toggle_auto_blur()
                        elif action == 'show_blur':
                            self.show_blur()
                        elif action == 'hide_blur':
                            self.hide_blur()
                        elif action == 'quit':
                            break
                    except queue.Empty:
                        pass
                    
                    # Auto-blur check every second
                    current_time = time.time()
                    if current_time - last_check >= 1.0:
                        last_check = current_time
                        
                        if self.is_enabled and not self.is_hovering:
                            hwnd = self.find_whatsapp_window()
                            whatsapp_visible = hwnd and self.is_whatsapp_visible_simple(hwnd)
                            
                            if whatsapp_visible and not self.is_blurred:
                                # Need to blur
                                self.show_blur()
                            elif not whatsapp_visible and self.is_blurred:
                                # Need to remove blur
                                self.hide_blur()
                        elif not self.is_enabled and self.is_blurred:
                            # Disabled - remove blur
                            self.hide_blur()
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Monitor error: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def create_system_tray(self):
        """Create system tray"""
        def quit_app(icon, item):
            self.ui_queue.put(('quit', None))
            self.hide_blur()
            icon.stop()
            self.root.quit()
        
        def toggle_tray(icon, item):
            self.ui_queue.put(('toggle_auto_blur', None))
        
        image = Image.new('RGB', (64, 64), color='white')
        
        menu = pystray.Menu(
            item('Toggle Auto-Blur (Ctrl+Alt+Q)', toggle_tray),
            pystray.Menu.SEPARATOR,
            item('Quit', quit_app)
        )
        
        self.icon = pystray.Icon("WhatsApp Auto-Blur", image, "WhatsApp Auto-Blur", menu)
        
        def run_tray():
            self.icon.run()
        
        tray_thread = threading.Thread(target=run_tray, daemon=True)
        tray_thread.start()
    
    def run(self):
        """Main run loop"""
        try:
            if not self.test_screenshot_permission():
                return
            
            print("🚀 WhatsApp Auto-Blur is running!")
            print(f"📝 Press {self.toggle_key} to toggle auto-blur")
            print("🎯 Auto-blur will activate when WhatsApp is visible")
            print("🖱️ Hover to reveal, stop hovering to blur again")
            
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        except Exception as e:
            logger.error(f"Main error: {e}")
        finally:
            self.hide_blur()
            if hasattr(self, 'icon'):
                self.icon.stop()

def main():
    app = WhatsAppAutoBlur()
    app.run()

if __name__ == "__main__":
    main()
