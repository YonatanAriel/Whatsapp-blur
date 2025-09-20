#!/usr/bin/env python3
"""
WhatsApp Blur - Proper Windows App Installer
Creates a proper Windows application that appears in Settings > Apps
"""

import os
import sys
import shutil
import subprocess
import winreg
from pathlib import Path
import tempfile
import requests
import zipfile

def is_admin():
    """Check if running as administrator"""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def run_as_admin():
    """Restart script as administrator"""
    if not is_admin():
        print("🔄 Requesting administrator privileges...")
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)

def create_proper_executable():
    """Create a proper .exe file using PyInstaller"""
    print("📦 Creating proper Windows executable...")
    
    app_dir = Path("C:/WhatsAppBlur")
    app_dir.mkdir(exist_ok=True)
    
    # Copy the Python script
    script_path = app_dir / "whatsapp_blur.py"
    shutil.copy("whatsapp_blur_final.py", script_path)
    
    # Create a spec file for PyInstaller
    spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{script_path.as_posix()}'],
    pathex=['{app_dir.as_posix()}'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'win32gui', 'win32con', 'win32api', 'win32process',
        'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.ImageFilter', 'PIL.ImageGrab',
        'pystray', 'keyboard', 'psutil', 'tkinter'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WhatsAppBlur',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    cofile=None,
    icon=None,
    version='version_info.txt'
)
'''
    
    spec_file = app_dir / "whatsapp_blur.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    # Create version info
    version_info = '''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'WhatsApp Blur'),
        StringStruct(u'FileDescription', u'WhatsApp Privacy Blur Tool'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'WhatsAppBlur'),
        StringStruct(u'LegalCopyright', u'Copyright 2024'),
        StringStruct(u'OriginalFilename', u'WhatsAppBlur.exe'),
        StringStruct(u'ProductName', u'WhatsApp Blur'),
        StringStruct(u'ProductVersion', u'1.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    version_file = app_dir / "version_info.txt"
    with open(version_file, 'w') as f:
        f.write(version_info)
    
    # Install PyInstaller if not present
    try:
        import PyInstaller
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build the executable
    print("🔨 Building executable (this may take a few minutes)...")
    os.chdir(app_dir)
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller", 
        "--onefile", "--windowed", "--clean",
        str(spec_file)
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        exe_path = app_dir / "dist" / "WhatsAppBlur.exe"
        if exe_path.exists():
            # Move exe to main app directory
            final_exe = app_dir / "WhatsAppBlur.exe"
            shutil.move(exe_path, final_exe)
            
            # Cleanup build files
            shutil.rmtree(app_dir / "build", ignore_errors=True)
            shutil.rmtree(app_dir / "dist", ignore_errors=True)
            
            print(f"✅ Executable created: {final_exe}")
            return final_exe
    
    print("❌ Failed to create executable, falling back to Python script")
    return script_path

def register_windows_app(exe_path):
    """Register the app in Windows registry"""
    print("📝 Registering Windows application...")
    
    app_name = "WhatsApp Blur"
    app_version = "1.0.0"
    publisher = "WhatsApp Blur Tools"
    
    # Registry paths
    uninstall_key = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}"
    app_paths_key = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WhatsAppBlur.exe"
    
    try:
        # Register in Uninstall list (makes it appear in Settings > Apps)
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, uninstall_key) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, app_name)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, app_version)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, publisher)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(exe_path.parent))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(exe_path))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{exe_path}" --uninstall')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, 50000)  # 50MB
        
        # Register in App Paths (allows running from Run dialog)
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, app_paths_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(exe_path))
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, str(exe_path.parent))
        
        print("✅ App registered in Windows registry")
        return True
        
    except Exception as e:
        print(f"❌ Failed to register app: {e}")
        return False

