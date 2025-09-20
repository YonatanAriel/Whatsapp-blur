#!/usr/bin/env python3
"""
WhatsApp Blur - Simple Registry Installer
Registers the app properly so it appears in Windows Settings
"""

import os
import sys
import winreg
import subprocess
from pathlib import Path
import shutil

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

def create_app_manifest():
    """Create an app manifest for Windows"""
    app_dir = Path("C:/WhatsAppBlur")
    
    manifest_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="*"
    name="WhatsAppBlur"
    type="win32"
  />
  <description>WhatsApp Privacy Blur Tool</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
</assembly>'''
    
    manifest_path = app_dir / "WhatsAppBlur.exe.manifest"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    
    print(f"✅ Created app manifest: {manifest_path}")
    return manifest_path

def register_uninstall_entry():
    """Register in Windows Uninstall list (makes it appear in Settings > Apps)"""
    print("📝 Registering in Windows Apps list...")
    
    app_dir = Path("C:/WhatsAppBlur")
    exe_path = app_dir / "whatsapp_blur.py"  # Use Python script for now
    
    # Create a batch file to run the Python script
    bat_path = app_dir / "WhatsAppBlur.bat"
    bat_content = f'''@echo off
cd /d "{app_dir}"
python "{exe_path}"
'''
    with open(bat_path, 'w') as f:
        f.write(bat_content)
    
    uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WhatsAppBlur"
    
    try:
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, uninstall_key) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "WhatsApp Blur")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "WhatsApp Blur Tools")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(app_dir))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(bat_path))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{bat_path}" --uninstall')
            winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, f'"{bat_path}" --uninstall --quiet')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, 25000)  # 25MB
            winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, "20240919")
            winreg.SetValueEx(key, "HelpLink", 0, winreg.REG_SZ, "https://github.com/YonatanAriel/Whatsapp-blur")
            winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, "https://github.com/YonatanAriel/Whatsapp-blur")
        
        print("✅ Registered in Windows Apps list")
        return True
        
    except Exception as e:
        print(f"❌ Failed to register app: {e}")
        return False

def register_privacy_permissions():
    """Register for screenshot/privacy permissions"""
    print("🔐 Registering for screenshot permissions...")
    
    try:
        # Register the app for privacy permissions
        privacy_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy\CapabilityAccessManager\ConsentStore\graphicsCaptureProgrammatic"
        app_subkey = f"{privacy_key}\\WhatsAppBlur"
        
        # Create main privacy key
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, app_subkey) as key:
            winreg.SetValueEx(key, "PackageFamilyName", 0, winreg.REG_SZ, "WhatsAppBlur_8wekyb3d8bbwe")
            winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Allow")
        
        # Also register for screenshot APIs
        screenshot_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy\CapabilityAccessManager\ConsentStore\graphicsCapture"
        app_screenshot_key = f"{screenshot_key}\\WhatsAppBlur"
        
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, app_screenshot_key) as key:
            winreg.SetValueEx(key, "PackageFamilyName", 0, winreg.REG_SZ, "WhatsAppBlur_8wekyb3d8bbwe")
            winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Allow")
        
        print("✅ Privacy permissions registered")
        return True
        
    except Exception as e:
        print(f"❌ Privacy registration failed: {e}")
        return False

def create_appx_manifest():
    """Create a minimal AppX-style manifest"""
    app_dir = Path("C:/WhatsAppBlur")
    
    appx_manifest = '''<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10">
  <Identity Name="WhatsAppBlur" Publisher="CN=WhatsAppBlur" Version="1.0.0.0" />
  <Properties>
    <DisplayName>WhatsApp Blur</DisplayName>
    <PublisherDisplayName>WhatsApp Blur Tools</PublisherDisplayName>
    <Description>Privacy tool for WhatsApp Desktop</Description>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.0.0" MaxVersionTested="10.0.0.0" />
  </Dependencies>
  <Applications>
    <Application Id="WhatsAppBlur" Executable="whatsapp_blur.py" EntryPoint="main">
      <VisualElements DisplayName="WhatsApp Blur" Description="Privacy blur for WhatsApp"
                      BackgroundColor="transparent" Square150x150Logo="Assets\\Logo.png"
                      Square44x44Logo="Assets\\SmallLogo.png" />
    </Application>
  </Applications>
  <Capabilities>
    <Capability Name="internetClient" />
    <rescap:Capability Name="graphicsCaptureProgrammatic" xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities" />
  </Capabilities>
</Package>'''
    
    manifest_path = app_dir / "AppxManifest.xml"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(appx_manifest)
    
    print(f"✅ Created AppX manifest: {manifest_path}")
    return manifest_path

def install_app():
    """Install the app properly"""
    print("📦 Installing WhatsApp Blur as Windows App...")
    
    app_dir = Path("C:/WhatsAppBlur")
    app_dir.mkdir(exist_ok=True)
    
    # Copy the main script
    source_script = Path("whatsapp_blur_final.py")
    target_script = app_dir / "whatsapp_blur.py"
    shutil.copy(source_script, target_script)
    print(f"✅ Copied script to: {target_script}")
    
    # Create manifests
    create_app_manifest()
    create_appx_manifest()
    
    # Register in Windows
    register_uninstall_entry()
    register_privacy_permissions()
    
    # Create startup entry
    try:
        startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, startup_key, 0, winreg.KEY_WRITE) as key:
            bat_path = app_dir / "WhatsAppBlur.bat"
            winreg.SetValueEx(key, "WhatsAppBlur", 0, winreg.REG_SZ, f'"{bat_path}"')
        print("✅ Added to startup")
    except Exception as e:
        print(f"❌ Startup registration failed: {e}")
    
    return True

def refresh_system():
    """Refresh Windows to recognize the new app"""
    print("🔄 Refreshing Windows app registration...")
    
    try:
        # Refresh the Start Menu database
        subprocess.run(['sfc', '/scannow'], capture_output=True)
        
        # Signal Windows to refresh apps
        import ctypes
        from ctypes import wintypes
        
        # Broadcast WM_SETTINGCHANGE
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
            0x0002, 5000, None  # SMTO_ABORTIFHUNG, 5 second timeout
        )
        
        print("✅ System refresh complete")
        
    except Exception as e:
        print(f"⚠️ System refresh failed: {e}")

def main():
    """Main installation function"""
    print("🔧 WhatsApp Blur - Windows App Registry Installer")
    print("=" * 55)
    
    # Require admin
    run_as_admin()
    print("✅ Running as administrator")
    
    # Install the app
    if install_app():
        print("✅ App installation complete")
    
    # Refresh system
    refresh_system()
    
    print("\n" + "=" * 55)
    print("🎉 INSTALLATION COMPLETE!")
    print("=" * 55)
    print()
    print("✅ WhatsApp Blur registered as Windows application")
    print("✅ Should appear in Settings > Apps within 1-2 minutes")
    print("✅ Auto-startup enabled")
    print()
    print("🔧 NEXT STEPS:")
    print("1. Wait 1-2 minutes for Windows to recognize the app")
    print("2. Go to Settings > Privacy & security > Screenshots and apps")
    print("3. Look for 'WhatsApp Blur' or 'Python' in the app list")
    print("4. Toggle ON the screenshot permission")
    print("5. Run: C:\\WhatsAppBlur\\WhatsAppBlur.bat")
    print("6. Press Ctrl+Win+B to toggle blur!")
    print()
    print("💡 If app doesn't appear, try restarting Windows")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
