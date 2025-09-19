#!/usr/bin/env python3
"""
WhatsApp Desktop Blur Application for Windows 11
Provides privacy by blurring WhatsApp content, with hover to reveal functionality.
"""

import tkinter as tk
from tkinter import messagebox
import win32gui
import win32con
import win32api
import win32process
import psutil
import threading
import time
import sys
import os
from PIL import Image, ImageTk, ImageFilter
import pystray
from pystray import MenuItem as item
import keyboard
import ctypes
from ctypes import wintypes

class WhatsAppBlur:
    def __init__(self):
        self.whatsapp_hwnd = None
        self.blur_window = None
        self.is_blurred = False
        self.is_enabled = True
        self.hover_remove_blur = True
        self.toggle_key = 'ctrl+shift+b'  # Custom keyboard shortcut
        
        # System tray icon
        self.tray_icon = None
        
        # Threading events
        self.shutdown_event = threading.Event()
        self.monitoring_thread = None
        
        # Initialize the application
        self.setup_keyboard_shortcut()
        self.create_tray_icon()
        self.start_monitoring()
    
    def find_whatsapp_window(self):
        """Find WhatsApp Desktop window handle"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                if 'WhatsApp' in window_text or 'whatsapp' in class_name.lower():
                    windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0] if windows else None
    
    def create_blur_overlay(self):
        """Create a blur overlay window"""
        if not self.whatsapp_hwnd:
            return
        
        # Get WhatsApp window position and size
        rect = win32gui.GetWindowRect(self.whatsapp_hwnd)
        x, y, x2, y2 = rect
        width = x2 - x
        height = y2 - y
        
        # Create blur overlay window
        if self.blur_window:
            self.blur_window.destroy()
        
        self.blur_window = tk.Toplevel()
        self.blur_window.title("WhatsApp Blur Overlay")
        self.blur_window.geometry(f"{width}x{height}+{x}+{y}")
        self.blur_window.configure(bg='#E5E5E5')
        self.blur_window.attributes('-alpha', 0.8)
        self.blur_window.attributes('-topmost', True)
        self.blur_window.overrideredirect(True)
        
        # Create blur effect using a semi-transparent overlay
        canvas = tk.Canvas(self.blur_window, width=width, height=height, 
                          bg='#E5E5E5', highlightthickness=0)
        canvas.pack()
        
        # Add privacy message
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
        
        # Make window click-through when not hovering
        self.make_clickthrough(True)
    
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
        except:
            pass
    
    def on_hover_enter(self, event):
        """Handle mouse entering blur overlay"""
        if self.hover_remove_blur and self.is_blurred:
            self.hide_blur()
    
    def on_hover_leave(self, event):
        """Handle mouse leaving blur overlay"""
        if self.hover_remove_blur and self.is_enabled:
            # Small delay to prevent flickering
            self.blur_window.after(100, self.show_blur_if_enabled)
    
    def show_blur_if_enabled(self):
        """Show blur if still enabled and mouse is not over window"""
        try:
            x, y = self.blur_window.winfo_pointerxy()
            widget = self.blur_window.winfo_containing(x, y)
            if widget != self.blur_window and not self.is_blurred and self.is_enabled:
                self.show_blur()
        except:
            if not self.is_blurred and self.is_enabled:
                self.show_blur()
    
    def show_blur(self):
        """Show the blur overlay"""
        if not self.is_enabled or self.is_blurred:
            return
            
        self.whatsapp_hwnd = self.find_whatsapp_window()
        if self.whatsapp_hwnd:
            self.create_blur_overlay()
            self.is_blurred = True
    
    def hide_blur(self):
        """Hide the blur overlay"""
        if self.blur_window:
            self.blur_window.withdraw()
        self.is_blurred = False
    
    def toggle_blur(self):
        """Toggle blur on/off"""
        self.is_enabled = not self.is_enabled
        if self.is_enabled:
            self.show_blur()
        else:
            self.hide_blur()
        
        # Update tray icon menu
        self.update_tray_menu()
    
    def setup_keyboard_shortcut(self):
        """Setup global keyboard shortcut"""
        try:
            keyboard.add_hotkey(self.toggle_key, self.toggle_blur)
        except Exception as e:
            print(f"Failed to setup keyboard shortcut: {e}")
    
    def create_tray_icon(self):
        """Create system tray icon"""
        # Create a simple icon
        image = Image.new('RGB', (64, 64), color='blue')
        
        menu = pystray.Menu(
            item('Toggle Blur', self.toggle_blur),
            item('Toggle Hover Mode', self.toggle_hover_mode),
            item('Settings', self.show_settings),
            item('Exit', self.quit_application)
        )
        
        self.tray_icon = pystray.Icon("WhatsApp Blur", image, menu=menu)
        
        # Start tray icon in separate thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
    
    def update_tray_menu(self):
        """Update tray icon menu"""
        if self.tray_icon:
            status = "Enabled" if self.is_enabled else "Disabled"
            hover_status = "Enabled" if self.hover_remove_blur else "Disabled"
            
            menu = pystray.Menu(
                item(f'Blur: {status}', self.toggle_blur),
                item(f'Hover Mode: {hover_status}', self.toggle_hover_mode),
                item('Settings', self.show_settings),
                item('Exit', self.quit_application)
            )
            self.tray_icon.menu = menu
    
    def toggle_hover_mode(self):
        """Toggle hover to reveal mode"""
        self.hover_remove_blur = not self.hover_remove_blur
        self.update_tray_menu()
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel()
        settings_window.title("WhatsApp Blur Settings")
        settings_window.geometry("400x300")
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
        
        # Instructions
        instructions = tk.Text(settings_window, height=8, width=50)
        instructions.pack(pady=10, padx=10)
        instructions.insert('1.0', 
            "Instructions:\n\n"
            f"• Press {self.toggle_key} to toggle blur on/off\n"
            "• Right-click tray icon for quick access\n"
            "• Hover over blurred area to reveal content\n"
            "• Blur automatically applies when WhatsApp is detected\n"
            "• Close this window to apply settings")
        instructions.config(state='disabled')
        
        # Close button
        tk.Button(settings_window, text="Close", 
                 command=settings_window.destroy).pack(pady=10)
    
    def start_monitoring(self):
        """Start monitoring WhatsApp window"""
        self.monitoring_thread = threading.Thread(target=self._monitor_whatsapp, daemon=True)
        self.monitoring_thread.start()
    
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
                            self.show_blur()
                    elif not current_hwnd and self.is_blurred:
                        # WhatsApp closed
                        self.hide_blur()
                        self.whatsapp_hwnd = None
                
                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)
    
    def quit_application(self):
        """Quit the application"""
        self.shutdown_event.set()
        self.hide_blur()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Unregister keyboard shortcut
        try:
            keyboard.unhook_all()
        except:
            pass
        
        sys.exit(0)

def main():
    """Main entry point"""
    if not sys.platform.startswith('win'):
        print("This application is designed for Windows only.")
        return
    
    # Check if WhatsApp is installed/running
    try:
        # Create root window (hidden)
        root = tk.Tk()
        root.withdraw()
        
        # Create and run the blur application
        app = WhatsAppBlur()
        
        # Show initial notification
        messagebox.showinfo("WhatsApp Blur", 
                           f"WhatsApp Blur is now running!\n\n"
                           f"• Press {app.toggle_key} to toggle blur\n"
                           f"• Check system tray for options\n"
                           f"• Hover over blurred content to reveal")
        
        # Keep the main thread alive
        try:
            while True:
                root.update()
                time.sleep(0.1)
        except KeyboardInterrupt:
            app.quit_application()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start WhatsApp Blur: {e}")

if __name__ == "__main__":
    main()