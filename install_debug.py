#!/usr/bin/env python3
"""
WhatsApp Blur - Debug Installer
Keeps window open to show errors
"""

import os
import sys
import shutil
import subprocess
import ctypes
from pathlib import Path
import traceback

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def pause_before_exit():
    """Keep window open"""
    print("\n" + "="*50)
    input("Press Enter to exit...")

def simple_install():
    """Simple installation with debug output"""
    try:
        print("🔧 WhatsApp Blur Debug Installer")
        print("=" * 50)
        
        # Check admin rights
        print(f"Admin rights: {'✅ Yes' if is_admin() else '❌ No'}")
        if not is_admin():
            print("❌ ERROR: Administrator rights required!")
            print("Please run as administrator")
            pause_before_exit()
            return False
        
        # Check if source files exist
        source_dir = Path(__file__).parent
        main_file = source_dir / "whatsapp_blur_dpi_fixed.py"
        req_file = source_dir / "requirements.txt"
        
        print(f"Source directory: {source_dir}")
        print(f"Main file exists: {'✅' if main_file.exists() else '❌'} {main_file}")
        print(f"Requirements exists: {'✅' if req_file.exists() else '❌'} {req_file}")
        
        if not main_file.exists():
            print("❌ ERROR: Main application file not found!")
            pause_before_exit()
            return False
        
        # Create installation directory
        install_dir = Path("C:/WhatsAppBlur")  # Simpler path
        print(f"Creating install directory: {install_dir}")
        
        try:
            install_dir.mkdir(exist_ok=True, parents=True)
            print("✅ Install directory created")
        except Exception as e:
            print(f"❌ Error creating install directory: {e}")
            pause_before_exit()
            return False
        
        # Copy files
        print("📁 Copying files...")
        try:
            target_main = install_dir / "whatsapp_blur.py"
            shutil.copy2(main_file, target_main)
            print(f"✅ Main file copied to: {target_main}")
            
            if req_file.exists():
                target_req = install_dir / "requirements.txt"
                shutil.copy2(req_file, target_req)
                print(f"✅ Requirements copied to: {target_req}")
        except Exception as e:
            print(f"❌ Error copying files: {e}")
            pause_before_exit()
            return False
        
        # Create simple launcher
        print("🚀 Creating launcher...")
        try:
            launcher_content = f'''@echo off
title WhatsApp Blur
cd /d "{install_dir}"
echo Starting WhatsApp Blur...
python whatsapp_blur.py
pause
'''
            launcher_path = install_dir / "start_whatsapp_blur.bat"
            with open(launcher_path, 'w') as f:
                f.write(launcher_content)
            print(f"✅ Launcher created: {launcher_path}")
        except Exception as e:
            print(f"❌ Error creating launcher: {e}")
            pause_before_exit()
            return False
        
        # Create desktop shortcut
        print("🖥️ Creating desktop shortcut...")
        try:
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "WhatsApp Blur.bat"
            
            shortcut_content = f'''@echo off
cd /d "{install_dir}"
python whatsapp_blur.py
'''
            with open(shortcut_path, 'w') as f:
                f.write(shortcut_content)
            print(f"✅ Desktop shortcut created: {shortcut_path}")
        except Exception as e:
            print(f"⚠️ Could not create desktop shortcut: {e}")
        
        # Install dependencies
        print("📦 Installing Python dependencies...")
        try:
            if req_file.exists():
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(req_file)
                ], capture_output=True, text=True, cwd=str(install_dir))
                
                if result.returncode == 0:
                    print("✅ Dependencies installed successfully")
                else:
                    print(f"⚠️ Dependency installation warning:")
                    print(f"STDOUT: {result.stdout}")
                    print(f"STDERR: {result.stderr}")
            else:
                print("⚠️ No requirements.txt found, skipping dependency installation")
        except Exception as e:
            print(f"⚠️ Error installing dependencies: {e}")
        
        # Test the installation
        print("🧪 Testing installation...")
        try:
            test_result = subprocess.run([
                sys.executable, "-c", 
                f"import sys; sys.path.insert(0, '{install_dir}'); "
                f"print('Python can access install directory')"
            ], capture_output=True, text=True)
            
            if test_result.returncode == 0:
                print("✅ Installation test passed")
            else:
                print(f"⚠️ Installation test warning: {test_result.stderr}")
        except Exception as e:
            print(f"⚠️ Could not test installation: {e}")
        
        print("\n🎉 INSTALLATION COMPLETED!")
        print("=" * 50)
        print(f"📁 Installed to: {install_dir}")
        print(f"🖥️ Desktop shortcut: {desktop / 'WhatsApp Blur.bat'}")
        print(f"🚀 Direct launcher: {launcher_path}")
        print("\n📋 NEXT STEPS:")
        print("1. Double-click the desktop shortcut to start")
        print("2. Grant privacy permissions when prompted")
        print("3. Use Ctrl+Alt+B to toggle blur")
        print("\n⚠️ IMPORTANT: You still need to grant privacy permissions!")
        print("   Settings > Privacy & Security > Screenshots")
        
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        print("TRACEBACK:")
        traceback.print_exc()
        return False

def main():
    """Main installer"""
    try:
        success = simple_install()
        if not success:
            print("\n❌ Installation failed!")
        pause_before_exit()
    except Exception as e:
        print(f"❌ INSTALLER CRASHED: {e}")
        traceback.print_exc()
        pause_before_exit()

if __name__ == "__main__":
    main()
