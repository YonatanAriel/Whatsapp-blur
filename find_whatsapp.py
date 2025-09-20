#!/usr/bin/env python3
"""
List all visible windows to find WhatsApp
"""

import win32gui
import win32process
import psutil

def list_all_windows():
    """List all visible windows to help find WhatsApp"""
    print("🔍 All visible windows:")
    print("=" * 60)
    
    def enum_window_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.strip():  # Only show windows with titles
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    rect = win32gui.GetWindowRect(hwnd)
                    size = f"{rect[2]-rect[0]}x{rect[3]-rect[1]}"
                    
                    # Highlight potential WhatsApp windows
                    marker = "🎯" if any(keyword in title.lower() for keyword in ['whats', 'chat', 'message']) else "  "
                    marker = "✅" if 'whatsapp' in title.lower() else marker
                    
                    print(f'{marker} "{title}" | {process.name()} | {size}')
                except:
                    print(f'   "{title}" | Unknown process | Unknown size')

    windows = []
    win32gui.EnumWindows(enum_window_callback, windows)

def find_whatsapp_windows():
    """Find windows that might be WhatsApp"""
    print("\n🎯 Searching for WhatsApp-related windows...")
    print("=" * 50)
    
    whatsapp_keywords = ['whatsapp', 'whats app', 'chat', 'message']
    found_windows = []
    
    def enum_window_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process = psutil.Process(pid)
                process_name = process.name().lower()
                title_lower = title.lower()
                
                # Check if this could be WhatsApp
                is_whatsapp = (
                    'whatsapp' in process_name or 
                    'whatsapp' in title_lower or
                    (process_name == 'applicationframehost.exe' and any(keyword in title_lower for keyword in whatsapp_keywords))
                )
                
                if is_whatsapp:
                    rect = win32gui.GetWindowRect(hwnd)
                    found_windows.append({
                        'hwnd': hwnd,
                        'title': title,
                        'process': process_name,
                        'pid': pid,
                        'rect': rect
                    })
                    
                    print(f'✅ Found potential WhatsApp window:')
                    print(f'   Title: "{title}"')
                    print(f'   Process: {process_name}')
                    print(f'   PID: {pid}')
                    print(f'   HWND: {hwnd}')
                    print(f'   Size: {rect[2]-rect[0]}x{rect[3]-rect[1]}')
                    print(f'   Position: ({rect[0]}, {rect[1]})')
                    
                    # Check window state
                    if win32gui.IsIconic(hwnd):
                        print(f'   ⚠️ MINIMIZED!')
                    if not win32gui.IsWindowVisible(hwnd):
                        print(f'   ⚠️ NOT VISIBLE!')
                    
                    print('---')
                    
            except:
                pass

    windows = []
    win32gui.EnumWindows(enum_window_callback, windows)
    
    return found_windows

if __name__ == "__main__":
    print("🔍 Window Detection Debug Tool")
    print("=" * 40)
    
    whatsapp_windows = find_whatsapp_windows()
    
    if not whatsapp_windows:
        print("\n❌ No WhatsApp windows found!")
        print("\n📋 Let's see all windows to help identify WhatsApp:")
        list_all_windows()
        print("\n💡 Look for windows marked with 🎯 - they might be WhatsApp!")
    else:
        print(f"\n✅ Found {len(whatsapp_windows)} potential WhatsApp window(s)!")
        print("\nIf the blur still doesn't work, WhatsApp might be:")
        print("1. Running but minimized")
        print("2. Running as a different process name")
        print("3. The window detection needs adjustment")
