#!/usr/bin/env python3
"""
WhatsApp Blur Auto-Updater
Updates the installed version with the latest fixes
"""

import os
import sys
import shutil
import subprocess
import time

def main():
    print("🔄 WhatsApp Blur Auto-Updater")
    print("=" * 40)
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Source file (latest version)
    source_file = os.path.join(script_dir, "whatsapp_blur_simple.py")
    
    # Target locations to update
    target_locations = [
        os.path.join(script_dir, "whatsapp_blur_final.py"),  # Main file
        os.path.join(script_dir, "whatsapp_blur.py"),        # Original file
    ]
    
    # Check if source exists
    if not os.path.exists(source_file):
        print(f"❌ Source file not found: {source_file}")
        return False
    
    print(f"📄 Source: {source_file}")
    
    try:
        # Stop any running WhatsApp blur processes
        print("🛑 Stopping running WhatsApp blur processes...")
        try:
            subprocess.run(["taskkill", "/f", "/im", "python.exe"], 
                         capture_output=True, check=False)
            time.sleep(1)
        except:
            pass
        
        # Update each target location
        updated_count = 0
        for target in target_locations:
            try:
                print(f"📝 Updating: {target}")
                shutil.copy2(source_file, target)
                print(f"✅ Updated: {os.path.basename(target)}")
                updated_count += 1
            except Exception as e:
                print(f"❌ Failed to update {target}: {e}")
        
        if updated_count > 0:
            print(f"\n🎉 Successfully updated {updated_count} file(s)")
            print("📌 Changes applied:")
            print("   • Fixed visibility detection")
            print("   • Simplified auto-blur logic")
            print("   • Improved hover responsiveness")
            print("   • No more white freezing windows")
            
            # Ask if user wants to start the updated app
            try:
                choice = input("\n🚀 Start the updated WhatsApp Blur? (y/n): ").lower().strip()
                if choice in ['y', 'yes']:
                    print("🚀 Starting updated WhatsApp Blur...")
                    
                    # Start the updated app
                    updated_script = target_locations[0]  # Use the main file
                    subprocess.Popen([sys.executable, updated_script], 
                                   cwd=script_dir,
                                   creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                    
                    print("✅ WhatsApp Blur started successfully!")
                    return True
                else:
                    print("📋 You can manually start WhatsApp Blur later")
                    return True
            except KeyboardInterrupt:
                print("\n👋 Update completed")
                return True
        else:
            print("❌ No files were updated")
            return False
            
    except Exception as e:
        print(f"❌ Update failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n👋 Update cancelled")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        input("\nPress Enter to exit...")
