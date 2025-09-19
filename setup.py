#!/usr/bin/env python3
"""
Setup script for WhatsApp Blur application
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def create_shortcut():
    """Create desktop shortcut"""
    try:
        import win32com.client
        
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        path = os.path.join(desktop, 'WhatsApp Blur.lnk')
        target = os.path.abspath('whatsapp_blur.py')
        wDir = os.path.dirname(target)
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = sys.executable
        shortcut.save()
        
        print(f"✓ Desktop shortcut created: {path}")
        return True
    except Exception as e:
        print(f"⚠ Could not create desktop shortcut: {e}")
        return False

def main():
    print("WhatsApp Blur Setup")
    print("=" * 30)
    
    # Check if running on Windows
    if not sys.platform.startswith('win'):
        print("✗ This application requires Windows")
        return
    
    # Install dependencies
    print("Installing dependencies...")
    if not install_requirements():
        return
    
    # Create shortcut
    print("Creating desktop shortcut...")
    create_shortcut()
    
    print("\n✓ Setup completed!")
    print("\nUsage:")
    print("• Run 'python whatsapp_blur.py' or use the desktop shortcut")
    print("• Use Ctrl+Shift+B to toggle blur")
    print("• Check system tray for options")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()