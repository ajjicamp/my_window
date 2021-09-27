import win32gui
import win32con


def getwindowlist():
    def ehandler(hwnd, hwnd_list: list):
    # def ehandler(hwnd, output: list):
    # def ehandler(hwnd, output):
        title = win32gui.GetWindowText(hwnd)
        if win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            hwnd_list.append((title, hwnd))
            # output.append((title, hwnd))
            return True
    output = []
    win32gui.EnumWindows(ehandler, output)
    return output

if __name__ == '__main__':
    output = getwindowlist()
    print('output', output)

# print("\n".join("{: 9d} {}".format(h, t) for t, h in getWindowList()))
# hwnd = win32gui.FindWindow(None, "계산기")
# print(hwnd)
# win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
# wtext = win32gui.GetWindowText(hwnd)

# print('wtext', wtext)
# print("getclassname", win32gui.GetClassName(hwnd))
# print("getclassname", win32gui.GetClassName('KakaoTalkEdgeWndClass'))