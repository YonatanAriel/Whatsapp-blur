#!/usr/bin/env python3
"""
Auto-start setup script for WhatsApp Blur
"""

import os
import sys
import shutil
from tkinter import messagebox
import tkinter as tk

def setup_auto_start():
    """Setup auto-start functionality"""
    try:
        # Get startup folder path
        startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        
        # Get current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fixed_script = os.path.join(script_dir, 'whatsapp_blur_fixed.py')
        
        # Check if fixed script exists
        if not os.path.exists(fixed_script):
            raise FileNotFoundError("whatsapp_blur_fixed.py not found")
        
        # Create batch file content
        batch_file = os.path.join(startup_folder, 'WhatsApp_Blur_AutoStart.bat')
        
        batch_content = f'''@echo off
title WhatsApp Blur - Auto Start
cd /d "{script_dir}"
python "{fixed_script}"
'''
        
        # Write batch file
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        return True, f"Auto-start enabled! File created: {batch_file}"
        
    except Exception as e:
        return False, f"Error setting up auto-start: {e}"

def remove_auto_start():
    """Remove auto-start functionality"""
    try:
        startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        batch_file = os.path.join(startup_folder, 'WhatsApp_Blur_AutoStart.bat')
        
        if os.path.exists(batch_file):
            os.remove(batch_file)
            return True, "Auto-start disabled!"
        else:
            return True, "Auto-start was not enabled."
            
    except Exception as e:
        return False, f"Error removing auto-start: {e}"

def main():
    """Main function"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    print("WhatsApp Blur - Auto-Start Setup")
    print("=" * 40)
    print("1. Enable Auto-Start")
    print("2. Disable Auto-Start")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                success, message = setup_auto_start()
                if success:
                    print(f"✓ {message}")
                    messagebox.showinfo("Auto-Start", message)
                else:
                    print(f"✗ {message}")
                    messagebox.showerror("Auto-Start Error", message)
                break
                
            elif choice == '2':
                success, message = remove_auto_start()
                if success:
                    print(f"✓ {message}")
                    messagebox.showinfo("Auto-Start", message)
                else:
                    print(f"✗ {message}")
                    messagebox.showerror("Auto-Start Error", message)
                break
                
            elif choice == '3':
                print("Exiting...")
                break
                
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    root.destroy()

if __name__ == "__main__":
    main()
