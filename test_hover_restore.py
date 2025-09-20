#!/usr/bin/env python3
"""
Automated hover/restore test for WhatsApp Blur (Windows only)

Requirements:
- WhatsApp Desktop running and visible in the foreground
- whatsapp_blur_final.py present in the same folder

Test verifies:
1) Blur overlay appears when WhatsApp is foreground-visible
2) On mouse hover over WhatsApp, overlay becomes click-through
3) After moving cursor outside WhatsApp bounds, overlay restores immediately (non-click-through)
"""

import os
import sys
import time
import ctypes
import subprocess

import win32gui
import win32con
import win32api
import win32process


def get_foreground_hwnd():
    try:
        return win32gui.GetForegroundWindow()
    except Exception:
        return None


def get_window_text(hwnd):
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


def find_whatsapp_hwnd():
    target = []

    def enum_cb(hwnd, acc):
        try:
            if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                title = win32gui.GetWindowText(hwnd) or ""
                cls = win32gui.GetClassName(hwnd) or ""
                if "whatsapp" in title.lower() or "whatsapp" in cls.lower():
                    acc.append(hwnd)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(enum_cb, target)
    except Exception:
        pass
    return target[0] if target else None


def bring_to_foreground(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def get_rect(hwnd):
    try:
        return win32gui.GetWindowRect(hwnd)
    except Exception:
        return None


def center_of_rect(rect):
    x1, y1, x2, y2 = rect
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def find_overlay_hwnd():
    matches = []

    def enum_cb(hwnd, acc):
        try:
            title = win32gui.GetWindowText(hwnd) or ""
            if title.strip() == "WhatsApp Blur":
                acc.append(hwnd)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(enum_cb, matches)
    except Exception:
        pass
    return matches[0] if matches else None


def exstyle(hwnd):
    try:
        return win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    except Exception:
        return 0


def window_from_point(pt):
    try:
        return win32gui.WindowFromPoint(pt)
    except Exception:
        return None


def set_cursor(pt):
    win32api.SetCursorPos(pt)


def wait_for(cond, timeout=5.0, poll=0.05):
    start = time.time()
    while time.time() - start < timeout:
        if cond():
            return True
        time.sleep(poll)
    return False


def main():
    if not sys.platform.startswith("win"):
        print("SKIP: Windows only test")
        return 0

    # Ensure DPI aware (avoid coordinate drift)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    wa = find_whatsapp_hwnd()
    if not wa:
        print("FAIL: WhatsApp window not found. Please open WhatsApp Desktop and make it visible.")
        return 1

    bring_to_foreground(wa)
    time.sleep(0.5)

    wa_rect = get_rect(wa)
    if not wa_rect:
        print("FAIL: Could not get WhatsApp window rect")
        return 1

    # Launch the blur app
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "whatsapp_blur_final.py")
    if not os.path.exists(app_path):
        print(f"FAIL: App not found: {app_path}")
        return 1

    print("Starting WhatsApp Blur...")
    proc = subprocess.Popen([sys.executable, app_path], cwd=script_dir)
    try:
        # Wait for overlay to appear
        ok = wait_for(lambda: find_overlay_hwnd() is not None, timeout=8.0)
        if not ok:
            print("FAIL: Overlay window did not appear")
            return 2

        overlay = find_overlay_hwnd()
        print(f"Overlay hwnd: {overlay}")

        # Initial state: should NOT be click-through
        style0 = exstyle(overlay)
        if style0 & win32con.WS_EX_TRANSPARENT:
            print("WARN: Overlay initially click-through; continuing test")

        # Move cursor to center of WA (hover)
        center = center_of_rect(wa_rect)
        set_cursor(center)
        time.sleep(0.25)

        # On hover: overlay should be click-through and WindowFromPoint should NOT be overlay
        style_hover = exstyle(overlay)
        wfp_hover = window_from_point(center)
        print(f"Hover exstyle=0x{style_hover:08X}, wfp={wfp_hover}, wa={wa}")
        if not (style_hover & win32con.WS_EX_TRANSPARENT):
            print("FAIL: Overlay did not become click-through on hover (WS_EX_TRANSPARENT not set)")
            return 3
        if wfp_hover == overlay:
            print("FAIL: WindowFromPoint returned overlay during hover; expected underlying WA or child")
            return 4

        # Move cursor outside WA bounds to trigger restore
        x1, y1, x2, y2 = wa_rect
        outside_pt = (min(x2 + 50, win32api.GetSystemMetrics(0) - 1), (y1 + y2) // 2)
        set_cursor(outside_pt)

        # Wait briefly for watcher to restore
        def restored():
            ov = find_overlay_hwnd()
            if not ov:
                return False
            st = exstyle(ov)
            return (st & win32con.WS_EX_TRANSPARENT) == 0

        if not wait_for(restored, timeout=1.0):
            st = exstyle(find_overlay_hwnd()) if find_overlay_hwnd() else 0
            print(f"FAIL: Overlay did not restore after leaving WA (exstyle=0x{st:08X})")
            return 5

        print("PASS: Hover -> click-through, leave -> restored immediately")
        return 0

    finally:
        # Cleanup cursor position a bit off the way
        set_cursor((10, 10))
        # Kill app
        try:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:
            pass


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
