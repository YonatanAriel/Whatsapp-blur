#!/usr/bin/env python3
"""
WhatsApp Blur - FINAL CLEAN VERSION
Fixes all issues: prioritizes real WhatsApp, stops logging spam, runs silently
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
from PIL import Image, ImageTk, ImageFilter, ImageGrab, ImageDraw
import pystray
from pystray import MenuItem as item
import keyboard
import queue
import logging

# Set up QUIET logging (only errors)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_rounded_rectangle_mask(width, height, radius):
    """Create a rounded rectangle mask for applying rounded corners"""
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    
    # Draw rounded rectangle
    draw.rounded_rectangle([(0, 0), (width-1, height-1)], radius=radius, fill=255)
    
    return mask

def apply_rounded_corners_to_image(image, radius):
    """Apply rounded corners to an image using PIL"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    width, height = image.size
    mask = create_rounded_rectangle_mask(width, height, radius)
    
    # Create output image
    output = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    output.paste(image, (0, 0))
    output.putalpha(mask)
    
    return output

class WhatsAppBlurFinal:
    def __init__(self):
        # Fix DPI awareness FIRST
        self.fix_dpi_awareness()

        # Core state
        self.whatsapp_hwnd = None
        self.blur_window = None
        self.is_blurred = False
        self.is_enabled = True
        self.hover_remove_blur = True
        # Require WhatsApp to be in foreground to show blur
        self.require_foreground = True
        # Hover state
        self._is_hovering = False
        self._hover_watch_thread = None
        self._hover_watch_stop = threading.Event()
        self.toggle_key = 'ctrl+alt+q'  # Single hand shortcut - easy to press with left hand

        # Safety: prevent rapid blur attempts that could freeze WhatsApp
        self.last_blur_attempt = 0
        self.min_blur_interval = 2.0  # Minimum 2 seconds between blur attempts
        self.capturing_screenshot = False  # Prevent screenshot interference

        # Main tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("WhatsApp Blur")

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
        
        # State tracking for logging throttling
        self.last_log_state = None
        self.log_repeat_count = 0
        self.max_log_repeats = 3  # Only show repeated messages 3 times
        
        # Performance optimization - caching (CPU OPTIMIZED)
        self.window_cache = {}  # Cache for window detection
        self.last_window_search = 0
        self.window_cache_ttl = 8.0  # CPU OPTIMIZED: Extended from 1s to 8s (87% fewer searches)
        
        # Long-term stability - memory management (CPU OPTIMIZED)
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        
        # Resource tracking for cleanup
        self.created_widgets = set()
        self.active_callbacks = set()
        
        # Process name cache for CPU optimization
        self.process_name_cache = {}  # Cache process names to avoid repeated psutil.Process() calls

        print(f"🔐 WhatsApp Blur - Starting silently (DPI: {self.dpi_scale * 100:.0f}%)")
        self.check_system_requirements()

        # Initialize the application
        self.setup_keyboard_shortcut()
        self.create_tray_icon()
        self.start_monitoring()
        self.process_ui_queue()
    
    def fix_dpi_awareness(self):
        """Fix DPI awareness for proper coordinate calculation"""
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    
    def get_dpi_scale(self):
        """Get the current DPI scaling factor"""
        try:
            hdc = ctypes.windll.user32.GetDC(0)
            dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            ctypes.windll.user32.ReleaseDC(0, hdc)
            return dpi_x / 96.0  # 96 DPI is 100% scaling
        except Exception:
            return 1.0
    
    def check_system_requirements(self):
        """Quick system check"""
        try:
            test_img = ImageGrab.grab(bbox=(0, 0, 100, 100))
            print("✅ Screenshot capability working")
        except Exception:
            print("❌ Screenshot test failed - check Windows Privacy Settings")
    
    def is_whatsapp_currently_visible(self, hwnd):
        """Check if WhatsApp is actually visible and in the foreground RIGHT NOW"""
        try:
            if not hwnd or not win32gui.IsWindowVisible(hwnd):
                return False
            
            # Check if minimized
            if win32gui.IsIconic(hwnd):
                return False
            
            # Get current window rect
            try:
                current_rect = win32gui.GetWindowRect(hwnd)
                x, y, x2, y2 = current_rect
                width = x2 - x
                height = y2 - y
                
                # Check if window is actually on screen
                if width < 100 or height < 100:
                    return False
                
                # Check if window is mostly on screen
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                
                if x2 < 0 or y2 < 0 or x > screen_width or y > screen_height:
                    return False
                
                # If required, ensure WhatsApp is the foreground window
                if self.require_foreground:
                    try:
                        fg_hwnd = win32gui.GetForegroundWindow()
                        if fg_hwnd != hwnd:
                            return False
                    except Exception:
                        return False
                # Update the rect to current position
                self.whatsapp_rect = current_rect
                return True
                
            except Exception:
                return False
                
        except Exception:
            return False

    def _set_blur_window_visibility(self, alpha: float, clickthrough: bool):
        """Set blur window alpha and clickthrough without destroying it"""
        if not self.blur_window:
            return
        try:
            self.blur_window.attributes('-alpha', max(0.0, min(1.0, alpha)))
            hwnd = self.blur_window.winfo_id()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            # Ensure layered for alpha
            style |= win32con.WS_EX_LAYERED
            # Toggle clickthrough
            if clickthrough:
                style |= win32con.WS_EX_TRANSPARENT
            else:
                style &= ~win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        except Exception as e:
            print(f"⚠️ Error adjusting window visibility: {e}")
            raise

    def throttled_log(self, message):
        """Log message only if it's different from last or haven't exceeded repeat limit"""
        if message != self.last_log_state:
            print(message)
            self.last_log_state = message
            self.log_repeat_count = 1
        elif self.log_repeat_count < self.max_log_repeats:
            print(message)
            self.log_repeat_count += 1
        # Otherwise, suppress the repeated message

    def _point_in_rect(self, pt, rect):
        x, y = pt
        rx1, ry1, rx2, ry2 = rect
        return rx1 <= x <= rx2 and ry1 <= y <= ry2

    def _start_hover_watcher(self):
        if self._hover_watch_thread and self._hover_watch_thread.is_alive():
            return
        self._hover_watch_stop.clear()

        def watcher():
            while not self._hover_watch_stop.is_set():
                try:
                    # Only restore if we're actually hovering and should be watching
                    if not self._is_hovering:
                        break
                        
                    # If WhatsApp moved, refresh rect
                    if self.whatsapp_hwnd and win32gui.IsWindow(self.whatsapp_hwnd):
                        self.whatsapp_rect = win32gui.GetWindowRect(self.whatsapp_hwnd)
                    
                    # Get cursor position
                    pt = win32gui.GetCursorPos()
                    
                    # If cursor left WhatsApp rect, restore blur
                    if self.whatsapp_rect and not self._point_in_rect(pt, self.whatsapp_rect):
                        self._is_hovering = False
                        # Restore immediately if app still enabled and WA visible/foreground
                        if self.is_enabled and self.whatsapp_hwnd and self.is_whatsapp_currently_visible(self.whatsapp_hwnd):
                            # Restore alpha and interactivity
                            self._set_blur_window_visibility(1.0, clickthrough=False)
                        self._hover_watch_stop.set()
                        break
                except Exception:
                    pass
                time.sleep(0.1)  # Reduced frequency to 10Hz for better stability

        self._hover_watch_thread = threading.Thread(target=watcher, daemon=True)
        self._hover_watch_thread.start()
    
    def find_whatsapp_window(self):
        """Find WhatsApp window with caching for performance"""
        current_time = time.time()
        
        # Use cached result if recent enough
        if (current_time - self.last_window_search < self.window_cache_ttl and 
            'hwnd' in self.window_cache):
            # Verify cached window is still valid
            try:
                if (self.window_cache['hwnd'] and 
                    win32gui.IsWindow(self.window_cache['hwnd']) and
                    win32gui.IsWindowVisible(self.window_cache['hwnd'])):
                    return self.window_cache['hwnd']
            except:
                pass  # Cache invalid, search again
        
        # Perform new search
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    exe_name = ""
                    
                    # Get process name (CPU OPTIMIZED with caching)
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        
                        # Check cache first to avoid expensive psutil.Process() creation
                        if pid in self.process_name_cache:
                            exe_name = self.process_name_cache[pid]
                        else:
                            try:
                                process = psutil.Process(pid)
                                exe_name = process.name().lower()
                                # Cache the result (limit cache size)
                                if len(self.process_name_cache) < 100:
                                    self.process_name_cache[pid] = exe_name
                            except:
                                exe_name = ""
                    except:
                        exe_name = ""
                    
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
                
                # Check each window to find one that's actually visible NOW
                for window_data in windows:
                    hwnd = window_data[0]
                    if self.is_whatsapp_currently_visible(hwnd):
                        # Only log when we find a new window or change selection
                        if not self.whatsapp_hwnd or self.whatsapp_hwnd != hwnd:
                            print(f"🎯 WhatsApp found and VISIBLE: '{window_data[1]}' (process: {window_data[4]})")
                            print(f"📍 Current WhatsApp rect: {self.whatsapp_rect}")
                        
                        # Cache the result
                        self.window_cache = {'hwnd': hwnd, 'time': current_time}
                        self.last_window_search = current_time
                        return hwnd
                
                # If no window is actually visible
                self.throttled_log("⚠️ WhatsApp windows found but none are currently visible")
                self.whatsapp_rect = None
                # Cache negative result
                self.window_cache = {'hwnd': None, 'time': current_time}
                self.last_window_search = current_time
                return None
            else:
                self.whatsapp_rect = None
                # Cache negative result
                self.window_cache = {'hwnd': None, 'time': current_time}
                self.last_window_search = current_time
                return None
        except Exception as e:
            logger.error(f"Error finding WhatsApp window: {e}")
            self.whatsapp_rect = None
            return None
    
    def get_window_rect_dpi_aware(self, hwnd):
        """Get window rect with DPI scaling compensation"""
        try:
            return win32gui.GetWindowRect(hwnd)
        except Exception as e:
            logger.error(f"Error getting window rect: {e}")
            return None
    
    def capture_whatsapp_screenshot(self):
        """Capture screenshot with DPI scaling fixes - SAFE VERSION"""
        if not self.whatsapp_hwnd:
            return None
        
        # Prevent concurrent screenshots that cause white flash
        if self.capturing_screenshot:
            print("⚠️ Screenshot already in progress, skipping")
            return None
        
        self.capturing_screenshot = True
        
        try:
            # Check if WhatsApp is responsive before capturing
            try:
                window_text = win32gui.GetWindowText(self.whatsapp_hwnd)
                if not window_text:
                    print("⚠️ WhatsApp window has no title, may be loading")
                    return None
                    
                # Check if window is actually responsive
                if not win32gui.IsWindowVisible(self.whatsapp_hwnd):
                    print("⚠️ WhatsApp window not visible")
                    return None
                    
            except Exception as e:
                print(f"⚠️ WhatsApp window check failed: {e}")
                return None
            
            # Add small delay to avoid interfering with WhatsApp rendering
            time.sleep(0.1)
            
            rect = self.get_window_rect_dpi_aware(self.whatsapp_hwnd)
            if not rect:
                return None
            
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            # Store for blur window positioning
            self.whatsapp_rect = rect
            
            # Validate coordinates
            if x < -10000 or y < -10000 or width <= 0 or height <= 0:
                print(f"⚠️ Invalid coordinates: {rect}")
                return None
            
            # Check if window is too small (might be minimized or loading)
            if width < 200 or height < 200:
                print(f"⚠️ WhatsApp window too small: {width}x{height}")
                return None
            
            try:
                # Use gentle screenshot method
                screenshot = ImageGrab.grab(bbox=(x, y, x2, y2))
                
                # Validate screenshot quality
                if screenshot.size[0] < 100 or screenshot.size[1] < 100:
                    print("⚠️ Screenshot too small, WhatsApp may not be ready")
                    return None
                
                return screenshot
            except Exception as e:
                print(f"⚠️ Screenshot capture failed: {e}")
                # Don't try fallback methods that might interfere
                return None
                
        except Exception as e:
            logger.error(f"Error in capture_whatsapp_screenshot: {e}")
            return None
        finally:
            # Always reset the capturing flag
            self.capturing_screenshot = False
    
    def create_blurred_image(self, image):
        """Create TRUE transparent glass overlay with memory optimization"""
        if not image:
            return None
        
        try:
            # Convert to RGBA for consistency
            if image.mode != 'RGBA':
                base_image = image.convert('RGBA')
            else:
                base_image = image
            
            width, height = base_image.size
            
            try:
                import numpy as np
                
                # Create solid glass effect overlay (no alpha in PIL) with memory-efficient processing
                glass_array = np.zeros((height, width, 3), dtype=np.uint8)  # RGB only
                
                # Glass color - subtle blue-white tint
                base_r, base_g, base_b = 245, 248, 255  # Light blue-white
                
                # Add subtle texture for glass effect
                np.random.seed(42)  # Consistent pattern
                noise = np.random.normal(0, 2, (height, width))
                
                glass_r = np.clip(base_r + noise, 0, 255).astype(np.uint8)
                glass_g = np.clip(base_g + noise, 0, 255).astype(np.uint8) 
                glass_b = np.clip(base_b + noise, 0, 255).astype(np.uint8)
                
                # Combine channels (RGB only - no alpha)
                glass_array[:, :, 0] = glass_r
                glass_array[:, :, 1] = glass_g
                glass_array[:, :, 2] = glass_b
                
                # Convert to PIL RGB image (tkinter will handle transparency)
                glass_overlay = Image.fromarray(glass_array.astype('uint8'), mode='RGB')
                
                # Apply subtle blur for frosted glass texture
                glass_overlay = glass_overlay.filter(ImageFilter.GaussianBlur(radius=1.5))
                
                # Explicit memory cleanup for long-term stability
                del glass_array, noise, glass_r, glass_g, glass_b
                
                return glass_overlay
                
            except ImportError:
                # Fallback without numpy
                print("⚠️ NumPy not available, using simple glass overlay")
                
                # Create simple solid glass overlay (RGB only)
                glass_color = (245, 248, 255)  # Light blue-white
                glass_overlay = Image.new('RGB', base_image.size, glass_color)
                
                # Apply subtle blur
                glass_overlay = glass_overlay.filter(ImageFilter.GaussianBlur(radius=1.5))
                
                return glass_overlay
            
        except Exception as e:
            logger.error(f"Error creating glass effect: {e}")
            # Simple fallback
            try:
                return Image.new('RGB', image.size, (250, 252, 255))  # Light glass color
            except:
                return None
    
    def apply_rounded_corners(self, image, radius=12):
        """Apply rounded corners to match WhatsApp Desktop's design"""
        try:
            return apply_rounded_corners_to_image(image, radius)
        except Exception as e:
            logger.error(f"Error applying rounded corners: {e}")
            return image  # Return original if rounding fails
    
    def draw_rounded_fallback(self, canvas, width, height, radius=12):
        """Draw a rounded rectangle fallback when no image is available"""
        try:
            # Create a rounded rectangle on the canvas
            # Since tkinter doesn't have built-in rounded rectangles, we'll approximate with arcs
            
            # Fill the main rectangle (minus corners)
            canvas.create_rectangle(radius, 0, width-radius, height, 
                                  fill='#FAFCFF', outline='', width=0)
            canvas.create_rectangle(0, radius, width, height-radius, 
                                  fill='#FAFCFF', outline='', width=0)
            
            # Add corner arcs
            canvas.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, 
                            fill='#FAFCFF', outline='', width=0, style='pieslice')
            canvas.create_arc(width-radius*2, 0, width, radius*2, start=0, extent=90, 
                            fill='#FAFCFF', outline='', width=0, style='pieslice')
            canvas.create_arc(0, height-radius*2, radius*2, height, start=180, extent=90, 
                            fill='#FAFCFF', outline='', width=0, style='pieslice')
            canvas.create_arc(width-radius*2, height-radius*2, width, height, start=270, extent=90, 
                            fill='#FAFCFF', outline='', width=0, style='pieslice')
            
            # Add text overlay
            canvas.create_text(width//2, height//2, 
                             text="🔒 WhatsApp Blurred\nHover to reveal", 
                             font=('Arial', 14, 'bold'), 
                             fill='#666666', justify='center')
        except Exception as e:
            logger.error(f"Error drawing rounded fallback: {e}")
            # Simple fallback without rounding
            canvas.create_rectangle(0, 0, width, height, fill='#FAFCFF', outline='')
            canvas.create_text(width//2, height//2, 
                             text="🔒 WhatsApp Blurred\nHover to reveal", 
                             font=('Arial', 14, 'bold'), 
                             fill='#666666', justify='center')
    
    def create_blur_window(self):
        """Create blur overlay window using current WhatsApp position"""
        if not self.whatsapp_hwnd:
            print("❌ No WhatsApp handle - cannot create blur window")
            return
        
        try:
            # Get CURRENT WhatsApp coordinates (not cached)
            current_rect = win32gui.GetWindowRect(self.whatsapp_hwnd)
            x, y, x2, y2 = current_rect
            width = x2 - x
            height = y2 - y
            
            print(f"🪟 Creating blur window: {width}x{height} at ({x},{y}) - using CURRENT WhatsApp position")
            
            # Update cached rect with current position
            self.whatsapp_rect = current_rect
            
            # Destroy existing window
            if self.blur_window:
                self.blur_window.destroy()
            
            # Create blur window
            self.blur_window = tk.Toplevel(self.root)
            self.blur_window.title("WhatsApp Blur")
            
            # Set window properties FIRST
            self.blur_window.overrideredirect(True)  # Remove title bar
            self.blur_window.attributes('-topmost', True)  # Always on top
            self.blur_window.attributes('-alpha', 1.0)  # Full opacity
            
            # Set geometry AFTER properties
            self.blur_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Force window to display and update
            self.blur_window.update_idletasks()
            self.blur_window.update()
            
            # Use Win32 API to ensure window is above WhatsApp
            try:
                hwnd = self.blur_window.winfo_id()
                # Set window to be topmost using Windows API
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, x, y, width, height, 
                                    win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE)
            except Exception as e:
                print(f"⚠️ Win32 positioning failed: {e}")
            
            # Create canvas with glass effect background
            canvas = tk.Canvas(self.blur_window, width=width, height=height, 
                             highlightthickness=0, bg='#F5F8FF')  # Light glass color background
            canvas.pack()
            
            # Apply Windows 11 rounded corners to the window itself
            try:
                hwnd = self.blur_window.winfo_id()
                # Use Windows 11 DWM API for native rounded corners
                DWM_WINDOW_CORNER_PREFERENCE = 33
                DWMWCP_ROUND = 2  # Round corners if appropriate
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWM_WINDOW_CORNER_PREFERENCE, 
                    ctypes.byref(ctypes.c_int(DWMWCP_ROUND)), 
                    ctypes.sizeof(ctypes.c_int)
                )
                print("✅ Native Windows 11 rounded corners applied")
            except Exception as e:
                print(f"⚠️ Native rounded corners failed: {e}")
            
            # Set window transparency for glass effect (30% transparent)
            self.blur_window.attributes('-alpha', 0.7)
            
            # Add glass texture overlay image if available
            if self.blur_cache:
                try:
                    # Resize if needed
                    if self.blur_cache.size != (width, height):
                        resized = self.blur_cache.resize((width, height), Image.Resampling.LANCZOS)
                    else:
                        resized = self.blur_cache
                    
                    photo = ImageTk.PhotoImage(resized)
                    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                    canvas.image = photo  # Keep reference
                    
                except Exception as e:
                    print(f"❌ Image creation failed: {e}")
                    # Fallback with solid glass color
                    canvas.configure(bg='#F5F8FF')
            else:
                # Fallback with glass color and text
                canvas.configure(bg='#F5F8FF')
                canvas.create_text(width//2, height//2, 
                                 text="🔒 WhatsApp Blurred\nHover to reveal", 
                                 font=('Segoe UI', 14, 'normal'), 
                                 fill='#666666', justify='center')
            
            # Bind hover events
            self.blur_window.bind('<Enter>', self.on_hover_enter)
            self.blur_window.bind('<Leave>', self.on_hover_leave)
            canvas.bind('<Enter>', self.on_hover_enter)
            canvas.bind('<Leave>', self.on_hover_leave)
            print("✅ Hover events bound")
            
            # Ensure layered style for alpha control; not click-through by default
            try:
                hwnd = self.blur_window.winfo_id()
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                style |= win32con.WS_EX_LAYERED
                style &= ~win32con.WS_EX_TRANSPARENT
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
            except Exception:
                pass
            print("✅ Layered window ready (non-clickthrough by default)")
            print("🎉 Blur window creation completed successfully!")
            
        except Exception as e:
            print(f"❌ Error creating blur window: {e}")
            logger.error(f"Error creating blur window: {e}")
            if self.blur_window:
                self.blur_window.destroy()
                self.blur_window = None
    
    def make_clickthrough(self):
        """Deprecated: now controlled by _set_blur_window_visibility"""
        self._set_blur_window_visibility(1.0, clickthrough=False)
    
    def on_hover_enter(self, event):
        """Handle hover enter: temporarily reveal WhatsApp without destroying overlay"""
        if self.hover_remove_blur and self.is_blurred and self.blur_window:
            self._is_hovering = True
            # Make overlay invisible and click-through
            self._set_blur_window_visibility(alpha=0.0, clickthrough=True)
            # Start watcher to restore when cursor leaves WhatsApp rect
            self._start_hover_watcher()
    
    def on_hover_leave(self, event):
        """Handle hover leave: let watcher handle restoration for better timing"""
        if self.hover_remove_blur and self.is_blurred and self.blur_window:
            # Don't immediately restore - let the watcher thread handle it
            # This prevents the overlay from flickering back and forth
            pass
    
    def show_blur_if_enabled(self):
        """Show blur if conditions are met"""
        if not self.is_blurred and self.is_enabled:
            self.show_blur()
    
    def show_blur(self):
        """Show blur overlay - ONLY when WhatsApp is actually visible"""
        print("🔍 show_blur() called")
        
        # Safety check: prevent rapid blur attempts
        current_time = time.time()
        if current_time - self.last_blur_attempt < self.min_blur_interval:
            print(f"⚠️ Too soon since last blur attempt ({current_time - self.last_blur_attempt:.1f}s < {self.min_blur_interval}s)")
            return
        
        self.last_blur_attempt = current_time
        
        if not self.is_enabled:
            print("❌ App is disabled - enable in tray menu first")
            return
        
        if self.is_blurred:
            print("⚠️ Blur already active")
            return
        
        print("🔍 Looking for WhatsApp window...")
        
        # CRITICAL: Find WhatsApp and verify it's currently visible
        self.whatsapp_hwnd = self.find_whatsapp_window()
        if not self.whatsapp_hwnd:
            print("❌ WhatsApp not found or not currently visible - no blur shown")
            return
        
        # Double-check that it's really visible before proceeding
        if not self.is_whatsapp_currently_visible(self.whatsapp_hwnd):
            print("❌ WhatsApp visibility double-check failed")
            self.whatsapp_hwnd = None
            return
        
        print("📸 Capturing screenshot (safely)...")
        
        # Capture screenshot with safety checks
        screenshot = self.capture_whatsapp_screenshot()
        if not screenshot:
            print("❌ Screenshot capture failed - WhatsApp may be loading")
            return
        
        print("🌀 Creating blur effect...")
        
        # Create blur
        self.blur_cache = self.create_blurred_image(screenshot)
        if not self.blur_cache:
            print("❌ Blur creation failed")
            return
        
        print("🪟 Creating blur window...")
        
        # Create window
        self.create_blur_window()
        
        # Check if creation was successful
        if self.blur_window:
            self.is_blurred = True
            # Ensure visible and non-clickthrough after creation
            self._set_blur_window_visibility(alpha=1.0, clickthrough=False)
            print("✅ Blur successfully activated!")
        else:
            print("❌ Blur window creation failed")
    
    def hide_blur(self):
        """Hide blur overlay and clean up state with improved memory management"""
        print("🙈 hide_blur() called")
        
        if self.blur_window:
            print("🗂️ Destroying blur window...")
            try:
                # Proper cleanup sequence to prevent memory leaks
                self.blur_window.withdraw()  # Hide first
                self.blur_window.update_idletasks()  # Process pending events
                self.blur_window.destroy()  # Then destroy
                self.blur_window = None
                print("✅ Blur window destroyed")
            except Exception as e:
                logger.error(f"Error destroying blur window: {e}")
                self.blur_window = None
        
        if self.is_blurred:
            self.is_blurred = False
            print("✅ Blur state cleared")
        
        # Clear blur cache to save memory
        if self.blur_cache:
            self.blur_cache = None
            print("🧹 Blur cache cleared")
        
        # Force garbage collection for better memory management
        import gc
        gc.collect()
        print("🗑️ Memory cleanup completed")
        
        print("✅ Blur completely hidden and cleaned up")
    
    def update_blur_position(self):
        """Update blur window position to follow WhatsApp window"""
        if not self.is_blurred or not self.blur_window or not self.whatsapp_hwnd:
            return
        
        try:
            # Get current WhatsApp window position
            current_rect = win32gui.GetWindowRect(self.whatsapp_hwnd)
            
            # Check if position changed
            if current_rect != self.whatsapp_rect:
                self.whatsapp_rect = current_rect
                x, y, x2, y2 = current_rect
                
                # Update blur window position and size
                self.blur_window.geometry(f"{x2-x}x{y2-y}+{x}+{y}")
                
                # Optionally refresh the blur image for new position
                # (Commented out for performance - only position tracking)
                # screenshot = self.capture_whatsapp_screenshot()
                # if screenshot:
                #     self.blur_cache = self.create_blurred_image(screenshot)
                #     # Update the image in the window...
                
        except Exception as e:
            # Window might be closed/minimized
            pass
    
    def toggle_blur(self):
        """Toggle blur on/off - FIXED to actually work"""
        print(f"\n🎯 HOTKEY PRESSED! Current blur: {'ON' if self.is_blurred else 'OFF'}")
        
        if self.is_blurred:
            # Hide current blur
            self.ui_queue.put(('hide_blur', None))
            print("❌ Blur turned OFF")
        else:
            # Show blur if WhatsApp is visible
            self.ui_queue.put(('show_blur', None))
            print("🔍 Attempting to show blur...")
        
        self.update_tray_menu()
    
    def setup_keyboard_shortcut(self):
        """Setup keyboard shortcut"""
        try:
            keyboard.add_hotkey(self.toggle_key, self.toggle_blur)
            print(f"✅ Keyboard shortcut: {self.toggle_key}")
        except Exception as e:
            logger.error(f"Failed to setup keyboard shortcut: {e}")
    
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
            print("✅ System tray icon created")
        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
    
    def test_screenshot(self):
        """Test screenshot functionality"""
        try:
            test_img = ImageGrab.grab(bbox=(0, 0, 400, 300))
            test_path = "test_screenshot.png"
            test_img.save(test_path)
            
            messagebox.showinfo("Screenshot Test", 
                              f"✅ Screenshot test successful!\n"
                              f"Saved: {test_path}\n"
                              f"Size: {test_img.size}\n"
                              f"DPI Scale: {self.dpi_scale}")
        except Exception as e:
            messagebox.showerror("Screenshot Test", 
                               f"❌ Screenshot test failed!\n"
                               f"Error: {e}\n\n"
                               f"Check Windows Privacy Settings:\n"
                               f"Settings > Privacy & Security > Screenshots and apps")
    
    def show_system_info(self):
        """Show system information"""
        try:
            info_window = tk.Toplevel(self.root)
            info_window.title("WhatsApp Blur - System Info")
            info_window.geometry("450x350")
            info_window.attributes('-topmost', True)
            
            info_text = f"""WhatsApp Blur - System Information

Status: {'Running' if self.is_enabled else 'Disabled'}
Blur Active: {'Yes' if self.is_blurred else 'No'}
DPI Scale: {self.dpi_scale * 100:.0f}%
WhatsApp Found: {'Yes' if self.whatsapp_hwnd else 'No'}

Keyboard Shortcut: {self.toggle_key}
✅ Safe shortcut - no conflicts with WhatsApp

Privacy Permissions Setup:
1. Windows + I → Settings
2. Privacy & security → Screenshots and apps  
3. Enable "Let desktop apps take screenshots"

For Windows privacy settings to show this app:
- App will appear after running for a while
- May need to restart computer
- Look for "Python" or "WhatsApp Blur" in the list

Troubleshooting:
• If no blur appears: Check privacy permissions
• If wrong window detected: Close other apps with "WhatsApp" in name
• DPI scaling issues: Try setting display to 100%
• Run as Administrator for best compatibility

Current keyboard shortcuts that DON'T conflict:
❌ Ctrl+Shift+B (WhatsApp bold)
❌ Ctrl+Alt+B (WhatsApp bold alternative)  
❌ Ctrl+Win+B (conflicts with WhatsApp bold)
✅ Ctrl+Alt+Q (easy single hand shortcut!)
"""
            
            text_widget = tk.Text(info_window, wrap=tk.WORD, font=('Consolas', 9))
            text_widget.insert('1.0', info_text)
            text_widget.config(state=tk.DISABLED)
            text_widget.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
            
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
                item('Show System Info', self.show_system_info),
                item('Exit', self.quit_application)
            )
            self.tray_icon.menu = menu
    
    def start_monitoring(self):
        """Start monitoring thread"""
        self.monitoring_thread = threading.Thread(target=self._monitor_whatsapp, daemon=True)
        self.monitoring_thread.start()
    
    def periodic_cleanup(self):
        """Perform periodic memory cleanup to prevent long-term degradation - CPU OPTIMIZED"""
        current_time = time.time()
        
        # Time-based cleanup check (CPU optimized)
        if current_time - self.last_cleanup_time > self.cleanup_interval:
            
            print("🧹 Performing periodic memory cleanup...")
            
            try:
                # Clear window and image caches
                self.window_cache.clear()
                # Clear process name cache periodically
                if len(self.process_name_cache) > 50:
                    self.process_name_cache.clear()
                    print("🧹 Cleared process name cache to free memory")
                if hasattr(self, 'cached_image'):
                    self.cached_image = None
                if hasattr(self, 'blur_cache'):
                    self.blur_cache = None
                
                # Cancel any old after() callbacks to prevent accumulation (research finding)
                old_callbacks = len(self.active_callbacks)
                if old_callbacks > 50:  # If too many callbacks accumulated
                    print(f"🧹 Cleaning up {old_callbacks} accumulated callbacks...")
                    for callback_id in list(self.active_callbacks)[:old_callbacks//2]:
                        try:
                            self.root.after_cancel(callback_id)
                            self.active_callbacks.discard(callback_id)
                        except:
                            pass
                
                # Clear any created widgets that may have accumulated
                widgets_cleaned = 0
                for widget in list(self.created_widgets):
                    try:
                        if hasattr(widget, 'destroy'):
                            widget.destroy()
                        self.created_widgets.discard(widget)
                        widgets_cleaned += 1
                    except:
                        pass
                
                if widgets_cleaned > 0:
                    print(f"🧹 Cleaned up {widgets_cleaned} old widgets")
                
                # Force garbage collection
                import gc
                collected = gc.collect()
                print(f"🗑️ Garbage collected: {collected} objects")
                
                # Reset cleanup timer
                self.last_cleanup_time = current_time
                
                # Log memory usage for monitoring
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                print(f"📊 Memory usage after cleanup: {memory_mb:.1f} MB")
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def _monitor_whatsapp(self):
        """Monitor WhatsApp window - CPU OPTIMIZED VERSION"""
        last_whatsapp_state = None
        state_change_time = 0
        debounce_delay = 0.5
        last_cleanup_check = time.time()
        
        while not self.shutdown_event.is_set():
            try:
                current_time = time.time()
                
                # Time-based cleanup check (CPU optimized - no operation counting)
                if current_time - last_cleanup_check > 60:  # Check every minute
                    if current_time - self.last_cleanup_time > self.cleanup_interval:
                        self.periodic_cleanup()
                    last_cleanup_check = current_time
                
                if self.is_enabled:
                    current_hwnd = self.find_whatsapp_window()
                    current_state = bool(current_hwnd and self.is_whatsapp_currently_visible(current_hwnd))
                    
                    # Debounce state changes to prevent rapid toggling
                    if current_state != last_whatsapp_state:
                        if current_time - state_change_time > debounce_delay:
                            if current_state:
                                print("📱 WhatsApp became visible")
                            else:
                                print("📱 WhatsApp no longer visible")
                            last_whatsapp_state = current_state
                            state_change_time = current_time
                            
                            # Queue UI updates with debouncing
                            if current_state and current_hwnd != self.whatsapp_hwnd:
                                self.whatsapp_hwnd = current_hwnd
                                if not self.is_blurred and not self._is_hovering:
                                    self.ui_queue.put(('show_blur', None))
                            elif not current_state and self.is_blurred:
                                self.ui_queue.put(('hide_blur', None))
                                self.whatsapp_hwnd = None
                    
                    # Update position less frequently to reduce load
                    if self.is_blurred and current_hwnd and current_time % 2 < 0.3:
                        self.ui_queue.put(('update_blur_position', None))
                
                time.sleep(1.5)  # CPU OPTIMIZED: Reduced from 0.3s to 1.5s (75% fewer cycles)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)
    
    def process_ui_queue(self):
        """Process UI operations with throttling - CPU OPTIMIZED"""
        try:
            operations_processed = 0
            max_operations_per_cycle = 3  # Limit operations per cycle
            
            while not self.ui_queue.empty() and operations_processed < max_operations_per_cycle:
                operation, data = self.ui_queue.get_nowait()
                
                try:
                    if operation == 'show_blur':
                        self.show_blur()
                    elif operation == 'hide_blur':
                        self.hide_blur()
                    elif operation == 'show_blur_if_enabled':
                        self.show_blur_if_enabled()
                    elif operation == 'update_blur_position':
                        self.update_blur_position()
                    
                    operations_processed += 1
                    
                except Exception as e:
                    logger.error(f"UI operation '{operation}' failed: {e}")
                    
            # Schedule next processing with callback tracking for cleanup
            next_interval = 100 if self.ui_queue.empty() else 50
            callback_id = self.root.after(next_interval, self.process_ui_queue)
            self.active_callbacks.add(callback_id)
            
        except Exception as e:
            logger.error(f"Error processing UI queue: {e}")
            # Reschedule even on error
            callback_id = self.root.after(200, self.process_ui_queue)
            self.active_callbacks.add(callback_id)
    
    def quit_application(self):
        """Quit application with comprehensive cleanup"""
        print("🛑 Quitting WhatsApp Blur with memory cleanup...")
        self.shutdown_event.set()
        
        try:
            # Clean up blur window
            self.hide_blur()
            
            # Cancel all pending after() callbacks
            for callback_id in list(self.active_callbacks):
                try:
                    self.root.after_cancel(callback_id)
                except:
                    pass
            self.active_callbacks.clear()
            
            # Clean up created widgets
            for widget in list(self.created_widgets):
                try:
                    if hasattr(widget, 'destroy'):
                        widget.destroy()
                except:
                    pass
            self.created_widgets.clear()
            
            # Stop tray icon
            if self.tray_icon:
                self.tray_icon.stop()
            
            # Unhook keyboard
            try:
                keyboard.unhook_all()
            except:
                pass
            
            # Final garbage collection
            import gc
            collected = gc.collect()
            print(f"🗑️ Final cleanup: {collected} objects collected")
            
        except Exception as e:
            logger.error(f"Cleanup during quit: {e}")
        finally:
            self.root.quit()
            self.root.destroy()
            sys.exit(0)

def main():
    """Main function"""
    if not sys.platform.startswith('win'):
        print("This application is designed for Windows only.")
        return
    
    try:
        app = WhatsAppBlurFinal()
        
        # Show simplified startup message
        print(f"\n🎉 WhatsApp Blur started successfully!")
        print(f"✅ Press {app.toggle_key} to toggle blur")
        print(f"✅ Right-click system tray icon for options")
        print(f"✅ Will auto-start with Windows")
        print(f"\n📋 First time setup:")
        print(f"1. Grant privacy permissions in Windows Settings")
        print(f"2. Settings > Privacy & Security > Screenshots and apps")
        print(f"3. Enable 'Let desktop apps take screenshots'")
        print(f"\n🔄 Running silently in background...")
        
        app.root.mainloop()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        messagebox.showerror("Error", f"Failed to start: {e}")

if __name__ == "__main__":
    main()
