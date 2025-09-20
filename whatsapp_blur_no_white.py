#!/usr/bin/env python3
"""
WhatsApp Blur - NO WHITE WINDOW VERSION
Solves the white freezing window with loading cursor issue
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

class WhatsAppBlurNoWhite:
    def __init__(self):
        # Fix DPI awareness FIRST
        self.fix_dpi_awareness()
        
        self.whatsapp_hwnd = None
        self.blur_window = None
        self.is_blurred = False
        self.is_enabled = True  # Auto-blur is enabled by default
        self.hover_remove_blur = True
        self.toggle_key = 'ctrl+alt+q'
        self.auto_blur_mode = True  # NEW: Auto-blur when WhatsApp is visible
        
        # Safety: prevent rapid blur attempts
        self.last_blur_attempt = 0
        self.min_blur_interval = 1.0  # Reduced for better responsiveness
        self.capturing_screenshot = False
        
        # Hover state tracking
        self.is_hovering = False
        self.hover_timer = None
        
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
        
        print("🚀 WhatsApp Blur (Auto-Blur Mode) initialized successfully!")
        print(f"📝 Press {self.toggle_key} to toggle auto-blur on/off")
        print("🔄 Auto-blur will activate when WhatsApp is visible")
        print("🖱️ Hover to temporarily reveal, stop hovering to blur again")
    
    def fix_dpi_awareness(self):
        """Fix DPI awareness to prevent blurry window positioning"""
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass
    
    def test_screenshot_permission(self):
        """Test if we can take screenshots (for Windows 11 privacy)"""
        print("🔍 Testing screenshot permissions...")
        try:
            test_shot = ImageGrab.grab(bbox=(0, 0, 100, 100))
            if test_shot and test_shot.size == (100, 100):
                print("✅ Screenshot permissions working")
                return True
            else:
                print("❌ Screenshot returned invalid size")
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
    
    def is_whatsapp_currently_visible(self, hwnd):
        """Check if WhatsApp is actually visible and in the foreground - IMPROVED"""
        try:
            if not hwnd or not win32gui.IsWindowVisible(hwnd):
                print("❌ WhatsApp window not visible or invalid handle")
                return False
            
            # Check if minimized
            if win32gui.IsIconic(hwnd):
                print("❌ WhatsApp is minimized")
                return False
            
            # Get current window rect
            try:
                current_rect = win32gui.GetWindowRect(hwnd)
                x, y, x2, y2 = current_rect
                width = x2 - x
                height = y2 - y
                
                # Check if window is actually on screen with reasonable size
                if width < 200 or height < 200:
                    print(f"❌ WhatsApp window too small: {width}x{height}")
                    return False
                
                # Check if window is mostly on screen
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                
                if x2 < 0 or y2 < 0 or x > screen_width or y > screen_height:
                    print(f"❌ WhatsApp window off-screen: {x},{y} to {x2},{y2}")
                    return False
                
                # CRITICAL: Check if window is actually in foreground or visible
                # Get the foreground window
                foreground_hwnd = win32gui.GetForegroundWindow()
                
                # Check if WhatsApp is the foreground window OR is visible behind foreground
                if hwnd == foreground_hwnd:
                    print("✅ WhatsApp is in foreground")
                    self.whatsapp_rect = current_rect
                    return True
                else:
                    # Check if WhatsApp window is actually visible (not covered)
                    # by trying to find it in the window z-order
                    try:
                        # Get window title to verify it's really WhatsApp
                        window_title = win32gui.GetWindowText(hwnd)
                        if not window_title or "whatsapp" not in window_title.lower():
                            print(f"❌ Window title doesn't contain WhatsApp: '{window_title}'")
                            return False
                        
                        # Check if window area is mostly visible (not covered by other windows)
                        # We'll consider it visible if it's not minimized and has reasonable size
                        print(f"✅ WhatsApp visible but not in foreground: '{window_title}'")
                        self.whatsapp_rect = current_rect
                        return True
                        
                    except Exception as e:
                        print(f"❌ Error checking window visibility: {e}")
                        return False
                
            except Exception as e:
                print(f"❌ Error getting window rect: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error in visibility check: {e}")
            return False
    
    def find_whatsapp_window(self):
        """Find WhatsApp window with improved prioritization"""
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
                    
                    # Priority scoring system
                    priority = 0
                    
                    # Desktop WhatsApp (highest priority)
                    if exe_name == "whatsapp.exe":
                        priority = 100
                        
                    # UWP WhatsApp
                    elif ("whatsapp" in window_text.lower() and 
                          "applicationframehost.exe" in exe_name):
                        priority = 90
                        
                    # Web WhatsApp in browsers (lower priority)
                    elif ("whatsapp" in window_text.lower() and 
                          exe_name in ["chrome.exe", "firefox.exe", "msedge.exe"]):
                        priority = 50
                    
                    if priority > 0:
                        windows.append((hwnd, priority, window_text, class_name, exe_name))
                        
                except Exception:
                    pass
            return True
        
        windows = []
        try:
            win32gui.EnumWindows(enum_callback, windows)
            
            if windows:
                # Sort by priority (highest first) and get the best match
                windows.sort(key=lambda x: x[1], reverse=True)
                best_hwnd = windows[0][0]
                
                # Verify this window is actually visible
                if self.is_whatsapp_currently_visible(best_hwnd):
                    return best_hwnd
                    
        except Exception as e:
            logger.error(f"Error finding WhatsApp window: {e}")
        
        return None
    
    def capture_whatsapp_screenshot(self, hwnd):
        """Capture screenshot of WhatsApp window with safety checks"""
        if self.capturing_screenshot:
            return None
            
        try:
            self.capturing_screenshot = True
            
            # Get exact window rect
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            
            # Safety check - don't capture if window is too small
            width = x2 - x
            height = y2 - y
            if width < 100 or height < 100:
                return None
            
            # Brief delay to ensure window is stable
            time.sleep(0.1)
            
            # Capture the screenshot
            screenshot = ImageGrab.grab(bbox=(x, y, x2, y2))
            
            if screenshot and screenshot.size == (width, height):
                return screenshot
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
        finally:
            self.capturing_screenshot = False
    
    def create_blurred_image(self, image):
        """Create blurred version of image with strong blur effect"""
        if not image:
            return None
            
        try:
            # Apply strong Gaussian blur - increased radius for better privacy
            blurred = image.filter(ImageFilter.GaussianBlur(radius=40))
            return blurred
        except Exception as e:
            logger.error(f"Error creating blurred image: {e}")
            return None
    
    def create_blur_window_no_white(self, x, y, width, height):
        """Create blur window with NO WHITE SCREEN - the proper solution"""
        try:
            print(f"🪟 Creating NO-WHITE blur window at ({x}, {y}) size {width}x{height}")
            
            # Destroy existing window first
            if self.blur_window:
                self.blur_window.destroy()
                self.blur_window = None
                # Small delay to ensure complete cleanup
                self.root.update_idletasks()
                time.sleep(0.1)
            
            # Create new toplevel window
            self.blur_window = tk.Toplevel(self.root)
            
            # CRITICAL FIX: Withdraw window IMMEDIATELY to prevent white flash
            self.blur_window.withdraw()
            
            # Set all window properties while HIDDEN
            self.blur_window.overrideredirect(True)
            self.blur_window.configure(bg='black')
            self.blur_window.attributes('-topmost', True)
            self.blur_window.attributes('-alpha', 1.0)
            
            # Set geometry while HIDDEN
            self.blur_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create and configure all content while HIDDEN
            canvas = tk.Canvas(self.blur_window, 
                             width=width, height=height,
                             bg='black', highlightthickness=0)
            canvas.pack(fill='both', expand=True)
            
            # Prepare image content while HIDDEN
            image_loaded = False
            if self.blur_cache:
                try:
                    # Resize image to exact window size
                    if self.blur_cache.size != (width, height):
                        resized = self.blur_cache.resize((width, height), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(resized)
                    else:
                        photo = ImageTk.PhotoImage(self.blur_cache)
                    
                    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                    canvas.image = photo  # Keep reference
                    image_loaded = True
                    print("✅ Blur image loaded while window hidden")
                    
                except Exception as e:
                    print(f"⚠️ Image loading error: {e}")
                    image_loaded = False
            
            # Add fallback text if no image
            if not image_loaded:
                canvas.create_text(width//2, height//2, 
                                 text="🔒 WhatsApp Blurred\nHover to reveal", 
                                 font=('Arial', 16, 'bold'), 
                                 fill='white', justify='center')
                print("✅ Text content loaded while window hidden")
            
            # Bind hover events while HIDDEN
            if self.hover_remove_blur:
                self.blur_window.bind('<Enter>', self.on_hover_enter)
                self.blur_window.bind('<Leave>', self.on_hover_leave)
                canvas.bind('<Enter>', self.on_hover_enter)
                canvas.bind('<Leave>', self.on_hover_leave)
            
            # CRITICAL: Update all content while window is STILL HIDDEN
            self.blur_window.update_idletasks()
            self.blur_window.update()
            
            # ONLY NOW show the window - all content is ready!
            print("🎬 Showing window with content ready...")
            self.blur_window.deiconify()
            
            # Apply Win32 positioning after window is shown
            try:
                # Small delay to ensure window is fully shown
                time.sleep(0.05)
                hwnd = self.blur_window.winfo_id()
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 
                                    x, y, width, height,
                                    win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE)
                print("✅ Win32 positioning applied")
            except Exception as e:
                print(f"⚠️ Win32 positioning warning: {e}")
            
            # Final updates
            self.blur_window.update_idletasks()
            
            print("🎉 SUCCESS: Blur window shown with NO WHITE SCREEN!")
            
        except Exception as e:
            print(f"❌ Error creating blur window: {e}")
            logger.error(f"Error creating blur window: {e}")
            if self.blur_window:
                try:
                    self.blur_window.destroy()
                except:
                    pass
                self.blur_window = None
    
    def show_blur(self):
        """Show blur overlay on WhatsApp with improved validation"""
        # Don't blur if auto-blur is disabled
        if not self.is_enabled:
            print("⏸️ Auto-blur disabled")
            return
            
        # Don't blur if currently hovering
        if self.is_hovering:
            print("🖱️ Currently hovering - not blurring")
            return
            
        # Safety check: don't blur too frequently
        current_time = time.time()
        if current_time - self.last_blur_attempt < self.min_blur_interval:
            print(f"⏰ Too soon - waiting {self.min_blur_interval}s")
            return
        
        self.last_blur_attempt = current_time
        
        if self.is_blurred:
            print("ℹ️ Already blurred")
            return  # Already blurred
        
        # Find WhatsApp window
        print("🔍 Finding WhatsApp window...")
        hwnd = self.find_whatsapp_window()
        if not hwnd:
            print("❌ WhatsApp window not found")
            return  # WhatsApp not found
        
        # CRITICAL: Double-check it's actually visible with detailed logging
        print("🔍 Verifying WhatsApp visibility...")
        if not self.is_whatsapp_currently_visible(hwnd):
            print("❌ WhatsApp visibility check failed")
            return  # WhatsApp not currently visible
        
        self.whatsapp_hwnd = hwnd
        print("✅ WhatsApp window verified as visible")
        
        # Get window position
        x, y, x2, y2 = self.whatsapp_rect
        width = x2 - x
        height = y2 - y
        
        print(f"📐 WhatsApp position: {x}, {y}, size: {width}x{height}")
        
        # Capture and blur screenshot
        print("📸 Capturing screenshot...")
        screenshot = self.capture_whatsapp_screenshot(hwnd)
        if screenshot:
            print("🔄 Creating blur effect...")
            self.blur_cache = self.create_blurred_image(screenshot)
            print("✅ Blur effect created")
        else:
            print("⚠️ Screenshot failed, will show text overlay")
            self.blur_cache = None
        
        # Create blur window with NO WHITE SCREEN method
        print("🪟 Creating blur window...")
        self.create_blur_window_no_white(x, y, width, height)
        
        if self.blur_window:
            self.is_blurred = True
            print("🔒 Auto-blur activated successfully!")
        else:
            print("❌ Failed to create blur window")
    
    def hide_blur(self):
        """Hide blur overlay with logging"""
        if self.blur_window:
            print("🔓 Removing blur overlay")
            self.blur_window.destroy()
            self.blur_window = None
        
        self.is_blurred = False
        self.blur_cache = None
    
    def toggle_auto_blur(self):
        """Toggle auto-blur mode on/off"""
        self.is_enabled = not self.is_enabled
        if self.is_enabled:
            print("🔄 Auto-blur ENABLED - will blur when WhatsApp is visible")
            # Immediately try to blur if WhatsApp is visible
            self.ui_queue.put(('check_and_blur', None))
        else:
            print("⏸️ Auto-blur DISABLED - blur removed")
            self.hide_blur()
    
    def on_hover_enter(self, event):
        """Handle hover enter - temporarily remove blur"""
        print("🖱️ Hover detected - temporarily removing blur")
        self.is_hovering = True
        if self.is_blurred:
            self.hide_blur()
    
    def on_hover_leave(self, event):
        """Handle hover leave - restore blur immediately"""
        print("🖱️ Hover ended - restoring blur")
        self.is_hovering = False
        # Use a small delay to avoid flicker
        if self.hover_timer:
            self.hover_timer.cancel()
        
        def restore_blur():
            if not self.is_hovering and self.is_enabled:  # Double-check we're not hovering again
                self.ui_queue.put(('show_blur', None))
        
        self.hover_timer = threading.Timer(0.2, restore_blur)  # 200ms delay
        self.hover_timer.start()
    
    def setup_hotkey(self):
        """Setup keyboard hotkey to toggle auto-blur mode"""
        def hotkey_handler():
            self.ui_queue.put(('toggle_auto_blur', None))
        
        try:
            keyboard.add_hotkey(self.toggle_key, hotkey_handler)
            print(f"⌨️ Hotkey {self.toggle_key} registered (toggles auto-blur)")
        except Exception as e:
            logger.error(f"Error setting up hotkey: {e}")
    
    def start_monitoring(self):
        """Start monitoring thread with simple and reliable auto-blur"""
        def monitor():
            last_check_time = 0
            check_interval = 1.0  # Check every 1 second
            
            while True:
                try:
                    # Process UI queue first
                    try:
                        action, data = self.ui_queue.get_nowait()
                        if action == 'toggle_auto_blur':
                            self.toggle_auto_blur()
                        elif action == 'show_blur':
                            self.show_blur()
                        elif action == 'hide_blur':
                            self.hide_blur()
                        elif action == 'check_and_blur':
                            # Force immediate check by resetting timer
                            last_check_time = 0
                        elif action == 'quit':
                            break
                    except queue.Empty:
                        pass
                    
                    # Simple auto-blur logic
                    current_time = time.time()
                    if current_time - last_check_time >= check_interval:
                        last_check_time = current_time
                        
                        # Only do auto-blur checks if enabled and not hovering
                        if self.is_enabled and not self.is_hovering:
                            hwnd = self.find_whatsapp_window()
                            whatsapp_is_visible = hwnd and self.is_whatsapp_currently_visible(hwnd)
                            
                            if whatsapp_is_visible and not self.is_blurred:
                                # WhatsApp visible but not blurred - add blur
                                self.show_blur()
                            elif not whatsapp_is_visible and self.is_blurred:
                                # WhatsApp not visible but blurred - remove blur
                                self.hide_blur()
                        elif not self.is_enabled and self.is_blurred:
                            # Auto-blur disabled - remove blur
                            self.hide_blur()
                    
                    time.sleep(0.1)  # Fast loop for UI responsiveness
                    
                except Exception as e:
                    logger.error(f"Monitor error: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def create_system_tray(self):
        """Create system tray icon"""
        def quit_app(icon, item):
            self.ui_queue.put(('quit', None))
            self.hide_blur()
            icon.stop()
            self.root.quit()
        
        def toggle_auto_blur_tray(icon, item):
            self.ui_queue.put(('toggle_auto_blur', None))
        
        def toggle_hover(icon, item):
            self.hover_remove_blur = not self.hover_remove_blur
            status = "enabled" if self.hover_remove_blur else "disabled"
            print(f"🖱️ Hover to remove blur {status}")
        
        # Create simple icon (white square)
        image = Image.new('RGB', (64, 64), color='white')
        
        menu = pystray.Menu(
            item('Toggle Auto-Blur (Ctrl+Alt+Q)', toggle_auto_blur_tray),
            item('Hover to Remove', toggle_hover),
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
            print(f"📝 Press {self.toggle_key} to toggle auto-blur on/off")
            print("📍 Check system tray for more options")
            print("🎯 Auto-blur activates when WhatsApp is visible!")
            print("🖱️ Hover over blur to temporarily reveal content")
            
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        except Exception as e:
            logger.error(f"Main loop error: {e}")
        finally:
            self.hide_blur()
            if hasattr(self, 'icon'):
                self.icon.stop()

def main():
    app = WhatsAppBlurNoWhite()
    app.run()

if __name__ == "__main__":
    main()