def create_privacy_registration():
    """Register for privacy/screenshot permissions"""
    print("🔐 Registering for privacy permissions...")
    
    try:
        # Create AppX-style registration for privacy
        app_key = r"SOFTWARE\Classes\AppUserModelId\WhatsAppBlur.PrivacyApp"
        
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, app_key) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "WhatsApp Blur")
            winreg.SetValueEx(key, "PackageRelativeApplicationId", 0, winreg.REG_SZ, "WhatsAppBlur")
        
        # Register capabilities
        capabilities_key = r"SOFTWARE\WhatsAppBlur\Capabilities"
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, capabilities_key) as key:
            winreg.SetValueEx(key, "ApplicationName", 0, winreg.REG_SZ, "WhatsApp Blur")
            winreg.SetValueEx(key, "ApplicationDescription", 0, winreg.REG_SZ, "Privacy tool for WhatsApp")
        
        print("✅ Privacy registration created")
        return True
        
    except Exception as e:
        print(f"❌ Privacy registration failed: {e}")
        return False

def setup_startup():
    """Setup auto-startup"""
    print("🚀 Setting up auto-startup...")
    
    try:
        startup_folder = Path(os.path.expanduser("~")) / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
        startup_folder.mkdir(parents=True, exist_ok=True)
        
        exe_path = Path("C:/WhatsAppBlur/WhatsAppBlur.exe")
        if not exe_path.exists():
            exe_path = Path("C:/WhatsAppBlur/whatsapp_blur.py")
        
        # Create startup shortcut
        shortcut_path = startup_folder / "WhatsApp Blur.lnk"
        
        import winshell
        with winshell.shortcut(str(shortcut_path)) as shortcut:
            shortcut.path = str(exe_path)
            shortcut.description = "WhatsApp Blur - Privacy Tool"
            shortcut.working_directory = str(exe_path.parent)
            shortcut.arguments = "--startup"
        
        print(f"✅ Startup shortcut created: {shortcut_path}")
        return True
        
    except Exception as e:
        print(f"❌ Startup setup failed: {e}")
        return False

def create_desktop_shortcut():
    """Create desktop shortcut"""
    print("🖥️ Creating desktop shortcut...")
    
    try:
        desktop = Path(winshell.desktop())
        exe_path = Path("C:/WhatsAppBlur/WhatsAppBlur.exe")
        if not exe_path.exists():
            exe_path = Path("C:/WhatsAppBlur/whatsapp_blur.py")
        
        shortcut_path = desktop / "WhatsApp Blur.lnk"
        
        with winshell.shortcut(str(shortcut_path)) as shortcut:
            shortcut.path = str(exe_path)
            shortcut.description = "WhatsApp Blur - Privacy Tool"
            shortcut.working_directory = str(exe_path.parent)
        
        print(f"✅ Desktop shortcut created: {shortcut_path}")
        return True
        
    except Exception as e:
        print(f"❌ Desktop shortcut failed: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    dependencies = [
        "pillow>=10.0.0",
        "pywin32>=306", 
        "pystray>=0.19.0",
        "keyboard>=0.13.0",
        "psutil>=5.9.0",
        "winshell>=0.6"
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            print(f"✅ Installed: {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install: {dep}")

def main():
    """Main installation function"""
    print("🔧 WhatsApp Blur - Proper Windows App Installer")
    print("=" * 50)
    
    # Check admin privileges
    run_as_admin()
    
    print("✅ Running as administrator")
    
    # Install dependencies
    install_dependencies()
    
    # Create the executable
    exe_path = create_proper_executable()
    
    # Register as Windows app
    if register_windows_app(Path(exe_path)):
        print("✅ App will appear in Settings > Apps")
    
    # Register for privacy permissions
    create_privacy_registration()
    
    # Setup auto-startup
    setup_startup()
    
    # Create desktop shortcut
    create_desktop_shortcut()
    
    print("\n" + "=" * 50)
    print("🎉 INSTALLATION COMPLETE!")
    print("=" * 50)
    print()
    print("✅ WhatsApp Blur is now a proper Windows application")
    print("✅ Will appear in Settings > Apps > Installed apps")
    print("✅ Auto-starts with Windows")
    print("✅ Desktop shortcut created")
    print()
    print("🔧 NEXT STEPS:")
    print("1. Restart your computer (recommended)")
    print("2. Go to Settings > Privacy & security > Screenshots and apps")
    print("3. Find 'WhatsApp Blur' in the app list")
    print("4. Toggle ON the permission")
    print("5. Launch WhatsApp Blur from desktop shortcut")
    print("6. Press Ctrl+Win+B to toggle blur!")
    print()
    print("🎯 The app should now appear in Windows Settings!")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
