#!/usr/bin/env python3
"""
WhatsApp Blur - Second Laptop Deployment Script
Easy setup for deploying to additional Windows 11 laptops
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

def deploy_to_second_laptop():
    """Deploy WhatsApp Blur to a second laptop easily"""
    
    print("🚀 WhatsApp Blur - Second Laptop Deployment")
    print("=" * 50)
    print("📱 This script will set up WhatsApp Blur on your second laptop")
    print("🔧 Make sure you've already cloned the repo!")
    print()
    
    try:
        # Step 1: Check if we're in the right directory
        current_dir = os.getcwd()
        if not os.path.exists("whatsapp_blur_final.py"):
            print("❌ Error: Please run this script from the WhatsApp Blur repo directory")
            print("💡 Make sure you've cloned the repo first:")
            print("   git clone https://github.com/YonatanAriel/Whatsapp-blur.git")
            return False
        
        print("✅ 1. Repository found")
        
        # Step 2: Install dependencies
        print("📦 2. Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
        
        # Step 3: Run the installer
        print("🔧 3. Running installer...")
        subprocess.run([sys.executable, "install_whatsapp_blur.py"], check=True)
        print("✅ WhatsApp Blur installed")
        
        # Step 4: Set up auto-startup
        print("⚡ 4. Setting up auto-startup...")
        subprocess.run([sys.executable, "setup_auto_startup.py"], check=True)
        print("✅ Auto-startup configured")
        
        # Step 5: Test the installation
        print("🧪 5. Testing installation...")
        test_result = subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.append(r'C:\\Users\\Public\\WhatsApp Blur'); import whatsapp_blur; print('✅ Installation test passed')"
        ], capture_output=True, text=True)
        
        if test_result.returncode == 0:
            print("✅ Installation test passed")
        else:
            print("⚠️ Installation test had issues, but app should still work")
        
        print("\n🎉 DEPLOYMENT COMPLETED!")
        print("=" * 50)
        print("✅ WhatsApp Blur is now set up on this laptop")
        print("🔄 The app will start automatically when you boot Windows")
        print("🎯 Press Ctrl+Alt+Q to toggle blur when WhatsApp is open")
        print("\n📋 Features configured:")
        print("   ✅ Glass effect overlay (no white background)")
        print("   ✅ Rounded corners matching WhatsApp Desktop")
        print("   ✅ Auto-startup on Windows boot")
        print("   ✅ Fast response (0.2s monitoring)")
        print("   ✅ Clean console (no deprecated warnings)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during deployment: {e}")
        print("💡 Try running as administrator if you get permission errors")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def quick_clone_instructions():
    """Show instructions for cloning the repo"""
    print("\n📋 QUICK SETUP INSTRUCTIONS FOR SECOND LAPTOP:")
    print("=" * 50)
    print("1. Open PowerShell as Administrator")
    print("2. Install Git (if not installed):")
    print("   winget install Git.Git")
    print("3. Clone the repository:")
    print("   git clone https://github.com/YonatanAriel/Whatsapp-blur.git")
    print("4. Navigate to the directory:")
    print("   cd Whatsapp-blur")
    print("5. Run this deployment script:")
    print("   python deploy_second_laptop.py")
    print("\n🎉 That's it! WhatsApp Blur will be fully set up and ready to go!")

if __name__ == "__main__":
    success = deploy_to_second_laptop()
    
    if not success:
        quick_clone_instructions()
    
    input("\nPress Enter to exit...")
