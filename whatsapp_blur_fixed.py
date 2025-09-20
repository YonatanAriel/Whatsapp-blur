#!/usr/bin/env python3
"""
WhatsApp Desktop Blur Application for Windows 11
Fixed version - Uses screenshot-based blur to avoid window interference.
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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhatsAppBlur:
    def __init__(self):
        self.whatsapp_hwnd = None
        self.blur_window = None
        self.is_blurred = False
        self.is_enabled = True
        self.hover_remove_blur = True
        self.toggle_key = 'ctrl+shift+b'
        
        # Main tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window
        self.root.title("WhatsApp Blur")
        
        # System tray icon
        self.tray_icon = None
        
        # Threading events and queue for thread-safe operations
        self.shutdown_event = threading.Event()
        self.monitoring_thread = None
        self.ui_queue = queue.Queue()
        
        # Screenshot and blur cache
        self.last_screenshot = None
        self.blur_cache = None
        self.whatsapp_rect = None
        
        # Initialize the application
        self.setup_keyboard_shortcut()
        self.create_tray_icon()
        self.start_monitoring()
        self.process_ui_queue()
    
    def find_whatsapp_window(self):
        """Find WhatsApp Desktop window handle"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    if 'WhatsApp' in window_text and 'Chrome_WidgetWin_1' in class_name:
                        # Get window rect to verify it's a main window
                        rect = win32gui.GetWindowRect(hwnd)
                        width = rect[2] - rect[0]
                        height = rect[3] - rect[1]
                        if width > 300 and height > 400:  # Main window size check
                            windows.append(hwnd)
                except:
                    pass
            return True
        
        windows = []
        try:
            win32gui.EnumWindows(enum_windows_callback, windows)
            return windows[0] if windows else None
        except Exception as e:
            logger.error(f"Error finding WhatsApp window: {e}")
            return None
    
    def capture_whatsapp_screenshot(self):
        """Capture screenshot of WhatsApp window area"""
        if not self.whatsapp_hwnd:
            return None
        
        try:
            # Get WhatsApp window position and size
            rect = win32gui.GetWindowRect(self.whatsapp_hwnd)
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            # Store rect for blur window positioning
            self.whatsapp_rect = rect
            
            # Capture screenshot of the specific area
            screenshot = ImageGrab.grab(bbox=(x, y, x2, y2))
            return screenshot
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    def create_blurred_image(self, image):
        """Create a blurred version of the image"""
        if not image:
            return None
        
        try:
            # Apply blur filter
            blurred = image.filter(ImageFilter.GaussianBlur(radius=15))
            
            # Add privacy overlay
            overlay = Image.new('RGBA', blurred.size, (200, 200, 200, 100))
            blurred = Image.alpha_composite(blurred.convert('RGBA'), overlay)
            
            return blurred
        except Exception as e:
            logger.error(f"Error creating blurred image: {e}")
            return None
    
    def create_blur_window(self):
        """Create blur window with screenshot-based blur"""
        if not self.whatsapp_rect:
            return
        
        try:
            x, y, x2, y2 = self.whatsapp_rect
            width = x2 - x
            height = y2 - y
            
            # Create blur window
            if self.blur_window:
                self.blur_window.destroy()
            
            self.blur_window = tk.Toplevel(self.root)
            self.blur_window.title("WhatsApp Blur Overlay")
            self.blur_window.geometry(f"{width}x{height}+{x}+{y}")
            self.blur_window.attributes('-topmost', True)
            self.blur_window.overrideredirect(True)
            self.blur_window.configure(bg='gray')
            
            # Create canvas for blurred image
            canvas = tk.Canvas(self.blur_window, width=width, height=height, highlightthickness=0)
            canvas.pack()
            
            # Add blur image if available
            if self.blur_cache:
                try:
                    photo = ImageTk.PhotoImage(self.blur_cache)
                    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                    # Keep a reference to prevent garbage collection
                    canvas.image = photo
                except Exception as e:
                    logger.error(f"Error displaying blur image: {e}")
                    # Fallback to text overlay
                    canvas.configure(bg='#E5E5E5')
                    canvas.create_text(width//2, height//2, 
                                     text="🔒 WhatsApp is blurred for privacy\nHover to reveal content", 
                                     font=('Arial', 16, 'bold'), 
                                     fill='#666666', 
                                     justify='center')
            else:
                # Fallback overlay
                canvas.configure(bg='#E5E5E5')
                canvas.create_text(width//2, height//2, 
                                 text="🔒 WhatsApp is blurred for privacy\nHover to reveal content", 
                                 font=('Arial', 16, 'bold'), 
                                 fill='#666666', 
                                 justify='center')
            
            # Bind hover events
            self.blur_window.bind('<Enter>', self.on_hover_enter)
            self.blur_window.bind('<Leave>', self.on_hover_leave)
            canvas.bind('<Enter>', self.on_hover_enter)
            canvas.bind('<Leave>', self.on_hover_leave)
            
            # Make window click-through
            self.make_clickthrough(True)
            
        except Exception as e:
            logger.error(f"Error creating blur window: {e}")
    
    def make_clickthrough(self, enable=True):
        """Make the blur overlay click-through"""
        if not self.blur_window:
            return
            
        try:
            hwnd = self.blur_window.winfo_id()
            if enable:
                # Make window click-through
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
            else:
                # Make window interactive
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                style &= ~win32con.WS_EX_TRANSPARENT
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        except Exception as e:
            logger.error(f"Error setting click-through: {e}")
    
    def on_hover_enter(self, event):
        """Handle mouse entering blur overlay"""
        if self.hover_remove_blur and self.is_blurred:
            self.ui_queue.put(('hide_blur', None))
    
    def on_hover_leave(self, event):
        """Handle mouse leaving blur overlay"""
        if self.hover_remove_blur and self.is_enabled:
            # Small delay to prevent flickering
            self.root.after(500, lambda: self.ui_queue.put(('show_blur_if_enabled', None)))
    
    def show_blur_if_enabled(self):
        """Show blur if still enabled and mouse is not over window"""
        if not self.is_blurred and self.is_enabled:
            self.show_blur()
    
    def show_blur(self):
        """Show the blur overlay"""
        if not self.is_enabled or self.is_blurred:
            return
            
        self.whatsapp_hwnd = self.find_whatsapp_window()
        if self.whatsapp_hwnd:
            # Capture and blur screenshot
            screenshot = self.capture_whatsapp_screenshot()
            if screenshot:
                self.blur_cache = self.create_blurred_image(screenshot)
            
            self.create_blur_window()
            self.is_blurred = True
            logger.info("Blur overlay activated")
    
    def hide_blur(self):
        """Hide the blur overlay"""
        if self.blur_window:
            self.blur_window.destroy()
            self.blur_window = None
        self.is_blurred = False
        logger.info("Blur overlay deactivated")
    
    def toggle_blur(self):
        """Toggle blur on/off"""
        self.is_enabled = not self.is_enabled
        if self.is_enabled:
            self.ui_queue.put(('show_blur', None))
        else:
            self.ui_queue.put(('hide_blur', None))
        
        # Update tray icon menu
        self.update_tray_menu()
        logger.info(f"Blur toggled: {'ON' if self.is_enabled else 'OFF'}")
    
    def setup_keyboard_shortcut(self):
        """Setup global keyboard shortcut"""
        try:
            keyboard.add_hotkey(self.toggle_key, self.toggle_blur)
            logger.info(f"Keyboard shortcut {self.toggle_key} registered")
        except Exception as e:
            logger.error(f"Failed to setup keyboard shortcut: {e}")
    
    def create_tray_icon(self):
        """Create system tray icon"""
        try:
            # Create a simple icon
            image = Image.new('RGB', (64, 64), color='blue')
            
            menu = pystray.Menu(
                item('Toggle Blur', self.toggle_blur),
                item('Toggle Hover Mode', self.toggle_hover_mode),
                item('Refresh Blur', self.refresh_blur),
                item('Settings', self.show_settings),
                item('Exit', self.quit_application)
            )
            
            self.tray_icon = pystray.Icon("WhatsApp Blur", image, menu=menu)
            
            # Start tray icon in separate thread
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            logger.info("System tray icon created")
        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
    
    def update_tray_menu(self):
        """Update tray icon menu"""
        if self.tray_icon:
            status = "Enabled" if self.is_enabled else "Disabled"
            hover_status = "Enabled" if self.hover_remove_blur else "Disabled"
            
            menu = pystray.Menu(
                item(f'Blur: {status}', self.toggle_blur),
                item(f'Hover Mode: {hover_status}', self.toggle_hover_mode),
                item('Refresh Blur', self.refresh_blur),
                item('Settings', self.show_settings),
                item('Exit', self.quit_application)
            )
            self.tray_icon.menu = menu
    
    def toggle_hover_mode(self):
        """Toggle hover to reveal mode"""
        self.hover_remove_blur = not self.hover_remove_blur
        self.update_tray_menu()
        logger.info(f"Hover mode toggled: {'ON' if self.hover_remove_blur else 'OFF'}")
    
    def refresh_blur(self):
        """Manually refresh the blur overlay"""
        if self.is_blurred:
            self.ui_queue.put(('hide_blur', None))
            self.root.after(100, lambda: self.ui_queue.put(('show_blur', None)))
    
    def show_settings(self):
        """Show settings dialog"""
        try:
            settings_window = tk.Toplevel(self.root)
            settings_window.title("WhatsApp Blur Settings")
            settings_window.geometry("400x350")
            settings_window.attributes('-topmost', True)
            
            # Blur toggle
            blur_var = tk.BooleanVar(value=self.is_enabled)
            tk.Checkbutton(settings_window, text="Enable Blur", 
                          variable=blur_var, 
                          command=lambda: setattr(self, 'is_enabled', blur_var.get())).pack(pady=10)
            
            # Hover mode toggle
            hover_var = tk.BooleanVar(value=self.hover_remove_blur)
            tk.Checkbutton(settings_window, text="Hover to Reveal", 
                          variable=hover_var,
                          command=lambda: setattr(self, 'hover_remove_blur', hover_var.get())).pack(pady=5)
            
            # Keyboard shortcut display
            tk.Label(settings_window, text=f"Keyboard Shortcut: {self.toggle_key}", 
                    font=('Arial', 10)).pack(pady=10)
            
            # Auto-start button
            tk.Button(settings_window, text="Enable Auto-Start", 
                     command=self.setup_auto_start).pack(pady=5)
            
            # Instructions
            instructions = tk.Text(settings_window, height=10, width=50)
            instructions.pack(pady=10, padx=10)
            instructions.insert('1.0', 
                "Instructions:\n\n"
                f"• Press {self.toggle_key} to toggle blur on/off\n"
                "• Right-click tray icon for quick access\n"
                "• Hover over blurred area to reveal content\n"
                "• Blur automatically applies when WhatsApp is detected\n"
                "• Use 'Refresh Blur' if the overlay gets out of sync\n"
                "• Click 'Enable Auto-Start' to run on Windows startup\n"
                "• Close this window to apply settings")
            instructions.config(state='disabled')
            
            # Close button
            tk.Button(settings_window, text="Close", 
                     command=settings_window.destroy).pack(pady=10)
        except Exception as e:
            logger.error(f"Error showing settings: {e}")
    
    def setup_auto_start(self):
        """Setup auto-start on Windows boot"""
        try:
            startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            batch_file = os.path.join(startup_folder, 'WhatsApp_Blur.bat')
            
            script_path = os.path.abspath(__file__)
            script_dir = os.path.dirname(script_path)
            
            batch_content = f'''@echo off
cd /d "{script_dir}"
python "{script_path}"
'''
            
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            messagebox.showinfo("Auto-Start", "Auto-start has been enabled! WhatsApp Blur will now start with Windows.")
            logger.info("Auto-start enabled")
        except Exception as e:
            logger.error(f"Error setting up auto-start: {e}")
            messagebox.showerror("Auto-Start Error", f"Failed to enable auto-start: {e}")
    
    def start_monitoring(self):
        """Start monitoring WhatsApp window"""
        self.monitoring_thread = threading.Thread(target=self._monitor_whatsapp, daemon=True)
        self.monitoring_thread.start()
        logger.info("Monitoring thread started")
    
    def _monitor_whatsapp(self):
        """Monitor WhatsApp window in background"""
        while not self.shutdown_event.is_set():
            try:
                if self.is_enabled:
                    current_hwnd = self.find_whatsapp_window()
                    if current_hwnd and current_hwnd != self.whatsapp_hwnd:
                        self.whatsapp_hwnd = current_hwnd
                        if not self.is_blurred:
                            # Small delay to let WhatsApp fully load
                            time.sleep(2)
                            self.ui_queue.put(('show_blur', None))
                    elif not current_hwnd and self.is_blurred:
                        # WhatsApp closed
                        self.ui_queue.put(('hide_blur', None))
                        self.whatsapp_hwnd = None
                
                time.sleep(3)  # Check every 3 seconds (reduced frequency)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)
    
    def process_ui_queue(self):
        """Process UI operations from queue in main thread"""
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
        
        # Schedule next queue processing
        self.root.after(100, self.process_ui_queue)
    
    def quit_application(self):
        """Quit the application"""
        logger.info("Quitting application")
        self.shutdown_event.set()
        self.hide_blur()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Unregister keyboard shortcut
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
        # Create and run the blur application
        app = WhatsAppBlur()
        
        # Show initial notification
        messagebox.showinfo("WhatsApp Blur", 
                           f"WhatsApp Blur is now running!\n\n"
                           f"• Press {app.toggle_key} to toggle blur\n"
                           f"• Check system tray for options\n"
                           f"• Hover over blurred content to reveal\n"
                           f"• Uses screenshot-based blur (no interference)")
        
        # Start the main loop
        app.root.mainloop()
            
    except Exception as e:
        logger.error(f"Failed to start WhatsApp Blur: {e}")
        messagebox.showerror("Error", f"Failed to start WhatsApp Blur: {e}")

if __name__ == "__main__":
    main()
