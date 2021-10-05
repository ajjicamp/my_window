import sys
import os
import time
import pythoncom
from manuallogin import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from multiprocessing import Process
from PyQt5.QAxContainer import QAxWidget
# sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
openapi_path = 'C:/OpenAPI'
# from utility.setting import openapi_path
app = QtWidgets.QApplication(sys.argv)

class Window(QtWidgets.QMainWindow):
    def __init__(self, num):
        super().__init__()
        self.num = num
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
        print('err_code--->', err_code)

        self.AutoLoginOn()

    def AutoLoginOn(self):
        print('\n 자동 로그인 설정 대기 중 ...\n')
        # QTimer.singleShot(5000, lambda: auto_on(1))
        QTimer.singleShot(5000, lambda: auto_on(self.num))
        self.ocx.dynamicCall('KOA_Functions(QString, QString)', 'ShowAccountWindow', '')
        print(' 자동 로그인 설정 완료\n')
        print(' 자동 로그인 설정용 프로세스 종료 중 ...')


if __name__ == '__main__':
    for x, par in enumerate(sys.argv):
        print('param', x, par)
    num = int(sys.argv[1])
    # num = 3
    print(type(num), num)
    login_info = f'{openapi_path}/system/Autologin.dat'
    print('login_info', login_info)
    if os.path.isfile(login_info):
        os.remove(f'{openapi_path}/system/Autologin.dat')
    print('\n 자동 로그인 설정 파일 삭제 완료\n')
    if num == 1 or num == 2:
        gubun = 1
    elif num == 3 or num == 4:
        gubun = 2
    p = Process(target=Window, args=(gubun,))
    p.start()
    # p.join()
    print(' 자동 로그인 설정용 프로세스 시작\n')

    while find_window('Open API login') == 0:
        print(' 로그인창 열림 대기 중 ...\n')
        time.sleep(1)

    print(' 아이디 및 패스워드 입력 대기 중 ...\n')
    time.sleep(5)

    manual_login(num)
    # manual_login(1)
    print(' 아이디 및 패스워드 입력 완료\n')
