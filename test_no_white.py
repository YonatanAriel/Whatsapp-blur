#!/usr/bin/env python3
"""
Test the no-white-window blur app
"""

import subprocess
import sys
import os

def main():
    print("🧪 Testing WhatsApp Blur (No White Window Version)")
    print("=" * 50)
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"📁 Working directory: {script_dir}")
    
    # Test the no-white version
    script_path = "whatsapp_blur_no_white.py"
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return
    
    print(f"🚀 Starting {script_path}...")
    print("📝 Press Ctrl+Alt+Q to toggle blur")
    print("⚠️ Make sure WhatsApp Desktop is open and visible")
    print("🔍 Watch for NO WHITE WINDOW appearing!")
    print("-" * 50)
    
    try:
        # Run the script
        subprocess.run([sys.executable, script_path], check=True)
    except KeyboardInterrupt:
        print("\n👋 Test stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Script failed with error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
