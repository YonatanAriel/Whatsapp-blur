#!/usr/bin/env python3
"""
WhatsApp Blur - VISIBILITY FIXED VERSION
Critical fixes: only blurs when WhatsApp is visible and in foreground, stronger blur effect
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

class WhatsAppBlurVisibilityFixed:
    def __init__(self):
        # Fix DPI awareness FIRST
        self.fix_dpi_awareness()
        
        self.whatsapp_hwnd = None
        self.blur_window = None
        self.is_blurred = False
        self.is_enabled = True
        self.hover_remove_blur = True
        self.toggle_key = 'ctrl+alt+q'
        
        # Main tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("WhatsApp Blur")
        
        # System tray icon
        self.tray_icon = None
        
        # Threading
        self.ui_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        
        # Cache
        self.blur_cache = None
        self.whatsapp_rect = None
        
        # DPI
        self.dpi_scale = self.get_dpi_scale()
        
        # Initialize
        self.setup_keyboard_shortcut()
        self.create_tray_icon()
        self.start_monitoring()
        
        # Check if WhatsApp is already visible and auto-blur
        self.initial_whatsapp_check()
        
        # Process UI queue
        self.root.after(100, self.process_ui_queue)
    
    def initial_whatsapp_check(self):
        """Check if WhatsApp is already visible when app starts"""
        try:
            hwnd = self.find_whatsapp_window()
            if hwnd:
                print("📱 WhatsApp already visible at startup - auto-blurring")
                self.whatsapp_hwnd = hwnd
                self.root.after(1000, lambda: self.ui_queue.put(('show_blur', None)))  # Delay slightly
        except Exception as e:
            logger.error(f"Initial check error: {e}")
    
    def fix_dpi_awareness(self):
        """Fix DPI awareness for proper window positioning"""
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass
    
    def get_dpi_scale(self):
        """Get DPI scaling factor"""
        try:
            dc = win32gui.GetDC(0)
            dpi_x = win32api.GetDeviceCaps(dc, 88)
            win32gui.ReleaseDC(0, dc)
            return dpi_x / 96.0
        except:
            return 1.0
    
    def is_whatsapp_actually_visible(self, hwnd):
        """
        CRITICAL FIX: Check if WhatsApp is actually visible to the user
        This prevents blur from showing when WhatsApp is minimized/hidden
        """
        try:
            if not hwnd or not win32gui.IsWindowVisible(hwnd):
                return False
            
            # Check if minimized
            if win32gui.IsIconic(hwnd):
                return False
            
            # Check if in foreground or very close to foreground
            foreground_hwnd = win32gui.GetForegroundWindow()
            
            # Direct foreground match
            if hwnd == foreground_hwnd:
                return True
            
            # Check if it's a child of foreground (UWP apps)
            try:
                parent = win32gui.GetParent(hwnd)
                if parent == foreground_hwnd:
                    return True
            except:
                pass
            
            # Check window rect validity
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            if width < 200 or height < 200:
                return False
            
            # Check if mostly on screen
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            
            if x2 < 0 or y2 < 0 or x > screen_width or y > screen_height:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking visibility: {e}")
            return False
    
    def find_whatsapp_window(self):
        """Find WhatsApp with visibility check"""
        windows = []
        
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
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
                            windows.append((hwnd, window_text, class_name, rect, exe_name, priority))
                        
                except Exception:
                    pass
            
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, windows)
            
            if not windows:
                return None
            
            windows.sort(key=lambda x: x[5], reverse=True)
            
            # CRITICAL: Only return if actually visible
            for hwnd, title, class_name, rect, exe_name, priority in windows:
                if self.is_whatsapp_actually_visible(hwnd):
                    self.whatsapp_rect = rect
                    print(f"✅ WhatsApp VISIBLE: '{title}' (process: {exe_name})")
                    return hwnd
            
            print("⚠️ WhatsApp found but not visible/foreground")
            return None
            
        except Exception as e:
            logger.error(f"Error finding WhatsApp: {e}")
            return None
    
    def capture_whatsapp_screenshot(self):
        """Capture screenshot of WhatsApp window"""
        if not self.whatsapp_rect:
            return None
        
        try:
            x, y, x2, y2 = self.whatsapp_rect
            
            if self.dpi_scale != 1.0:
                x = int(x / self.dpi_scale)
                y = int(y / self.dpi_scale)
                x2 = int(x2 / self.dpi_scale)
                y2 = int(y2 / self.dpi_scale)
            
            try:
                screenshot = ImageGrab.grab(bbox=(x, y, x2, y2))
                return screenshot
            except Exception:
                try:
                    full_screenshot = ImageGrab.grab()
                    if x >= 0 and y >= 0 and x2 <= full_screenshot.width and y2 <= full_screenshot.height:
                        cropped = full_screenshot.crop((x, y, x2, y2))
                        return cropped
                except Exception:
                    pass
                return None
                
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    def create_blurred_image(self, image):
        """Create MUCH STRONGER blurred image"""
        if not image:
            return None
        
        try:
            # MUCH STRONGER blur for better privacy
            blurred = image.filter(ImageFilter.GaussianBlur(radius=50))  # Was 25, now 50!
            
            # Stronger privacy overlay
            overlay = Image.new('RGBA', blurred.size, (250, 250, 250, 140))
            result = Image.alpha_composite(blurred.convert('RGBA'), overlay)
            
            return result
        except Exception as e:
            logger.error(f"Error creating blurred image: {e}")
            return None
    
    def create_blur_window(self):
        """Create blur overlay window"""
        if not self.whatsapp_rect:
            return
        
        try:
            x, y, x2, y2 = self.whatsapp_rect
            width = x2 - x
            height = y2 - y
            
            if self.blur_window:
                self.blur_window.destroy()
            
            self.blur_window = tk.Toplevel(self.root)
            self.blur_window.title("WhatsApp Blur Overlay")
            self.blur_window.geometry(f"{width}x{height}+{x}+{y}")
            
            self.blur_window.attributes('-alpha', 0.95)
            self.blur_window.attributes('-topmost', True)
            self.blur_window.overrideredirect(True)
            
            if self.blur_cache:
                photo = ImageTk.PhotoImage(self.blur_cache)
                label = tk.Label(self.blur_window, image=photo)
                label.image = photo
                label.pack(fill='both', expand=True)
                
                label.bind('<Enter>', self.on_hover_enter)
                label.bind('<Leave>', self.on_hover_leave)
            
            self.make_clickthrough()
            self.is_blurred = True
            print("✅ STRONG blur overlay created")
            
        except Exception as e:
            logger.error(f"Error creating blur window: {e}")
    
    def update_blur_position(self):
        """Update blur position when WhatsApp moves"""
        if not self.is_blurred or not self.whatsapp_hwnd:
            return
        
        try:
            current_rect = win32gui.GetWindowRect(self.whatsapp_hwnd)
            
            if current_rect != self.whatsapp_rect:
                self.whatsapp_rect = current_rect
                x, y, x2, y2 = current_rect
                
                if self.blur_window and self.blur_window.winfo_exists():
                    self.blur_window.geometry(f"{x2-x}x{y2-y}+{x}+{y}")
                    
        except Exception as e:
            logger.error(f"Error updating position: {e}")
    
    def make_clickthrough(self):
        """Make window click-through"""
        if not self.blur_window:
            return
        
        try:
            hwnd = self.blur_window.winfo_id()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        except Exception as e:
            logger.error(f"Error setting click-through: {e}")
    
    def on_hover_enter(self, event):
        """Handle hover enter"""
        if self.hover_remove_blur and self.is_blurred:
            self.ui_queue.put(('hide_blur', None))
    
    def on_hover_leave(self, event):
        """Handle hover leave"""
        if self.hover_remove_blur and self.is_enabled:
            self.root.after(300, lambda: self.ui_queue.put(('show_blur_if_enabled', None)))
    
    def show_blur_if_enabled(self):
        """Show blur if conditions are met"""
        if not self.is_blurred and self.is_enabled:
            self.show_blur()
    
    def show_blur(self):
        """Show blur overlay - ONLY if WhatsApp is visible"""
        if not self.is_enabled or self.is_blurred:
            return
        
        print("🔍 Checking WhatsApp visibility...")
        
        # This now includes proper visibility check
        self.whatsapp_hwnd = self.find_whatsapp_window()
        if not self.whatsapp_hwnd:
            print("❌ WhatsApp not visible - no blur shown")
            return
        
        screenshot = self.capture_whatsapp_screenshot()
        if not screenshot:
            print("❌ Screenshot failed")
            return
        
        self.blur_cache = self.create_blurred_image(screenshot)
        if not self.blur_cache:
            print("❌ Blur creation failed")
            return
        
        self.create_blur_window()
        print("✅ Strong blur activated!")
    
    def hide_blur(self):
        """Hide blur overlay"""
        if self.blur_window:
            self.blur_window.destroy()
            self.blur_window = None
        
        self.is_blurred = False
        self.blur_cache = None
        print("❌ Blur hidden")
        self.update_tray_menu()
    
    def toggle_blur(self):
        """Toggle blur on/off"""
        print(f"\n🎯 TOGGLE PRESSED! Current: {'ON' if self.is_blurred else 'OFF'}")
        
        if self.is_blurred:
            self.hide_blur()
        else:
            self.show_blur()
    
    def setup_keyboard_shortcut(self):
        """Setup keyboard shortcut"""
        try:
            keyboard.add_hotkey(self.toggle_key, self.toggle_blur)
            print(f"✅ Hotkey ready: {self.toggle_key}")
        except Exception as e:
            logger.error(f"Hotkey setup failed: {e}")
    
    def create_tray_icon(self):
        """Create system tray icon"""
        try:
            image = Image.new('RGB', (64, 64), color='darkblue')
            
            menu = pystray.Menu(
                item('Toggle Blur', self.toggle_blur),
                item('Test Screenshot', self.test_screenshot),
                item('Show System Info', self.show_system_info),
                item('Exit', self.quit_application)
            )
            
            self.tray_icon = pystray.Icon("WhatsApp Blur", image, menu=menu)
            
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            print("✅ Tray icon created")
        except Exception as e:
            logger.error(f"Tray icon error: {e}")
    
    def test_screenshot(self):
        """Test screenshot functionality"""
        try:
            test_img = ImageGrab.grab(bbox=(0, 0, 400, 300))
            test_path = "test_screenshot.png"
            test_img.save(test_path)
            
            messagebox.showinfo("Screenshot Test", 
                              f"✅ Screenshot working!\n"
                              f"Saved: {test_path}\n"
                              f"Size: {test_img.size}")
        except Exception as e:
            messagebox.showerror("Screenshot Test", 
                               f"❌ Screenshot failed!\n"
                               f"Error: {e}\n\n"
                               f"Fix: Settings > Privacy & Security > Screenshots")
    
    def show_system_info(self):
        """Show system information"""
        whatsapp_info = "Not found"
        
        hwnd = self.find_whatsapp_window()
        if hwnd:
            try:
                title = win32gui.GetWindowText(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                visible = self.is_whatsapp_actually_visible(hwnd)
                
                whatsapp_info = f"Found: '{title}'\n"
                whatsapp_info += f"Position: {rect}\n"
                whatsapp_info += f"Actually visible: {visible}"
            except:
                whatsapp_info = "Found but error reading"
        
        info = f"🖥️ System Status\n\n"
        info += f"App: {'Enabled' if self.is_enabled else 'Disabled'}\n"
        info += f"Blur: {'Active' if self.is_blurred else 'Inactive'}\n"
        info += f"Hotkey: {self.toggle_key}\n"
        info += f"DPI: {self.dpi_scale:.2f}\n\n"
        info += f"📱 WhatsApp:\n{whatsapp_info}"
        
        messagebox.showinfo("System Info", info)
    
    def update_tray_menu(self):
        """Update tray menu"""
        if self.tray_icon:
            status = "ON" if self.is_enabled else "OFF"
            menu = pystray.Menu(
                item(f'Blur: {status}', self.toggle_blur),
                item('Test Screenshot', self.test_screenshot),
                item('Show System Info', self.show_system_info),
                item('Exit', self.quit_application)
            )
            self.tray_icon.menu = menu
    
    def start_monitoring(self):
        """Start monitoring thread"""
        self.monitoring_thread = threading.Thread(target=self._monitor_whatsapp, daemon=True)
        self.monitoring_thread.start()
    
    def _monitor_whatsapp(self):
        """Monitor WhatsApp - with AUTO BLUR when visible"""
        while not self.shutdown_event.is_set():
            try:
                if self.is_enabled:
                    current_hwnd = self.find_whatsapp_window()
                    
                    if current_hwnd and current_hwnd != self.whatsapp_hwnd:
                        self.whatsapp_hwnd = current_hwnd
                        print("📱 WhatsApp became visible - AUTO BLURRING")
                        # AUTOMATICALLY show blur when WhatsApp becomes visible
                        if not self.is_blurred:
                            self.ui_queue.put(('show_blur', None))
                    
                    elif not current_hwnd and self.is_blurred:
                        print("📱 WhatsApp no longer visible - hiding blur")
                        self.ui_queue.put(('hide_blur', None))
                        self.whatsapp_hwnd = None
                    
                    if self.is_blurred and current_hwnd:
                        self.ui_queue.put(('update_blur_position', None))
                
                time.sleep(0.5)  # Fast checking
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(2)
    
    def process_ui_queue(self):
        """Process UI operations"""
        try:
            while not self.ui_queue.empty():
                operation, data = self.ui_queue.get_nowait()
                
                if operation == 'show_blur':
                    self.show_blur()
                elif operation == 'hide_blur':
                    self.hide_blur()
                elif operation == 'show_blur_if_enabled':
                    self.show_blur_if_enabled()
                elif operation == 'update_blur_position':
                    self.update_blur_position()
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"UI queue error: {e}")
        
        self.root.after(100, self.process_ui_queue)
    
    def quit_application(self):
        """Quit application"""
        print("Quitting WhatsApp Blur")
        self.shutdown_event.set()
        self.hide_blur()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        try:
            keyboard.unhook_all()
        except:
            pass
        
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

def main():
    """Main function"""
    if not sys.platform.startswith('win'):
        print("This application is designed for Windows only.")
        return
    
    try:
        app = WhatsAppBlurVisibilityFixed()
        
        print(f"\n🎉 WhatsApp Blur VISIBILITY FIXED!")
        print(f"✅ Hotkey: {app.toggle_key}")
        print(f"✅ FIXED: Only blurs when WhatsApp is visible")
        print(f"✅ FIXED: Stronger blur (radius 50)")
        print(f"✅ FIXED: No more incorrect blur placement")
        print(f"\n🔄 Monitoring WhatsApp visibility...")
        
        app.root.mainloop()
        
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        messagebox.showerror("Error", f"Failed to start: {e}")

if __name__ == "__main__":
    main()
