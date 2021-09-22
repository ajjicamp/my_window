# example code ; 버전처리하는 코드
import win32gui
import win32con
import win32api
import time

def window_enumeration_handler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))

def enum_windows():
    windows = []
    win32gui.EnumWindows(window_enumeration_handler, windows)
    return windows

def find_window(caption):
    hwnd = win32gui.FindWindow(None, caption)
    if hwnd == 0:
        windows = enum_windows()
        for handle, title in windows:
            if caption in title:
                hwnd = handle
                break
    return hwnd

hwnd = find_window("opstarter")
if hwnd != 0:
    static_hwnd = win32gui.GetDlgItem(hwnd, 0xFFFF)
    text = win32gui.GetWindowText(static_hwnd)
    print(text)
    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)