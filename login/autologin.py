import sys
import os
import time
import pythoncom
from manuallogin22 import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from multiprocessing import Process
from PyQt5.QAxContainer import QAxWidget
# sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
openapi_path = 'C:/OpenAPI'
# from utility.setting import openapi_path
app = QtWidgets.QApplication(sys.argv)

class Window(QtWidgets.QMainWindow):
    def __init__(self, gubun):
        super().__init__()
        self.gubun = gubun
        # print('self.gubun', self.gubun)
        self.bool_connected = False
        self.ocx = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')
        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.CommConnect()

    def CommConnect(self):
        print('commconnect')
        self.ocx.dynamicCall('CommConnect()')
        while not self.bool_connected:
            pythoncom.PumpWaitingMessages()
            # print('connected state', self.bool_connected)

    def OnEventConnect(self, err_code):
        print('oneventconnect')
        if err_code == 0:
            self.bool_connected = True
        print('err_code--->', err_code)

        self.AutoLoginOn()

    def AutoLoginOn(self):
        print('\n 자동 로그인 설정 대기 중 ...\n')
        # QTimer.singleShot(5000, lambda: auto_on(1))
        QTimer.singleShot(5000, lambda: auto_on(self.gubun))  # 인자는 첫번째 계정 or 두번째계정 송부
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
    gubun = None
    if num == 1 or num == 2:    # 첫번째계정 모의서버(1), 실서버(2)
        gubun = 1       # 첫번째 계정
    elif num == 3 or num == 4:  # 두번째계정 모의서버(3), 실서버(4)
        gubun = 2       # 두번째 계정

    print('gubun', gubun)

    # 기술적으로 Process를 사용해야 하는 이유는 kiwoom API창이 뜨면 다음이 진행되어야 하기 때문이다. 따라서 join()하면 진행이 안된다.
    p = Process(target=Window, args=(gubun,))       # 여기 gubun은 auto_on(gubun)으로 사용됨.
    p.start()
    print(' 자동 로그인 설정용 프로세스 시작\n')

    while find_window('Open API login') == 0:
        print(' 로그인창 열림 대기 중 ...\n')
        time.sleep(1)

    print(' 아이디 및 패스워드 입력 대기 중 ...\n')
    time.sleep(3)

    manual_login(num)
    # manual_login(1)
    print(' 아이디 및 패스워드 입력 완료\n')
