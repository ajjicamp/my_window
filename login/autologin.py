import time
import pythoncom
# from manuallogin import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from multiprocessing import Process
from PyQt5.QAxContainer import QAxWidget
# sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
openapi_path = 'C:/OpenAPI'
# from utility.setting import openapi_path
app = QtWidgets.QApplication(sys.argv)


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.bool_connected = False
        self.ocx = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')
        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.CommConnect()

    def CommConnect(self):
        self.ocx.dynamicCall('CommConnect()')
        while not self.bool_connected:
            pythoncom.PumpWaitingMessages()

    def OnEventConnect(self, err_code):
        if err_code == 0:
            self.bool_connected = True
        self.AutoLoginOn()

    def AutoLoginOn(self):
        print('\n 자동 로그인 설정 대기 중 ...\n')
        QTimer.singleShot(5000, lambda: self.auto_on(1))
        self.ocx.dynamicCall('KOA_Functions(QString, QString)', 'ShowAccountWindow', '')
        print(' 자동 로그인 설정 완료\n')
        print(' 자동 로그인 설정용 프로세스 종료 중 ...')

    def auto_on(self, gubun):
        """
        gubun == 1 : 첫번째 계정
        gubun == 2 : 두번째 계정
        """
        hwndd = find_window('계좌비밀번호')
        if hwndd != 0:
            edit = win32gui.GetDlgItem(hwndd, 0xCC)
            if gubun == 1:
                win32gui.SendMessage(edit, win32con.WM_SETTEXT, 0, USER_CP1)
            elif gubun == 2:
                win32gui.SendMessage(edit, win32con.WM_SETTEXT, 0, USER_CP2)
            click_button(win32gui.GetDlgItem(hwndd, 0xD4))
            click_button(win32gui.GetDlgItem(hwndd, 0xD3))
            click_button(win32gui.GetDlgItem(hwndd, 0x01))


if __name__ == '__main__':
    login_info = f'{openapi_path}/system/Autologin.dat'
    if os.path.isfile(login_info):
        os.remove(f'{openapi_path}/system/Autologin.dat')
    print('\n 자동 로그인 설정 파일 삭제 완료\n')

    Process(target=Window).start()
    print(' 자동 로그인 설정용 프로세스 시작\n')

    while find_window('Open API login') == 0:
        print(' 로그인창 열림 대기 중 ...\n')
        time.sleep(1)

    print(' 아이디 및 패스워드 입력 대기 중 ...\n')
    time.sleep(5)

    manual_login(2)
    print(' 아이디 및 패스워드 입력 완료\n')
