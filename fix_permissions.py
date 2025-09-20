#!/usr/bin/env python3
"""
WhatsApp Blur - Privacy Permissions Helper
This script helps you configure the exact Windows privacy settings needed.
"""

import os
import subprocess
import sys
import webbrowser
from tkinter import messagebox
import tkinter as tk

def open_privacy_settings():
    """Open the specific privacy settings for screenshot permissions"""
    try:
        # Try the direct Windows 11 graphics capture settings
        subprocess.run(['ms-settings:privacy-graphicscaptureprogrammatic'], shell=True)
        return True
    except:
        try:
            # Fallback to general screenshot settings
            subprocess.run(['ms-settings:privacy-webcam'], shell=True)
            return True
        except:
            return False

def show_permission_guide():
    """Show a detailed guide for setting up permissions"""
    
    guide_window = tk.Tk()
    guide_window.title("WhatsApp Blur - Privacy Permission Setup")
    guide_window.geometry("700x500")
    guide_window.configure(bg='white')
    
    # Create main frame
    main_frame = tk.Frame(guide_window, bg='white')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Title
    title_label = tk.Label(main_frame, text="🔐 Privacy Permission Setup", 
                          font=('Arial', 16, 'bold'), bg='white', fg='#2e7d32')
    title_label.pack(pady=(0, 20))
    
    # Problem explanation
    problem_text = tk.Text(main_frame, height=8, wrap=tk.WORD, font=('Arial', 10))
    problem_text.insert('1.0', """🔍 THE ISSUE YOU SAW:
When you checked Privacy Settings, only Microsoft Teams and WhatsApp appeared in the list, but "WhatsApp Blur" didn't show up.

✅ THIS IS COMPLETELY NORMAL!

Desktop applications (.exe files) like our WhatsApp Blur app are controlled by a master toggle, NOT individual app permissions.

🎯 WHAT YOU NEED TO DO:
You need to enable the "Let desktop apps access graphics capture" setting.""")
    problem_text.configure(state='disabled', bg='#f5f5f5')
    problem_text.pack(fill=tk.X, pady=(0, 15))
    
    # Instructions frame
    instructions_frame = tk.Frame(main_frame, bg='white')
    instructions_frame.pack(fill=tk.X, pady=(0, 15))
    
    instructions_label = tk.Label(instructions_frame, text="📋 STEP-BY-STEP INSTRUCTIONS:", 
                                 font=('Arial', 12, 'bold'), bg='white', fg='#1976d2')
    instructions_label.pack(anchor='w')
    
    steps_text = tk.Text(instructions_frame, height=10, wrap=tk.WORD, font=('Arial', 10))
    steps_text.insert('1.0', """1. Click "Open Privacy Settings" button below
2. This opens "Screenshots and screen recording" settings
3. Make sure these are ENABLED:
   ✅ "Screenshots and screen recording access" = ON
   ✅ "Let apps take screenshots and record the screen" = ON  
   ✅ "Let desktop apps take screenshots and record the screen" = ON
   
⚠️  The third one is the most important - it controls our app!

4. After enabling, restart WhatsApp Blur
5. Test with Ctrl+Alt+Q (new shortcut!)

💡 Why desktop apps work this way:
• UWP Apps (Microsoft Store) = Individual permissions
• Desktop Apps (.exe files) = Master toggle permission""")
    steps_text.configure(state='disabled', bg='#e3f2fd')
    steps_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
    
    # Buttons frame
    buttons_frame = tk.Frame(main_frame, bg='white')
    buttons_frame.pack(fill=tk.X, pady=(15, 0))
    
    # Open Settings button
    settings_btn = tk.Button(buttons_frame, text="🔧 Open Privacy Settings", 
                           command=lambda: open_privacy_settings(),
                           bg='#4caf50', fg='white', font=('Arial', 11, 'bold'),
                           relief=tk.FLAT, padx=20, pady=10)
    settings_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    # Test App button
    test_btn = tk.Button(buttons_frame, text="🧪 Test App", 
                        command=lambda: test_whatsapp_blur(),
                        bg='#2196f3', fg='white', font=('Arial', 11, 'bold'),
                        relief=tk.FLAT, padx=20, pady=10)
    test_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    # Close button
    close_btn = tk.Button(buttons_frame, text="✅ Done", 
                         command=guide_window.destroy,
                         bg='#ff9800', fg='white', font=('Arial', 11, 'bold'),
                         relief=tk.FLAT, padx=20, pady=10)
    close_btn.pack(side=tk.RIGHT)
    
    guide_window.mainloop()

def test_whatsapp_blur():
    """Test if WhatsApp Blur is working"""
    try:
        # Try to run the test script
        result = subprocess.run([sys.executable, 'test_and_launch.py'], 
                              capture_output=True, text=True, cwd=r'c:\Users\yonat\repos\Whatsapp blur')
        
        if result.returncode == 0:
            messagebox.showinfo("✅ Test Successful", 
                              "WhatsApp Blur test completed!\n\n"
                              "Check the console output for details.\n"
                              "Try pressing Ctrl+Alt+Q to toggle blur!")
        else:
            messagebox.showerror("❌ Test Failed", 
                               "WhatsApp Blur test failed.\n\n"
                               "Please check:\n"
                               "1. Privacy permissions are enabled\n"
                               "2. WhatsApp is running\n"
                               "3. Run as Administrator if needed")
    except Exception as e:
        messagebox.showerror("Error", f"Could not run test: {e}")

def main():
    """Main function"""
    print("🔐 WhatsApp Blur - Privacy Permissions Helper")
    print("=" * 50)
    print()
    print("This helper will guide you through setting up the privacy permissions")
    print("needed for WhatsApp Blur to work properly.")
    print()
    print("🎯 The key issue: Desktop apps need 'Let desktop apps access graphics capture' enabled")
    print()
    
    # Show the guide
    try:
        show_permission_guide()
    except Exception as e:
        print(f"Error showing GUI: {e}")
        print("\n📋 Manual Instructions:")
        print("1. Open Windows Settings")
        print("2. Go to Privacy & security > Screenshots and screen recording")
        print("3. Enable 'Let desktop apps take screenshots and record the screen'")
        print("4. Restart WhatsApp Blur")
        print("5. Test with Ctrl+Alt+Q")

if __name__ == "__main__":
    main()
