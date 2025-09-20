#!/usr/bin/env python3
"""
WhatsApp Blur - Professional Installer
Creates proper Windows installation with icon, auto-start, and privacy permissions
"""

import os
import sys
import shutil
import subprocess
import winreg
import ctypes
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import requests
from PIL import Image, ImageDraw

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Re-run the script as administrator"""
    if is_admin():
        return True
    else:
        try:
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False
        except:
            messagebox.showerror("Error", "Administrator rights are required for proper installation.")
            return False

def create_app_icon():
    """Create a professional icon for the app"""
    try:
        # Create a 256x256 icon
        size = 256
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Create a shield-like design
        # Outer circle (blue)
        circle_margin = 20
        draw.ellipse([circle_margin, circle_margin, size-circle_margin, size-circle_margin], 
                    fill=(25, 118, 210, 255), outline=(13, 71, 161, 255), width=4)
        
        # Inner shield shape
        shield_margin = 50
        shield_points = [
            (size//2, shield_margin),  # Top
            (size-shield_margin, shield_margin + 40),  # Top right
            (size-shield_margin, size-shield_margin-20),  # Bottom right
            (size//2, size-shield_margin+20),  # Bottom point
            (shield_margin, size-shield_margin-20),  # Bottom left
            (shield_margin, shield_margin + 40),  # Top left
        ]
        draw.polygon(shield_points, fill=(255, 255, 255, 255), outline=(200, 200, 200, 255), width=2)
        
        # Eye symbol (privacy)
        eye_center_x, eye_center_y = size//2, size//2 + 10
        eye_width, eye_height = 80, 40
        
        # Eye outline
        draw.ellipse([eye_center_x - eye_width//2, eye_center_y - eye_height//2,
                     eye_center_x + eye_width//2, eye_center_y + eye_height//2],
                    fill=(100, 100, 100, 255), outline=(50, 50, 50, 255), width=2)
        
        # Eye pupil
        pupil_size = 20
        draw.ellipse([eye_center_x - pupil_size//2, eye_center_y - pupil_size//2,
                     eye_center_x + pupil_size//2, eye_center_y + pupil_size//2],
                    fill=(255, 255, 255, 255))
        
        # Slash (blur effect)
        slash_width = 6
        draw.line([eye_center_x - 50, eye_center_y - 30, eye_center_x + 50, eye_center_y + 30],
                 fill=(220, 53, 69, 255), width=slash_width)
        
        # Add text
        try:
            from PIL import ImageFont
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = None
        
        text = "WB"
        if font:
            # Get text size
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (size - text_width) // 2
            text_y = size - 60
            draw.text((text_x, text_y), text, fill=(25, 118, 210, 255), font=font)
        
        return image
    except Exception as e:
        print(f"Error creating icon: {e}")
        # Create simple fallback icon
        image = Image.new('RGB', (256, 256), (25, 118, 210))
        draw = ImageDraw.Draw(image)
        draw.text((100, 120), "WB", fill=(255, 255, 255))
        return image

def install_application():
    """Install the application properly"""
    try:
        print("🚀 Installing WhatsApp Blur...")
        
        # Create installation directory
        install_dir = Path(os.environ['PROGRAMFILES']) / "WhatsApp Blur"
        install_dir.mkdir(exist_ok=True, parents=True)
        
        print(f"📁 Installation directory: {install_dir}")
        
        # Create icon
        print("🎨 Creating application icon...")
        icon_image = create_app_icon()
        icon_path = install_dir / "whatsapp_blur.ico"
        
        # Save as ICO format
        icon_image.save(str(icon_path), format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print(f"✅ Icon created: {icon_path}")
        
    # Copy main application (use the current final version)
    source_file = Path(__file__).parent / "whatsapp_blur_final.py"
        target_file = install_dir / "whatsapp_blur.py"
        
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            print(f"✅ Application copied: {target_file}")
        else:
            print(f"❌ Source file not found: {source_file}")
            return False
        
        # Copy requirements
        req_source = Path(__file__).parent / "requirements.txt"
        req_target = install_dir / "requirements.txt"
        if req_source.exists():
            shutil.copy2(req_source, req_target)
            print(f"✅ Requirements copied: {req_target}")
        
        # Install Python dependencies
        print("📦 Installing Python dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_target)], 
                         check=True, capture_output=True, text=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Dependency installation failed: {e}")
            print("You may need to install dependencies manually")
        
        # Create launcher script
        launcher_content = f'''@echo off
cd /d "{install_dir}"
python whatsapp_blur.py
'''
        launcher_path = install_dir / "WhatsApp Blur.bat"
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        print(f"✅ Launcher created: {launcher_path}")
        
        # Create Start Menu shortcut
        create_start_menu_shortcut(install_dir, icon_path, launcher_path)
        
        # Add to Windows Registry for proper recognition
        register_application(install_dir, icon_path, launcher_path)
        
        # Setup auto-start
        setup_windows_autostart(launcher_path)
        
        print("\n🎉 Installation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def create_start_menu_shortcut(install_dir, icon_path, launcher_path):
    """Create Start Menu shortcut"""
    try:
        import win32com.client
        
        start_menu = Path(os.environ['PROGRAMDATA']) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        shortcut_path = start_menu / "WhatsApp Blur.lnk"
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = str(launcher_path)
        shortcut.WorkingDirectory = str(install_dir)
        shortcut.IconLocation = str(icon_path)
        shortcut.Description = "WhatsApp Privacy Blur Tool"
        shortcut.save()
        
        print(f"✅ Start Menu shortcut created: {shortcut_path}")
        
    except Exception as e:
        print(f"⚠️ Could not create Start Menu shortcut: {e}")

def register_application(install_dir, icon_path, launcher_path):
    """Register application in Windows Registry"""
    try:
        app_name = "WhatsApp Blur"
        app_key = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{app_name}.exe"
        
        # Register in HKEY_LOCAL_MACHINE
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, app_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(launcher_path))
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, str(install_dir))
        
        # Register for uninstall
        uninstall_key = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "WhatsApp Blur")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "WhatsApp Blur Team")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(icon_path))
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            
        print("✅ Application registered in Windows Registry")
        
    except Exception as e:
        print(f"⚠️ Registry registration failed: {e}")

def setup_windows_autostart(launcher_path):
    """Setup Windows auto-start"""
    try:
        # Method 1: Startup folder
        startup_folder = Path(os.environ['APPDATA']) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        startup_shortcut = startup_folder / "WhatsApp Blur.lnk"
        
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(startup_shortcut))
        shortcut.Targetpath = str(launcher_path)
        shortcut.Description = "WhatsApp Privacy Blur Tool - Auto Start"
        shortcut.save()
        
        print(f"✅ Auto-start shortcut created: {startup_shortcut}")
        
        # Method 2: Registry Run key
        run_key = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, run_key) as key:
            winreg.SetValueEx(key, "WhatsApp Blur", 0, winreg.REG_SZ, f'"{launcher_path}"')
        
        print("✅ Auto-start registry entry created")
        
    except Exception as e:
        print(f"⚠️ Auto-start setup failed: {e}")

def setup_privacy_permissions():
    """Guide user through privacy permission setup"""
    permission_guide = """
