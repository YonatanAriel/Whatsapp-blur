#!/usr/bin/env python3
"""
WhatsApp Desktop Blur Application - Debug Version
Enhanced with comprehensive debugging and better window detection.
"""

import tkinter as tk
from tkinter import messagebox
import win32gui
import win32con
import win32api
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

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhatsAppBlurDebug:
    def __init__(self):
        self.whatsapp_hwnd = None
        self.blur_window = None
        self.is_blurred = False
        self.is_enabled = True
        self.hover_remove_blur = True
        self.toggle_key = 'ctrl+shift+b'
        self.debug_mode = True
        
        # Main tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("WhatsApp Blur Debug")
        
        # System tray icon
        self.tray_icon = None
        
        # Threading events and queue
        self.shutdown_event = threading.Event()
        self.monitoring_thread = None
        self.ui_queue = queue.Queue()
        
        # Screenshot and blur cache
        self.last_screenshot = None
        self.blur_cache = None
        self.whatsapp_rect = None
        
        logger.info("=== WhatsApp Blur Debug Version Started ===")
        self.check_admin_rights()
        self.list_all_windows()
        
        # Initialize the application
        self.setup_keyboard_shortcut()
        self.create_tray_icon()
        self.start_monitoring()
        self.process_ui_queue()
    
    def check_admin_rights(self):
        """Check if running with admin rights"""
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                logger.info("✓ Running with Administrator privileges")
            else:
                logger.warning("⚠ NOT running as Administrator - this may cause screenshot issues!")
                logger.warning("  Try: Right-click Command Prompt → 'Run as Administrator'")
        except Exception as e:
            logger.error(f"Error checking admin rights: {e}")
    
    def list_all_windows(self):
        """List all windows for debugging"""
        logger.info("=== Listing All Visible Windows ===")
        
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    if window_text or width > 100:  # Filter out tiny windows
                        logger.debug(f"Window: '{window_text}' | Class: '{class_name}' | Size: {width}x{height}")
                        
                        # Check for WhatsApp-related windows
                        if 'whatsapp' in window_text.lower() or 'whatsapp' in class_name.lower():
                            logger.info(f"🔍 FOUND WhatsApp window: '{window_text}' | Class: '{class_name}'")
                            windows.append((hwnd, window_text, class_name, rect))
                except Exception as e:
                    logger.debug(f"Error processing window {hwnd}: {e}")
            return True
        
        windows = []
        try:
            win32gui.EnumWindows(enum_callback, windows)
            if windows:
                logger.info(f"Found {len(windows)} WhatsApp-related windows")
                for i, (hwnd, text, class_name, rect) in enumerate(windows):
                    logger.info(f"  {i+1}. '{text}' ({class_name}) at {rect}")
            else:
                logger.warning("❌ No WhatsApp windows found!")
                logger.warning("   Make sure WhatsApp Desktop is open and visible")
        except Exception as e:
            logger.error(f"Error listing windows: {e}")
        
        logger.info("=== End Window List ===")
    
    def find_whatsapp_window(self):
        """Enhanced WhatsApp window detection with debugging"""
        logger.debug("Searching for WhatsApp Desktop window...")
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    # Multiple detection strategies
                    is_whatsapp = False
                    detection_reason = ""
                    
                    # Strategy 1: Window title contains WhatsApp
                    if 'WhatsApp' in window_text:
                        is_whatsapp = True
                        detection_reason = f"Window title: '{window_text}'"
                    
                    # Strategy 2: Chrome widget with WhatsApp-like size
                    elif 'Chrome_WidgetWin_1' in class_name:
                        rect = win32gui.GetWindowRect(hwnd)
                        width = rect[2] - rect[0]
                        height = rect[3] - rect[1]
                        
                        # WhatsApp Desktop typical size range
                        if 800 <= width <= 1600 and 600 <= height <= 1200:
                            is_whatsapp = True
                            detection_reason = f"Chrome widget with size {width}x{height}"
                    
                    if is_whatsapp:
                        rect = win32gui.GetWindowRect(hwnd)
                        width = rect[2] - rect[0]
                        height = rect[3] - rect[1]
                        
                        logger.info(f"✓ WhatsApp window detected: {detection_reason}")
                        logger.info(f"  Title: '{window_text}'")
                        logger.info(f"  Class: '{class_name}'")
                        logger.info(f"  Position: {rect}")
                        logger.info(f"  Size: {width}x{height}")
                        
                        windows.append((hwnd, window_text, class_name, rect))
                        
                except Exception as e:
                    logger.debug(f"Error checking window {hwnd}: {e}")
            return True
        
        windows = []
        try:
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                # Return the largest window (likely the main WhatsApp window)
                best_window = max(windows, key=lambda w: (w[3][2]-w[3][0]) * (w[3][3]-w[3][1]))
                hwnd, title, class_name, rect = best_window
                logger.info(f"Selected WhatsApp window: '{title}' ({class_name})")
                return hwnd
            else:
                logger.warning("❌ No WhatsApp Desktop window found!")
                return None
                
        except Exception as e:
            logger.error(f"Error finding WhatsApp window: {e}")
            return None
    
    def capture_whatsapp_screenshot(self):
        """Enhanced screenshot capture with debugging"""
        if not self.whatsapp_hwnd:
            logger.warning("No WhatsApp window handle available")
            return None
        
        try:
            # Get window position
            rect = win32gui.GetWindowRect(self.whatsapp_hwnd)
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            logger.debug(f"Capturing screenshot: {rect} (size: {width}x{height})")
            
            # Store rect for blur window positioning
            self.whatsapp_rect = rect
            
            # Test basic screenshot capability first
            try:
                test_screenshot = ImageGrab.grab()
                logger.debug(f"✓ Basic screenshot successful: {test_screenshot.size}")
            except Exception as e:
                logger.error(f"❌ Basic screenshot failed: {e}")
                logger.error("  This usually means permission issues - try running as Administrator")
                return None
            
            # Capture specific area
            try:
                screenshot = ImageGrab.grab(bbox=(x, y, x2, y2))
                logger.info(f"✓ WhatsApp area screenshot captured: {screenshot.size}")
                
                # Save debug screenshot
                if self.debug_mode:
                    debug_path = "debug_whatsapp_screenshot.png"
                    screenshot.save(debug_path)
                    logger.debug(f"Debug screenshot saved: {debug_path}")
                
                return screenshot
                
            except Exception as e:
                logger.error(f"❌ WhatsApp area screenshot failed: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error in capture_whatsapp_screenshot: {e}")
            return None
    
    def create_blurred_image(self, image):
        """Create blurred image with debugging"""
        if not image:
            logger.warning("No image provided for blurring")
            return None
        
        try:
            logger.debug(f"Creating blur effect for image: {image.size}")
            
            # Apply blur filter
            blurred = image.filter(ImageFilter.GaussianBlur(radius=15))
            
            # Add privacy overlay
            overlay = Image.new('RGBA', blurred.size, (200, 200, 200, 100))
            blurred = Image.alpha_composite(blurred.convert('RGBA'), overlay)
            
            # Save debug blurred image
            if self.debug_mode:
                debug_path = "debug_blurred_image.png"
                blurred.save(debug_path)
                logger.debug(f"Debug blurred image saved: {debug_path}")
            
            logger.info("✓ Blur effect created successfully")
            return blurred
            
        except Exception as e:
            logger.error(f"Error creating blurred image: {e}")
            return None
    
    def create_blur_window(self):
        """Enhanced blur window creation with debugging"""
        if not self.whatsapp_rect:
            logger.warning("No WhatsApp window rect available")
            return
        
        try:
            x, y, x2, y2 = self.whatsapp_rect
            width = x2 - x
            height = y2 - y
            
            logger.info(f"Creating blur window at {x},{y} size {width}x{height}")
            
            # Destroy existing window
            if self.blur_window:
                self.blur_window.destroy()
                logger.debug("Destroyed previous blur window")
            
            # Create new blur window
            self.blur_window = tk.Toplevel(self.root)
            self.blur_window.title("WhatsApp Blur Overlay")
            self.blur_window.geometry(f"{width}x{height}+{x}+{y}")
            self.blur_window.attributes('-topmost', True)
            self.blur_window.overrideredirect(True)
            self.blur_window.configure(bg='gray')
            
            logger.debug("Blur window created")
            
            # Create canvas
            canvas = tk.Canvas(self.blur_window, width=width, height=height, highlightthickness=0)
            canvas.pack()
            
            # Add content
            if self.blur_cache:
                try:
                    # Resize blur cache if needed
                    if self.blur_cache.size != (width, height):
                        resized_blur = self.blur_cache.resize((width, height), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(resized_blur)
                    else:
                        photo = ImageTk.PhotoImage(self.blur_cache)
                    
                    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                    canvas.image = photo  # Keep reference
                    logger.debug("✓ Blur image displayed")
                    
                except Exception as e:
                    logger.error(f"Error displaying blur image: {e}")
                    # Fallback to text
                    self._create_fallback_overlay(canvas, width, height)
            else:
                logger.warning("No blur cache available, using fallback")
                self._create_fallback_overlay(canvas, width, height)
            
            # Bind events
            self.blur_window.bind('<Enter>', self.on_hover_enter)
            self.blur_window.bind('<Leave>', self.on_hover_leave)
            canvas.bind('<Enter>', self.on_hover_enter)
            canvas.bind('<Leave>', self.on_hover_leave)
            
            # Make click-through
            self.make_clickthrough(True)
            
            logger.info("✓ Blur window created and configured")
            
        except Exception as e:
            logger.error(f"Error creating blur window: {e}")
    
    def _create_fallback_overlay(self, canvas, width, height):
        """Create fallback text overlay"""
        canvas.configure(bg='#E5E5E5')
        canvas.create_text(width//2, height//2, 
                         text="🔒 WhatsApp is blurred for privacy\nHover to reveal content\n\n(Debug mode active)", 
                         font=('Arial', 16, 'bold'), 
                         fill='#666666', 
                         justify='center')
        logger.debug("Fallback text overlay created")
    
    def make_clickthrough(self, enable=True):
        """Make window click-through with debugging"""
        if not self.blur_window:
            return
            
        try:
            hwnd = self.blur_window.winfo_id()
            if enable:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
                logger.debug("✓ Window set to click-through")
            else:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                style &= ~win32con.WS_EX_TRANSPARENT
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
                logger.debug("✓ Window set to interactive")
        except Exception as e:
            logger.error(f"Error setting click-through: {e}")
    
    def on_hover_enter(self, event):
        """Handle hover enter with debugging"""
        logger.debug("Mouse entered blur area")
        if self.hover_remove_blur and self.is_blurred:
            self.ui_queue.put(('hide_blur', None))
    
    def on_hover_leave(self, event):
        """Handle hover leave with debugging"""
        logger.debug("Mouse left blur area")
        if self.hover_remove_blur and self.is_enabled:
            self.root.after(500, lambda: self.ui_queue.put(('show_blur_if_enabled', None)))
    
    def show_blur_if_enabled(self):
        """Show blur if conditions are met"""
        if not self.is_blurred and self.is_enabled:
            logger.debug("Re-showing blur after hover delay")
            self.show_blur()
    
    def show_blur(self):
        """Enhanced show blur with comprehensive debugging"""
        logger.info("=== SHOW BLUR REQUESTED ===")
        
        if not self.is_enabled:
            logger.info("❌ Blur disabled, not showing")
            return
            
        if self.is_blurred:
            logger.info("❌ Blur already active")
            return
        
        # Find WhatsApp window
        logger.info("Step 1: Finding WhatsApp window...")
        self.whatsapp_hwnd = self.find_whatsapp_window()
        
        if not self.whatsapp_hwnd:
            logger.warning("❌ No WhatsApp window found!")
            logger.warning("   Make sure WhatsApp Desktop is open and visible")
            return
        
        # Capture screenshot
        logger.info("Step 2: Capturing screenshot...")
        screenshot = self.capture_whatsapp_screenshot()
        
        if not screenshot:
            logger.error("❌ Screenshot capture failed!")
            logger.error("   Try running as Administrator")
            return
        
        # Create blur
        logger.info("Step 3: Creating blur effect...")
        self.blur_cache = self.create_blurred_image(screenshot)
        
        if not self.blur_cache:
            logger.error("❌ Blur creation failed!")
            return
        
        # Create window
        logger.info("Step 4: Creating blur window...")
        self.create_blur_window()
        
        if self.blur_window:
            self.is_blurred = True
            logger.info("✅ BLUR ACTIVATED SUCCESSFULLY!")
        else:
            logger.error("❌ Blur window creation failed!")
    
    def hide_blur(self):
        """Hide blur with debugging"""
        logger.info("Hiding blur overlay")
        if self.blur_window:
            self.blur_window.destroy()
            self.blur_window = None
            logger.debug("Blur window destroyed")
        self.is_blurred = False
    
    def toggle_blur(self):
        """Toggle blur with debugging"""
        logger.info(f"=== BLUR TOGGLE: {self.is_enabled} → {not self.is_enabled} ===")
        self.is_enabled = not self.is_enabled
        
        if self.is_enabled:
            logger.info("Enabling blur...")
            self.ui_queue.put(('show_blur', None))
        else:
            logger.info("Disabling blur...")
            self.ui_queue.put(('hide_blur', None))
        
        self.update_tray_menu()
    
    def setup_keyboard_shortcut(self):
        """Setup keyboard shortcut with debugging"""
        try:
            keyboard.add_hotkey(self.toggle_key, self.toggle_blur)
            logger.info(f"✓ Keyboard shortcut {self.toggle_key} registered")
        except Exception as e:
            logger.error(f"❌ Failed to setup keyboard shortcut: {e}")
    
    def create_tray_icon(self):
        """Create tray icon with debugging"""
        try:
            image = Image.new('RGB', (64, 64), color='blue')
            
            menu = pystray.Menu(
                item('Toggle Blur', self.toggle_blur),
                item('Debug: List Windows', self.list_all_windows),
                item('Debug: Test Screenshot', self.test_screenshot),
                item('Toggle Hover Mode', self.toggle_hover_mode),
                item('Refresh Blur', self.refresh_blur),
                item('Settings', self.show_settings),
                item('Exit', self.quit_application)
            )
            
            self.tray_icon = pystray.Icon("WhatsApp Blur Debug", image, menu=menu)
            
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            logger.info("✓ System tray icon created with debug options")
        except Exception as e:
            logger.error(f"❌ Error creating tray icon: {e}")
    
    def test_screenshot(self):
        """Test screenshot capability"""
        logger.info("=== TESTING SCREENSHOT CAPABILITY ===")
        try:
            screenshot = ImageGrab.grab()
            test_path = "test_screenshot.png"
            screenshot.save(test_path)
            logger.info(f"✅ Screenshot test successful! Saved: {test_path}")
            messagebox.showinfo("Screenshot Test", f"✅ Screenshot successful!\nSaved: {test_path}\nSize: {screenshot.size}")
        except Exception as e:
            logger.error(f"❌ Screenshot test failed: {e}")
            messagebox.showerror("Screenshot Test", f"❌ Screenshot failed!\nError: {e}\n\nTry running as Administrator!")
    
    def update_tray_menu(self):
        """Update tray menu"""
        if self.tray_icon:
            status = "Enabled" if self.is_enabled else "Disabled"
            hover_status = "Enabled" if self.hover_remove_blur else "Disabled"
            
            menu = pystray.Menu(
                item(f'Blur: {status}', self.toggle_blur),
                item('Debug: List Windows', self.list_all_windows),
                item('Debug: Test Screenshot', self.test_screenshot),
                item(f'Hover Mode: {hover_status}', self.toggle_hover_mode),
                item('Refresh Blur', self.refresh_blur),
                item('Settings', self.show_settings),
                item('Exit', self.quit_application)
            )
            self.tray_icon.menu = menu
    
    def toggle_hover_mode(self):
        """Toggle hover mode"""
        self.hover_remove_blur = not self.hover_remove_blur
        self.update_tray_menu()
        logger.info(f"Hover mode: {'ON' if self.hover_remove_blur else 'OFF'}")
    
    def refresh_blur(self):
        """Refresh blur"""
        logger.info("Manual blur refresh requested")
        if self.is_blurred:
            self.ui_queue.put(('hide_blur', None))
            self.root.after(200, lambda: self.ui_queue.put(('show_blur', None)))
    
    def show_settings(self):
        """Show settings with debugging info"""
        try:
            settings_window = tk.Toplevel(self.root)
            settings_window.title("WhatsApp Blur Debug Settings")
            settings_window.geometry("500x400")
            settings_window.attributes('-topmost', True)
            
            # Status info
            tk.Label(settings_window, text="Debug Information", font=('Arial', 12, 'bold')).pack(pady=5)
            
            status_text = f"""
Admin Rights: {'✓' if self.check_admin_rights else '❌'}
WhatsApp Window: {'Found' if self.whatsapp_hwnd else 'Not Found'}
Blur Active: {'Yes' if self.is_blurred else 'No'}
Blur Enabled: {'Yes' if self.is_enabled else 'No'}
            """
            tk.Label(settings_window, text=status_text, justify='left').pack(pady=5)
            
            # Controls
            blur_var = tk.BooleanVar(value=self.is_enabled)
            tk.Checkbutton(settings_window, text="Enable Blur", 
                          variable=blur_var, 
                          command=lambda: setattr(self, 'is_enabled', blur_var.get())).pack(pady=5)
            
            hover_var = tk.BooleanVar(value=self.hover_remove_blur)
            tk.Checkbutton(settings_window, text="Hover to Reveal", 
                          variable=hover_var,
                          command=lambda: setattr(self, 'hover_remove_blur', hover_var.get())).pack(pady=5)
            
            # Debug buttons
            tk.Button(settings_window, text="List All Windows", 
                     command=self.list_all_windows).pack(pady=5)
            tk.Button(settings_window, text="Test Screenshot", 
                     command=self.test_screenshot).pack(pady=5)
            
            # Instructions
            instructions = tk.Text(settings_window, height=8, width=60)
            instructions.pack(pady=10, padx=10)
            instructions.insert('1.0', 
                "DEBUG VERSION - Instructions:\n\n"
                "1. Run as Administrator for screenshot permissions\n"
                "2. Ensure WhatsApp Desktop is open and visible\n"
                "3. Use debug buttons to test functionality\n"
                "4. Check console/log output for detailed info\n"
                f"5. Press {self.toggle_key} to toggle blur\n"
                "6. Check debug_*.png files if created\n\n"
                "If blur doesn't appear:\n"
                "- Try 'Test Screenshot' button\n"
                "- Check if running as Administrator\n"
                "- Verify WhatsApp Desktop is visible")
            instructions.config(state='disabled')
            
            tk.Button(settings_window, text="Close", 
                     command=settings_window.destroy).pack(pady=10)
        except Exception as e:
            logger.error(f"Error showing settings: {e}")
    
    def start_monitoring(self):
        """Start monitoring thread"""
        self.monitoring_thread = threading.Thread(target=self._monitor_whatsapp, daemon=True)
        self.monitoring_thread.start()
        logger.info("✓ Monitoring thread started")
    
    def _monitor_whatsapp(self):
        """Monitor WhatsApp with debugging"""
        monitor_count = 0
        while not self.shutdown_event.is_set():
            try:
                monitor_count += 1
                if monitor_count % 10 == 0:  # Log every 10 cycles
                    logger.debug(f"Monitor cycle {monitor_count}")
                
                if self.is_enabled:
                    current_hwnd = self.find_whatsapp_window()
                    if current_hwnd and current_hwnd != self.whatsapp_hwnd:
                        logger.info(f"New WhatsApp window detected: {current_hwnd}")
                        self.whatsapp_hwnd = current_hwnd
                        if not self.is_blurred:
                            logger.info("Scheduling blur activation for new window")
                            time.sleep(2)
                            self.ui_queue.put(('show_blur', None))
                    elif not current_hwnd and self.is_blurred:
                        logger.info("WhatsApp window closed, hiding blur")
                        self.ui_queue.put(('hide_blur', None))
                        self.whatsapp_hwnd = None
                
                time.sleep(3)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)
    
    def process_ui_queue(self):
        """Process UI queue with debugging"""
        try:
            while not self.ui_queue.empty():
                operation, data = self.ui_queue.get_nowait()
                logger.debug(f"Processing UI operation: {operation}")
                
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
        """Quit with cleanup"""
        logger.info("=== QUITTING APPLICATION ===")
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
    """Main entry point"""
    if not sys.platform.startswith('win'):
        print("This application is designed for Windows only.")
        return
    
    try:
        app = WhatsAppBlurDebug()
        
        messagebox.showinfo("WhatsApp Blur Debug", 
                           f"WhatsApp Blur DEBUG version started!\n\n"
                           f"✓ Check console output for detailed logs\n"
                           f"✓ Use {app.toggle_key} to toggle blur\n"
                           f"✓ Right-click tray icon for debug options\n"
                           f"✓ Run as Administrator if screenshots fail\n\n"
                           f"Debug files will be saved if created:\n"
                           f"- debug_whatsapp_screenshot.png\n"
                           f"- debug_blurred_image.png")
        
        app.root.mainloop()
            
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        messagebox.showerror("Error", f"Failed to start: {e}")

if __name__ == "__main__":
    main()
