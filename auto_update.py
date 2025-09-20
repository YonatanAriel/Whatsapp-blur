#!/usr/bin/env python3
"""
WhatsApp Blur Auto-Updater
Updates the installed version with the latest fixes
"""

import shutil
import os
import sys
import subprocess
import time

def main():
    print("🔄 WhatsApp Blur Auto-Updater")
    print("=" * 50)
    
    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Source file (latest version) - use the final version as the authoritative source
    source_file = os.path.join(script_dir, "whatsapp_blur_final.py")
    
    # Target locations to update
    target_locations = [
        os.path.join(script_dir, "whatsapp_blur_final.py"),  # Local copy
        "C:\\Program Files\\WhatsApp Blur\\whatsapp_blur.py",  # System installation
        "C:\\Users\\Public\\WhatsApp Blur\\whatsapp_blur.py",  # Alternative location
    ]
    
    if not os.path.exists(source_file):
        print(f"❌ Source file not found: {source_file}")
        return
    
    print(f"✅ Source file found: {source_file}")
    
    # Update all target locations
    updated_count = 0
    for target in target_locations:
        try:
            target_dir = os.path.dirname(target)
            
            # Create directory if it doesn't exist
            if target_dir and not os.path.exists(target_dir):
                print(f"📁 Creating directory: {target_dir}")
                os.makedirs(target_dir, exist_ok=True)
            
            # Copy the file
            print(f"📄 Updating: {target}")
            shutil.copy2(source_file, target)  # Main file
            print(f"✅ Updated: {target}")
            updated_count += 1
            
        except PermissionError:
            print(f"⚠️ Permission denied: {target} (run as administrator)")
        except Exception as e:
            print(f"❌ Failed to update {target}: {e}")
    
    print(f"\n🎉 Updated {updated_count} locations")
    
    # Also update the launcher/shortcut
    try:
        # Import the shortcut creator
        import subprocess
        shortcut_script = os.path.join(script_dir, "create_shortcut.py")
        
        if os.path.exists(shortcut_script):
            print("🚀 Creating desktop shortcut...")
            result = subprocess.run([sys.executable, shortcut_script], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Desktop shortcut process completed")
                if result.stdout:
                    print(result.stdout.strip())
            else:
                print(f"⚠️ Shortcut creation had issues:")
                if result.stdout:
                    print(result.stdout.strip())
                if result.stderr:
                    print(f"Error details: {result.stderr.strip()}")
        else:
            print(f"⚠️ Shortcut creator not found: {shortcut_script}")
    except Exception as e:
        print(f"⚠️ Shortcut update failed: {e}")
    
    print("\n✅ Auto-update completed!")
    print("🔄 Restart the WhatsApp Blur app to use the latest version")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