🔐 PRIVACY PERMISSIONS SETUP

After installation, you need to grant privacy permissions:

1. Press Windows + I (Settings)
2. Go to "Privacy & security" 
3. Click "Camera" → Enable "Let desktop apps access your camera"
4. Click "Microphone" → Enable "Let desktop apps access your microphone"  
5. Look for "Screenshots and apps" or "Screen recording"
6. Enable "Let desktop apps take screenshots and record screen"

📍 IMPORTANT: Look for "WhatsApp Blur" in the apps list and enable it!

🔄 If you don't see the app in Privacy settings:
   - Restart your computer after installation
   - The app will appear after first launch

✅ Once permissions are set, the app will work automatically!
"""
    
    messagebox.showinfo("Privacy Permissions Required", permission_guide)

def main():
    """Main installer function"""
    print("🔧 WhatsApp Blur Professional Installer")
    print("=" * 50)
    
    # Check admin rights
    if not is_admin():
        print("❌ Administrator rights required for installation")
        if not run_as_admin():
            return
        sys.exit(0)
    
    print("✅ Running with administrator rights")
    
    # Perform installation
    if install_application():
        # Show privacy permission guide
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        setup_privacy_permissions()
        
    success_message = """
🎉 WhatsApp Blur installed successfully!

✅ Auto-start enabled - no need to manually open
✅ Start Menu shortcut created  
✅ System tray integration ready
✅ Keyboard shortcut: Ctrl+Alt+Q (avoids WhatsApp conflicts)

🔄 RESTART YOUR COMPUTER to complete installation

After restart:
1. Grant privacy permissions (as shown)  
2. Use Ctrl+Alt+Q to toggle blur
3. The app runs automatically in background

📱 The app will appear in Windows Privacy Settings after first launch!
"""
        messagebox.showinfo("Installation Complete", success_message)
        
        # Ask to restart now
        restart = messagebox.askyesno("Restart Required", 
                                    "Restart computer now to complete installation?\n\n"
                                    "Click 'Yes' to restart immediately\n"
                                    "Click 'No' to restart later manually")
        
        if restart:
            subprocess.run(["shutdown", "/r", "/t", "10"], shell=True)
            messagebox.showinfo("Restarting", "Computer will restart in 10 seconds...")
    
    else:
        messagebox.showerror("Installation Failed", 
                           "Installation failed. Please check the console for errors.")

if __name__ == "__main__":
    main()
