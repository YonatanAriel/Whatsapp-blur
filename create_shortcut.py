#!/usr/bin/env python3
"""
Create desktop shortcut with icon for WhatsApp Blur
"""

import os
import sys
from PIL import Image, ImageDraw

def create_icon():
    """Create a simple blur effect icon"""
    try:
        # Create a 32x32 icon with blur effect appearance
        size = 32
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Create gradient blur effect
        center = size // 2
        for radius in range(center, 0, -2):
            alpha = int(255 * (1 - radius / center) * 0.8)
            color = (100, 150, 255, alpha)  # Blue glass color
            draw.ellipse([center-radius, center-radius, center+radius, center+radius], 
                        fill=color, outline=None)
        
        # Add small highlight
        draw.ellipse([8, 8, 12, 12], fill=(255, 255, 255, 180))
        
        # Save as icon
        icon_path = "whatsapp_blur.ico"
        img.save(icon_path, "ICO")
        print(f"[OK] Icon created: {icon_path}")
        return icon_path
    except Exception as e:
        print(f"[WARN] Could not create icon: {e}")
        return None

def create_shortcut():
    """Create desktop shortcut for WhatsApp Blur"""
    try:
        import win32com.client
        
        # Create icon first
        icon_path = create_icon()
        
        # Desktop path
        desktop_paths = [
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
            "C:\\Users\\Public\\Desktop"
        ]
        
        desktop_path = None
        for path in desktop_paths:
            if os.path.exists(path):
                desktop_path = path
                break
        
        if not desktop_path:
            print("[WARN] Could not find Desktop folder")
            return False
        
        # Create shortcut
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut_path = os.path.join(desktop_path, "WhatsApp Blur.lnk")
        shortcut = shell.CreateShortCut(shortcut_path)
        
        # Set target (python executable + script)
        python_exe = sys.executable
        script_path = "C:\\Users\\Public\\WhatsApp Blur\\whatsapp_blur.py"
        
        shortcut.Targetpath = python_exe
        shortcut.Arguments = f'"{script_path}"'
        shortcut.WorkingDirectory = "C:\\Users\\Public\\WhatsApp Blur"
        shortcut.Description = "WhatsApp Blur - Privacy overlay for WhatsApp"
        
        # Set icon if created
        if icon_path and os.path.exists(icon_path):
            shortcut.IconLocation = os.path.abspath(icon_path)
        
        # Save shortcut
        shortcut.save()
        print(f"[OK] Desktop shortcut created: {shortcut_path}")
        return True
        
    except ImportError:
        print("[WARN] win32com not available - creating .bat file instead")
        return create_bat_shortcut(desktop_path)
    except Exception as e:
        print(f"[WARN] Shortcut creation failed: {e}")
        return False

def create_bat_shortcut(desktop_path):
    """Fallback: create .bat shortcut"""
    try:
        bat_content = f'''@echo off
cd /d "C:\\Users\\Public\\WhatsApp Blur"
python whatsapp_blur.py
pause'''
        
        bat_path = os.path.join(desktop_path, "WhatsApp Blur.bat")
        with open(bat_path, 'w') as f:
            f.write(bat_content)
        
        print(f"[OK] Batch shortcut created: {bat_path}")
        return True
    except Exception as e:
        print(f"[WARN] Batch shortcut creation failed: {e}")
        return False

if __name__ == "__main__":
    create_shortcut()
