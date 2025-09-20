#!/usr/bin/env python3
"""
WhatsApp Blur - Manual Permission Granter
Grants screenshot permissions directly via registry
"""

import winreg
import subprocess
import sys

def is_admin():
    """Check if running as administrator"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    """Restart script as administrator"""
    if not is_admin():
        print("🔄 Requesting administrator privileges...")
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)

def grant_screenshot_permissions():
    """Grant screenshot permissions via registry"""
    print("🔐 Granting screenshot permissions...")
    
    try:
        # Grant to WhatsApp Blur specifically
        privacy_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy\CapabilityAccessManager\ConsentStore\graphicsCaptureProgrammatic"
        
        # Create app-specific permission
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, f"{privacy_key}\\NonPackaged\\C:#WhatsAppBlur#whatsapp_blur.py") as key:
            winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Allow")
            winreg.SetValueEx(key, "LastUsedTimeStart", 0, winreg.REG_QWORD, 0)
            winreg.SetValueEx(key, "LastUsedTimeStop", 0, winreg.REG_QWORD, 0)
        
        # Also grant to Python in general
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, f"{privacy_key}\\NonPackaged\\C:#Users#yonat#AppData#Local#Programs#Python#Python313#python.exe") as key:
            winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Allow")
            winreg.SetValueEx(key, "LastUsedTimeStart", 0, winreg.REG_QWORD, 0)
            winreg.SetValueEx(key, "LastUsedTimeStop", 0, winreg.REG_QWORD, 0)
        
        print("✅ Screenshot permissions granted!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to grant permissions: {e}")
        return False

def enable_global_screenshot_access():
    """Enable global screenshot access"""
    print("🌐 Enabling global screenshot access...")
    
    try:
        privacy_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy\CapabilityAccessManager\ConsentStore\graphicsCaptureProgrammatic"
        
        with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, privacy_key, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Allow")
        
        print("✅ Global screenshot access enabled!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to enable global access: {e}")
        return False

def test_permissions():
    """Test if permissions are working"""
    print("🧪 Testing screenshot permissions...")
    
    try:
        from PIL import ImageGrab
        test_img = ImageGrab.grab(bbox=(0, 0, 200, 200))
        test_img.save("permission_test.png")
        print("✅ Screenshot test successful! Permissions are working.")
        return True
    except Exception as e:
        print(f"❌ Screenshot test failed: {e}")
        return False

def main():
    """Main function"""
    print("🔧 WhatsApp Blur - Permission Granter")
    print("=" * 40)
    
    # Require admin
    run_as_admin()
    print("✅ Running as administrator")
    
    # Test current permissions
    if not test_permissions():
        print("\n🔧 Granting permissions...")
        
        # Try global first
        if enable_global_screenshot_access():
            print("✅ Global permissions granted")
        
        # Then specific app permissions
        if grant_screenshot_permissions():
            print("✅ App-specific permissions granted")
        
        # Test again
        print("\n🧪 Testing permissions after grant...")
        if test_permissions():
            print("🎉 SUCCESS! Permissions are now working!")
        else:
            print("❌ Still having permission issues")
            print("\n🔧 Manual steps:")
            print("1. Settings > Privacy & security > Screenshots and apps")
            print("2. Turn ON: 'Let desktop apps take screenshots'")
            print("3. Find 'Python' or 'WhatsApp Blur' in app list")
            print("4. Toggle ON the permission")
    else:
        print("✅ Permissions already working!")
    
    print("\n" + "=" * 40)
    print("🎉 READY TO USE!")
    print("=" * 40)
    print("1. Run: C:\\WhatsAppBlur\\WhatsAppBlur.bat")
    print("2. Press Ctrl+Win+B to toggle blur")
    print("3. Enjoy your privacy! 🔒")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
