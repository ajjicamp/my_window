import os
import sys
import time
import win32api
import win32con
import win32gui
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))    # 상위폴더참조
system_path = 'C:/Users/USER/PycharmProjects/my_window'
# from utility.setting import system_path

# f = open(f'{system_path}/login/user.txt')

f = open('C:/Users/USER/PycharmProjects/my_window/login/user.txt')
lines = f.readlines()
USER_ID1 = lines[0].strip()
USER_PW1 = lines[1].strip()
USER_CR1 = lines[2].strip()
USER_CP1 = lines[3].strip()
USER_ID2 = lines[4].strip()
USER_PW2 = lines[5].strip()
USER_CR2 = lines[6].strip()
USER_CP2 = lines[7].strip()
f.close()


def window_enumeration_handler(hwndd, top_windows):
    top_windows.append((hwndd, win32gui.GetWindowText(hwndd)))


def enum_windows():
    windows = []
    win32gui.EnumWindows(window_enumeration_handler, windows)
    return windows


def find_window(caption):
    hwndd = win32gui.FindWindow(None, caption)
    if hwndd == 0:
        windows = enum_windows()
        for handle, title in windows:
            if caption in title:
                hwndd = handle
                break
    return hwndd

def click_button(btn_hwnd):
    win32api.PostMessage(btn_hwnd, win32con.WM_LBUTTONDOWN, 0, 0)
    win32api.Sleep(100)
    win32api.PostMessage(btn_hwnd, win32con.WM_LBUTTONUP, 0, 0)
    win32api.Sleep(300)

def enter_keys(hwndd, data):
    # todo 버전처리할 일이 없을때라서 sleep없이 처리되는 지 모른다. 버전처리할 때도 되는지 확인필요
    win32api.SendMessage(hwndd, win32con.EM_SETSEL, 0, -1)
    win32api.SendMessage(hwndd, win32con.EM_REPLACESEL, 0, data)
    win32api.Sleep(300)
    win32api.PostMessage(hwndd, win32con.WM_LBUTTONDOWN, 0, 0)

def manual_login(gubun):
    """
    gubun == 1 : 첫번째 계정 모의서버
    gubun == 2 : 첫번째 계정 본서버
    gubun == 3 : 두번째 계정 모의서버
    gubun == 4 : 두번째 계정 본서버
    """

    hwndd = find_window('Open API login')
    if gubun in [1, 3]:
        # 모의서버체크란에 클릭하기
        if win32gui.IsWindowEnabled(win32gui.GetDlgItem(hwndd, 0x3EA)):
            click_button(win32gui.GetDlgItem(hwndd, 0x3ED))
    elif gubun in [2, 4]:
        print("본서버에 연결작업 진행중")
        if not win32gui.IsWindowEnabled(win32gui.GetDlgItem(hwndd, 0x3EA)):
            click_button(win32gui.GetDlgItem(hwndd, 0x3ED))

    if gubun in [1, 2]:
        enter_keys(win32gui.GetDlgItem(hwndd, 0x3E8), USER_ID1)
        enter_keys(win32gui.GetDlgItem(hwndd, 0x3E9), USER_PW1)

        if gubun == 2:
            enter_keys(win32gui.GetDlgItem(hwndd, 0x3EA), USER_CR1)
            click_button(win32gui.GetDlgItem(hwndd, 0x1))

    elif gubun in [3, 4]:
        enter_keys(win32gui.GetDlgItem(hwndd, 0x3E8), USER_ID2)
        enter_keys(win32gui.GetDlgItem(hwndd, 0x3E9), USER_PW2)

        if gubun == 4:
            enter_keys(win32gui.GetDlgItem(hwndd, 0x3EA), USER_CR2)
            click_button(win32gui.GetDlgItem(hwndd, 0x1))
    click_button(win32gui.GetDlgItem(hwndd, 0x1))

def auto_on(gubun):
    print("hwndd 찾기 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    """
    gubun == 1 : 첫번째 계정
    gubun == 2 : 두번째 계정
    """
    hwndd = find_window('계좌비밀번호')
    print('hwndd', hwndd)
    if hwndd != 0:
        edit = win32gui.GetDlgItem(hwndd, 0xCC)
        print('edit', edit)
        if gubun == 1:
            win32gui.SendMessage(edit, win32con.WM_SETTEXT, 0, USER_CP1)    # 계정1 계좌비밀번호
        elif gubun == 2:
            win32gui.SendMessage(edit, win32con.WM_SETTEXT, 0, USER_CP2)    # 계정2 계좌비밀번호
        click_button(win32gui.GetDlgItem(hwndd, 0xD4))
        click_button(win32gui.GetDlgItem(hwndd, 0xD3))
        click_button(win32gui.GetDlgItem(hwndd, 0x01))

       #######


def auto_on(gubun):
    """
    gubun == 1 : 첫번째 계정
    gubun == 2 : 두번째 계정
    """
    hwnd = find_window('계좌비밀번호')
    if hwnd != 0:
        edit = win32gui.GetDlgItem(hwnd, 0xCC)
        if gubun == 1:
            win32gui.SendMessage(edit, win32con.WM_SETTEXT, 0, USER_CP1)
        elif gubun == 2:
            win32gui.SendMessage(edit, win32con.WM_SETTEXT, 0, USER_CP2)
        click_button(win32gui.GetDlgItem(hwnd, 0xD4))
        click_button(win32gui.GetDlgItem(hwnd, 0xD3))
        click_button(win32gui.GetDlgItem(hwnd, 0x01))
