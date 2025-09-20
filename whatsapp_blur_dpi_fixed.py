#!/usr/bin/env python3
"""
WhatsApp Blur - DPI Scaling Fixed Version
This version fixes Windows 11 DPI scaling and positioning issues.
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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhatsAppBlurFixed:
    def __init__(self):
        # Fix DPI awareness FIRST
        self.fix_dpi_awareness()
        
        self.whatsapp_hwnd = None
        self.blur_window = None
        self.is_blurred = False
        self.is_enabled = True
        self.hover_remove_blur = True
        self.toggle_key = 'ctrl+win+b'
        
        # Main tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("WhatsApp Blur Fixed")
        
        # System tray icon
        self.tray_icon = None
        
        # Threading events and queue
        self.shutdown_event = threading.Event()
        self.monitoring_thread = None
        self.ui_queue = queue.Queue()
        
        # Screenshot and blur cache
        self.blur_cache = None
        self.whatsapp_rect = None
        self.dpi_scale = self.get_dpi_scale()
        
        logger.info(f"=== WhatsApp Blur Fixed Version - DPI Scale: {self.dpi_scale} ===")
        self.check_system_requirements()
        
        # Initialize the application
        self.setup_keyboard_shortcut()
        self.create_tray_icon()
        self.start_monitoring()
        self.process_ui_queue()
    
    def fix_dpi_awareness(self):
        """Fix DPI awareness for proper coordinate calculation"""
        try:
            # Method 1: Set DPI awareness for current process
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            logger.info("✓ DPI awareness set to per-monitor aware")
        except Exception as e:
            try:
                # Method 2: Alternative DPI awareness
                ctypes.windll.user32.SetProcessDPIAware()
                logger.info("✓ DPI awareness set (alternative method)")
            except Exception as e2:
                logger.warning(f"⚠ Could not set DPI awareness: {e}, {e2}")
    
    def get_dpi_scale(self):
        """Get the current DPI scaling factor"""
        try:
            # Get DPI of primary monitor
            hdc = ctypes.windll.user32.GetDC(0)
            dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            ctypes.windll.user32.ReleaseDC(0, hdc)
            
            scale = dpi_x / 96.0  # 96 DPI is 100% scaling
            logger.info(f"DPI: {dpi_x}, Scale factor: {scale}")
            return scale
        except Exception as e:
            logger.error(f"Error getting DPI scale: {e}")
            return 1.0
    
    def check_system_requirements(self):
        """Check system requirements and settings"""
        logger.info("=== System Requirements Check ===")
        
        # Check admin rights
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            logger.info(f"Admin rights: {'✓' if is_admin else '❌'}")
            if not is_admin:
                logger.warning("Consider running as Administrator for full functionality")
        except:
            logger.warning("Could not check admin rights")
        
        # Check DPI scaling
        if self.dpi_scale != 1.0:
            logger.warning(f"⚠ DPI scaling detected: {self.dpi_scale * 100:.0f}%")
            logger.warning("  This may cause positioning issues. Consider setting display to 100% scale.")
        else:
            logger.info("✓ Display scaling at 100%")
        
        # Test screenshot capability
        try:
            test_img = ImageGrab.grab(bbox=(0, 0, 100, 100))
            logger.info("✓ Screenshot capability working")
        except Exception as e:
            logger.error(f"❌ Screenshot test failed: {e}")
            logger.error("  Check Windows Privacy Settings > Screenshots/Screen recording")
    
    def find_whatsapp_window(self):
        """Enhanced WhatsApp window detection - Fixed for proper WhatsApp identification"""
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    exe_name = ""
                    
                    # Get process name for better identification
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        exe_name = process.name().lower()
                    except:
                        pass
                    
                    # Improved WhatsApp detection
                    is_whatsapp = False
                    
                    # Method 1: Check for exact WhatsApp process name
                    if exe_name == "whatsapp.exe":
                        is_whatsapp = True
                        logger.debug(f"Found WhatsApp by process name: {exe_name}")
                    
                    # Method 2: Check window title for WhatsApp
                    elif any(keyword in window_text.lower() for keyword in ["whatsapp", "whats app"]):
                        # Make sure it's not a browser tab by checking class name
                        if "chrome" not in class_name.lower() or "whatsapp" in window_text.lower():
                            is_whatsapp = True
                            logger.debug(f"Found WhatsApp by title: '{window_text}'")
                    
                    # Method 3: Check for WhatsApp Desktop specific patterns
                    elif class_name == "ApplicationFrameWindow" and "whatsapp" in window_text.lower():
                        is_whatsapp = True
                        logger.debug(f"Found WhatsApp Desktop frame: '{window_text}'")
                    
                    # Method 4: Fallback - Chrome widget with WhatsApp-like characteristics
                    elif 'Chrome_WidgetWin_1' in class_name and exe_name == "whatsapp.exe":
                        rect = win32gui.GetWindowRect(hwnd)
                        width = rect[2] - rect[0]
                        height = rect[3] - rect[1]
                        # WhatsApp Desktop typical size range
                        if 300 <= width <= 1600 and 400 <= height <= 1200:
                            is_whatsapp = True
                            logger.debug(f"Found WhatsApp by Chrome widget size: {width}x{height}")
                    
                    # EXCLUDE VS Code and other development tools
                    if any(keyword in window_text.lower() for keyword in 
                           ["visual studio code", "vs code", "code.exe", "notepad", "sublime", "atom"]):
                        is_whatsapp = False
                        logger.debug(f"Excluded development tool: '{window_text}'")
                    
                    if is_whatsapp:
                        rect = win32gui.GetWindowRect(hwnd)
                        windows.append((hwnd, window_text, class_name, rect, exe_name))
                        logger.info(f"✅ Found WhatsApp window: '{window_text}' (process: {exe_name}) at {rect}")
                        
                except Exception as e:
                    logger.debug(f"Error checking window {hwnd}: {e}")
            return True
        
        windows = []
        try:
            win32gui.EnumWindows(enum_callback, windows)
            if windows:
                # Priority 1: WhatsApp.exe process (most reliable)
                whatsapp_exe_windows = [w for w in windows if w[4] == "whatsapp.exe"]
                if whatsapp_exe_windows:
                    best = max(whatsapp_exe_windows, key=lambda w: (w[3][2]-w[3][0]) * (w[3][3]-w[3][1]))
                    logger.info(f"🎯 Selected WhatsApp.exe window: '{best[1]}' (process: {best[4]}) at {best[3]}")
                    return best[0]
                
                # Priority 2: ApplicationFrameHost.exe (WhatsApp Desktop from Microsoft Store)
                frame_host_windows = [w for w in windows if w[4] == "applicationframehost.exe"]
                if frame_host_windows:
                    best = max(frame_host_windows, key=lambda w: (w[3][2]-w[3][0]) * (w[3][3]-w[3][1]))
                    logger.info(f"🎯 Selected WhatsApp Desktop window: '{best[1]}' (process: {best[4]}) at {best[3]}")
                    return best[0]
                
                # Priority 3: Exclude known non-WhatsApp processes
                filtered_windows = [w for w in windows if w[4] not in 
                                  ["windowsterminal.exe", "explorer.exe", "python.exe", "code.exe"]]
                if filtered_windows:
                    best = max(filtered_windows, key=lambda w: (w[3][2]-w[3][0]) * (w[3][3]-w[3][1]))
                    logger.info(f"🎯 Selected filtered window: '{best[1]}' (process: {best[4]}) at {best[3]}")
                    return best[0]
                
                # Fallback: Return largest window
                best = max(windows, key=lambda w: (w[3][2]-w[3][0]) * (w[3][3]-w[3][1]))
                logger.warning(f"⚠️ Fallback selection: '{best[1]}' (process: {best[4]}) at {best[3]}")
                return best[0]
            else:
                logger.debug("No WhatsApp window found")
                return None
        except Exception as e:
            logger.error(f"Error finding WhatsApp window: {e}")
            return None
    
    def get_window_rect_dpi_aware(self, hwnd):
        """Get window rect with DPI scaling compensation"""
        try:
            # Get raw window rect
            raw_rect = win32gui.GetWindowRect(hwnd)
            
            # If DPI scaling is involved, we might need to adjust
            if self.dpi_scale != 1.0:
                # For some Windows versions, coordinates might need scaling
                x, y, x2, y2 = raw_rect
                # Try both scaled and unscaled versions
                logger.debug(f"Raw rect: {raw_rect}, DPI scale: {self.dpi_scale}")
            
            return raw_rect
        except Exception as e:
            logger.error(f"Error getting window rect: {e}")
            return None
    
    def capture_whatsapp_screenshot(self):
        """Capture screenshot with DPI scaling fixes"""
        if not self.whatsapp_hwnd:
            logger.warning("No WhatsApp window handle")
            return None
        
        try:
            # Get window position with DPI awareness
            rect = self.get_window_rect_dpi_aware(self.whatsapp_hwnd)
            if not rect:
                return None
            
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            logger.info(f"Capturing WhatsApp at {rect} (size: {width}x{height})")
            
            # Store for blur window positioning
            self.whatsapp_rect = rect
            
            # Capture with error handling
            try:
                # Test if coordinates are valid
                if x < -10000 or y < -10000 or width <= 0 or height <= 0:
                    logger.error(f"Invalid coordinates: {rect}")
                    return None
                
                screenshot = ImageGrab.grab(bbox=(x, y, x2, y2))
                logger.info(f"✓ Screenshot captured: {screenshot.size}")
                
                # Save debug image
                debug_path = "debug_whatsapp_screenshot.png"
                screenshot.save(debug_path)
                logger.debug(f"Debug screenshot saved: {debug_path}")
                
                return screenshot
                
            except Exception as e:
                logger.error(f"Screenshot capture failed: {e}")
                
                # Try alternative: capture full screen and crop
                try:
                    logger.info("Trying full screen capture method...")
                    full_screenshot = ImageGrab.grab()
                    
                    # Crop to WhatsApp area
                    if x >= 0 and y >= 0 and x2 <= full_screenshot.width and y2 <= full_screenshot.height:
                        cropped = full_screenshot.crop((x, y, x2, y2))
                        logger.info(f"✓ Alternative screenshot method worked: {cropped.size}")
                        return cropped
                    else:
                        logger.error(f"Invalid crop coordinates for full screen method")
                        return None
                        
                except Exception as e2:
                    logger.error(f"Alternative screenshot method failed: {e2}")
                    return None
                
        except Exception as e:
            logger.error(f"Error in capture_whatsapp_screenshot: {e}")
            return None
    
    def create_blurred_image(self, image):
        """Create blurred image"""
        if not image:
            return None
        
        try:
            # Apply Gaussian blur
            blurred = image.filter(ImageFilter.GaussianBlur(radius=12))
            
            # Add privacy overlay
            overlay = Image.new('RGBA', blurred.size, (220, 220, 220, 80))
            result = Image.alpha_composite(blurred.convert('RGBA'), overlay)
            
            # Save debug blurred image
            debug_path = "debug_blurred_image.png"
            result.save(debug_path)
            logger.debug(f"Debug blurred image saved: {debug_path}")
            
            return result
        except Exception as e:
            logger.error(f"Error creating blurred image: {e}")
            return None
    
    def create_blur_window(self):
        """Create blur overlay window with DPI fixes"""
        if not self.whatsapp_rect:
            logger.warning("No WhatsApp rect available")
            return
        
        try:
            x, y, x2, y2 = self.whatsapp_rect
            width = x2 - x
            height = y2 - y
            
            logger.info(f"Creating blur window at {x},{y} size {width}x{height}")
            
            # Destroy existing window
            if self.blur_window:
                self.blur_window.destroy()
            
            # Create blur window
            self.blur_window = tk.Toplevel(self.root)
            self.blur_window.title("WhatsApp Blur")
            self.blur_window.geometry(f"{width}x{height}+{x}+{y}")
            self.blur_window.attributes('-topmost', True)
            self.blur_window.overrideredirect(True)
            
            # Create canvas
            canvas = tk.Canvas(self.blur_window, width=width, height=height, 
                             highlightthickness=0, bg='#E8E8E8')
            canvas.pack()
            
            # Add blur image or fallback
            if self.blur_cache:
                try:
                    # Resize if needed
                    if self.blur_cache.size != (width, height):
                        resized = self.blur_cache.resize((width, height), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(resized)
                    else:
                        photo = ImageTk.PhotoImage(self.blur_cache)
                    
                    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                    canvas.image = photo  # Keep reference
                    logger.info("✓ Blur image displayed")
                    
                except Exception as e:
                    logger.error(f"Error displaying blur image: {e}")
                    # Fallback text
                    canvas.create_text(width//2, height//2, 
                                     text="🔒 WhatsApp Blurred\nHover to reveal", 
                                     font=('Arial', 14, 'bold'), 
                                     fill='#666666', justify='center')
            else:
                # Fallback text overlay
                canvas.create_text(width//2, height//2, 
                                 text="🔒 WhatsApp Blurred\nHover to reveal", 
                                 font=('Arial', 14, 'bold'), 
                                 fill='#666666', justify='center')
            
            # Bind hover events
            self.blur_window.bind('<Enter>', self.on_hover_enter)
            self.blur_window.bind('<Leave>', self.on_hover_leave)
            canvas.bind('<Enter>', self.on_hover_enter)
            canvas.bind('<Leave>', self.on_hover_leave)
            
            # Make click-through
            self.make_clickthrough()
            
            logger.info("✓ Blur window created successfully")
            
        except Exception as e:
            logger.error(f"Error creating blur window: {e}")
    
    def make_clickthrough(self):
        """Make window click-through"""
        if not self.blur_window:
            return
        
        try:
            hwnd = self.blur_window.winfo_id()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
            logger.debug("Window set to click-through")
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
    
    def debug_list_windows(self):
        """Debug function to list all windows for troubleshooting"""
        def enum_debug_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    rect = win32gui.GetWindowRect(hwnd)
                    
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        exe_name = process.name()
                    except:
                        exe_name = "unknown"
                    
                    if window_text or "whatsapp" in exe_name.lower():
                        windows.append(f"'{window_text}' | {class_name} | {exe_name} | {rect}")
                except:
                    pass
            return True
        
        windows = []
        win32gui.EnumWindows(enum_debug_callback, windows)
        
        logger.info("=== ALL VISIBLE WINDOWS DEBUG ===")
        for i, window in enumerate(windows[:20]):  # Show first 20
            logger.info(f"{i+1:2d}. {window}")
        logger.info("=================================")
        """Show blur if conditions are met"""
        if not self.is_blurred and self.is_enabled:
            self.show_blur()
    
    def show_blur(self):
        """Show blur overlay"""
        if not self.is_enabled or self.is_blurred:
            return
        
        logger.info("=== Activating Blur ===")
        
        # Find WhatsApp
        self.whatsapp_hwnd = self.find_whatsapp_window()
        if not self.whatsapp_hwnd:
            logger.warning("No WhatsApp window found")
            return
        
        # Capture screenshot
        screenshot = self.capture_whatsapp_screenshot()
        if not screenshot:
            logger.error("Screenshot capture failed")
            return
        
        # Create blur
        self.blur_cache = self.create_blurred_image(screenshot)
        if not self.blur_cache:
            logger.error("Blur creation failed")
            return
        
        # Create window
        self.create_blur_window()
        
        if self.blur_window:
            self.is_blurred = True
            logger.info("✅ BLUR ACTIVATED!")
        else:
            logger.error("Blur window creation failed")
    
    def hide_blur(self):
        """Hide blur overlay"""
        if self.blur_window:
            self.blur_window.destroy()
            self.blur_window = None
        self.is_blurred = False
        logger.info("Blur hidden")
    
    def toggle_blur(self):
        """Toggle blur on/off"""
        self.is_enabled = not self.is_enabled
        logger.info(f"Blur toggled: {'ON' if self.is_enabled else 'OFF'}")
        
        if self.is_enabled:
            self.ui_queue.put(('show_blur', None))
        else:
            self.ui_queue.put(('hide_blur', None))
        
        self.update_tray_menu()
    
    def setup_keyboard_shortcut(self):
        """Setup keyboard shortcut"""
        try:
            keyboard.add_hotkey(self.toggle_key, self.toggle_blur)
            logger.info(f"✓ Keyboard shortcut {self.toggle_key} registered")
        except Exception as e:
            logger.error(f"Failed to setup keyboard shortcut: {e}")
    
    def create_tray_icon(self):
        """Create system tray icon"""
        try:
            image = Image.new('RGB', (64, 64), color='darkblue')
            
            menu = pystray.Menu(
                item('Toggle Blur', self.toggle_blur),
                item('Test Screenshot', self.test_screenshot),
                item('Debug Windows', self.debug_list_windows),
                item('Show System Info', self.show_system_info),
                item('Exit', self.quit_application)
            )
            
            self.tray_icon = pystray.Icon("WhatsApp Blur Fixed", image, menu=menu)
            
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            logger.info("✓ System tray icon created")
        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
    
    def test_screenshot(self):
        """Test screenshot functionality"""
        try:
            logger.info("Testing screenshot capability...")
            test_img = ImageGrab.grab(bbox=(0, 0, 400, 300))
            test_path = "test_screenshot.png"
            test_img.save(test_path)
            
            messagebox.showinfo("Screenshot Test", 
                              f"✅ Screenshot test successful!\n"
                              f"Saved: {test_path}\n"
                              f"Size: {test_img.size}\n"
                              f"DPI Scale: {self.dpi_scale}")
            logger.info("Screenshot test successful")
        except Exception as e:
            logger.error(f"Screenshot test failed: {e}")
            messagebox.showerror("Screenshot Test", 
                               f"❌ Screenshot test failed!\n"
                               f"Error: {e}\n\n"
                               f"Check Windows Privacy Settings:\n"
                               f"Settings > Privacy & Security > Screen Recording")
    
    def show_system_info(self):
        """Show system information"""
        try:
            info_window = tk.Toplevel(self.root)
            info_window.title("System Information")
            info_window.geometry("400x300")
            info_window.attributes('-topmost', True)
            
            info_text = f"""System Information:

