#!/usr/bin/env python3
"""
WhatsApp Blur - Simple User Installer
No admin rights required!
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import traceback

def pause_before_exit():
    """Keep window open"""
    print("\n" + "="*50)
    input("Press Enter to exit...")

def create_simple_icon():
    """Create a simple icon file"""
    try:
        from PIL import Image, ImageDraw
        
        # Create 64x64 icon
        size = 64
        image = Image.new('RGB', (size, size), (25, 118, 210))  # Blue background
        draw = ImageDraw.Draw(image)
        
        # Draw simple "WB" text
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = None
        
        text = "WB"
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (size - text_width) // 2
            y = (size - text_height) // 2
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
        else:
            # Fallback simple shapes
            draw.rectangle([10, 10, size-10, size-10], outline=(255, 255, 255), width=3)
            draw.ellipse([20, 20, size-20, size-20], fill=(255, 255, 255))
        
        return image
    except Exception as e:
        print(f"Error creating icon: {e}")
        return None

def simple_user_install():
    """Simple installation in user directory"""
    try:
        print("🔧 WhatsApp Blur - Simple User Installer")
        print("=" * 50)
        print("✅ No admin rights required!")
        
        # Use user's AppData directory
        user_data = Path(os.environ['APPDATA'])
        install_dir = user_data / "WhatsAppBlur"
        
        print(f"📁 Installing to: {install_dir}")
        
        # Create directory
        install_dir.mkdir(exist_ok=True, parents=True)
        print("✅ Install directory created")
        
        # Check source files
        source_dir = Path(__file__).parent
        main_file = source_dir / "whatsapp_blur_dpi_fixed.py"
        req_file = source_dir / "requirements.txt"
        
        print(f"Source files check:")
        print(f"  Main app: {'✅' if main_file.exists() else '❌'} {main_file}")
        print(f"  Requirements: {'✅' if req_file.exists() else '❌'} {req_file}")
        
        if not main_file.exists():
            print("❌ ERROR: whatsapp_blur_dpi_fixed.py not found!")
            pause_before_exit()
            return False
        
        # Copy files
        print("📁 Copying files...")
        target_main = install_dir / "whatsapp_blur.py"
        shutil.copy2(main_file, target_main)
        print(f"✅ Main app copied to: {target_main}")
        
        if req_file.exists():
            target_req = install_dir / "requirements.txt"
            shutil.copy2(req_file, target_req)
            print(f"✅ Requirements copied to: {target_req}")
        
        # Create icon
        print("🎨 Creating app icon...")
        try:
            icon_image = create_simple_icon()
            if icon_image:
                icon_path = install_dir / "whatsapp_blur.ico"
                icon_image.save(str(icon_path), format='ICO', sizes=[(64, 64), (32, 32), (16, 16)])
                print(f"✅ Icon created: {icon_path}")
            else:
                print("⚠️ Could not create icon (will use default)")
        except Exception as e:
            print(f"⚠️ Icon creation failed: {e}")
        
        # Install dependencies
        print("📦 Installing dependencies...")
        try:
            if req_file.exists():
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "--user", "-r", str(req_file)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Dependencies installed successfully")
                else:
                    print(f"⚠️ Some dependencies may have failed:")
                    if result.stderr:
                        print(f"  Error: {result.stderr[:200]}...")
        except Exception as e:
            print(f"⚠️ Dependency installation error: {e}")
        
        # Create startup launcher
        print("🚀 Creating startup launcher...")
        try:
            startup_folder = Path(os.environ['APPDATA']) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            startup_bat = startup_folder / "WhatsApp Blur.bat"
            
            startup_content = f'''@echo off
title WhatsApp Blur
cd /d "{install_dir}"
python whatsapp_blur.py > nul 2>&1
'''
            with open(startup_bat, 'w') as f:
                f.write(startup_content)
            print(f"✅ Auto-startup created: {startup_bat}")
        except Exception as e:
            print(f"⚠️ Auto-startup creation failed: {e}")
        
        # Create desktop shortcut
        print("🖥️ Creating desktop shortcut...")
        try:
            desktop = Path.home() / "Desktop"
            desktop_bat = desktop / "WhatsApp Blur.bat"
            
            desktop_content = f'''@echo off
title WhatsApp Blur
cd /d "{install_dir}"
echo Starting WhatsApp Blur...
echo.
echo ✅ App starting in background...
echo ✅ Use Ctrl+Win+B to toggle blur
echo ✅ Right-click system tray icon for options
echo.
python whatsapp_blur.py
pause
'''
            with open(desktop_bat, 'w') as f:
                f.write(desktop_content)
            print(f"✅ Desktop shortcut created: {desktop_bat}")
        except Exception as e:
            print(f"⚠️ Desktop shortcut creation failed: {e}")
        
        # Create manual launcher for first time
        print("📋 Creating manual launcher...")
        try:
            manual_bat = install_dir / "start_manual.bat"
            manual_content = f'''@echo off
title WhatsApp Blur - Manual Start
cd /d "{install_dir}"
echo.
echo 🔐 WhatsApp Blur - Manual Launcher
echo ================================
echo.
echo ✅ Keyboard shortcut: Ctrl+Win+B
echo ✅ This will start automatically on next boot
echo ✅ Check system tray for icon
echo.
echo Starting application...
python whatsapp_blur.py
echo.
echo Application stopped.
pause
'''
            with open(manual_bat, 'w') as f:
                f.write(manual_content)
            print(f"✅ Manual launcher: {manual_bat}")
        except Exception as e:
            print(f"⚠️ Manual launcher creation failed: {e}")
        
        print("\n🎉 INSTALLATION COMPLETED!")
        print("=" * 50)
        print(f"📁 Installed to: {install_dir}")
        print(f"🖥️ Desktop shortcut: {desktop / 'WhatsApp Blur.bat'}")
        print(f"🚀 Auto-start: Will start with Windows")
        print(f"⌨️ Shortcut: Ctrl+Win+B (safe, no conflicts!)")
        
        print("\n📋 NEXT STEPS:")
        print("1. Double-click desktop shortcut to start now")
        print("2. Grant privacy permissions:")
        print("   Settings > Privacy & Security > Screenshots")
        print("   Enable 'Let desktop apps take screenshots'")
        print("3. Use Ctrl+Win+B to toggle blur anytime!")
        print("4. App will auto-start on next Windows boot")
        
        print("\n🔍 FOR PRIVACY SETTINGS:")
        print("The app will appear in Privacy Settings after first run!")
        
        # Ask to start now
        try:
            start_now = input("\n🚀 Start WhatsApp Blur now? (y/n): ").lower().strip()
            if start_now in ['y', 'yes', '']:
                print("Starting application...")
                subprocess.Popen([sys.executable, str(target_main)], 
                               cwd=str(install_dir), 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                print("✅ Application started in background!")
                print("✅ Check system tray for icon")
                print("✅ Use Ctrl+Win+B to toggle blur")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ INSTALLATION ERROR: {e}")
        traceback.print_exc()
        return False

def main():
    """Main installer"""
    try:
        success = simple_user_install()
        if not success:
            print("\n❌ Installation failed!")
        pause_before_exit()
    except Exception as e:
        print(f"❌ INSTALLER CRASHED: {e}")
        traceback.print_exc()
        pause_before_exit()

if __name__ == "__main__":
    main()