DPI Scale: {self.dpi_scale * 100:.0f}%
Admin Rights: {'Yes' if ctypes.windll.shell32.IsUserAnAdmin() else 'No'}
WhatsApp Found: {'Yes' if self.whatsapp_hwnd else 'No'}
Blur Active: {'Yes' if self.is_blurred else 'No'}

Troubleshooting:
1. Check Windows Privacy Settings
2. Set display scaling to 100%
3. Run as Administrator
4. Ensure WhatsApp is visible
5. Try on primary monitor only

Press {self.toggle_key} to toggle blur
"""
            
            tk.Label(info_window, text=info_text, justify='left', 
                    font=('Consolas', 9)).pack(pady=10, padx=10)
            
            tk.Button(info_window, text="Close", 
                     command=info_window.destroy).pack(pady=10)
        except Exception as e:
            logger.error(f"Error showing system info: {e}")
    
    def update_tray_menu(self):
        """Update tray menu"""
        if self.tray_icon:
            status = "ON" if self.is_enabled else "OFF"
            menu = pystray.Menu(
                item(f'Blur: {status}', self.toggle_blur),
                item('Test Screenshot', self.test_screenshot),
                item('Debug Windows', self.debug_list_windows),
                item('Show System Info', self.show_system_info),
                item('Exit', self.quit_application)
            )
            self.tray_icon.menu = menu
    
    def start_monitoring(self):
        """Start monitoring thread"""
        self.monitoring_thread = threading.Thread(target=self._monitor_whatsapp, daemon=True)
        self.monitoring_thread.start()
        logger.info("Monitoring thread started")
    
    def _monitor_whatsapp(self):
        """Monitor WhatsApp window"""
        while not self.shutdown_event.is_set():
            try:
                if self.is_enabled:
                    current_hwnd = self.find_whatsapp_window()
                    if current_hwnd and current_hwnd != self.whatsapp_hwnd:
                        self.whatsapp_hwnd = current_hwnd
                        if not self.is_blurred:
                            time.sleep(1)  # Small delay
                            self.ui_queue.put(('show_blur', None))
                    elif not current_hwnd and self.is_blurred:
                        self.ui_queue.put(('hide_blur', None))
                        self.whatsapp_hwnd = None
                
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)
    
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
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error processing UI queue: {e}")
        
        self.root.after(100, self.process_ui_queue)
    
    def quit_application(self):
        """Quit application"""
        logger.info("Quitting application")
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
        app = WhatsAppBlurFixed()
        
        messagebox.showinfo("WhatsApp Blur Fixed", 
                           f"WhatsApp Blur (DPI Fixed) started!\n\n"
                           f"• DPI Scale detected: {app.dpi_scale * 100:.0f}%\n"
                           f"• Press {app.toggle_key} to toggle blur\n"
                           f"• Right-click tray icon for options\n"
                           f"• Check system info for troubleshooting\n\n"
                           f"If blur doesn't work:\n"
                           f"1. Check Windows Privacy Settings\n"
                           f"2. Set display scaling to 100%\n"
                           f"3. Run as Administrator")
        
        app.root.mainloop()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        messagebox.showerror("Error", f"Failed to start: {e}")

if __name__ == "__main__":
    main()
