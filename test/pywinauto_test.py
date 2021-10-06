# -*- coding: utf-8 -*-
from threading import Thread
from multiprocessing import Process, Lock
# from config import configUpdate  # user-defined
# from qpkg import Kiwoom  # user-defined
from PyQt5.QAxContainer import QAxWidget
from PyQt5 import QtWidgets
import time
import sys
import pythoncom

def login_input(user_id, norm_pwd, cert_pwd, is_simulated=False):
    # print("login_input")
    import pywinauto
    # sys.coinit_flags=0
    while True:
        procs = pywinauto.findwindows.find_elements()
        for proc in procs:
            if proc.name == 'Open API Login':
                break
        if proc.name == 'Open API Login':
            print('proc.name 감지되었음.')
            break

    login_app = pywinauto.Application().connect(process=proc.process_id)
    login_dig = login_app.OpenAPILogin
    login_dig.Edit1.send_keystrokes(user_id)
    login_dig.Edit2.send_keystrokes(norm_pwd)
    if is_simulated:
        if login_dig.Edit3.is_enabled():
            login_dig.Button5.click()  # check mock invest server mode
        login_dig.Edit2.send_keystrokes('{ENTER}')  # login
    else:
        if not login_dig.Edit3.is_enabled():
            login_dig.Button5.click()  # uncheck mock invest server mode
        login_dig.Edit3.send_keystrokes(cert_pwd)
        login_dig.Edit3.send_keystrokes('{ENTER}')  # login


def multi(idx, lock):
    # app = Kiwoom.QApplication(sys.argv)
    app = QtWidgets.QApplication(sys.argv)
    kiwoom = Kiwoom()

    if idx % 2 == 0:  # check mock invest server mode
        is_simulated = True
    else:
        is_simulated = False
    lock.acquire()  # process lock
    with open('/my_window/login/user.txt') as f:
        lines = f.readlines()
        USER_ID1 = lines[0].strip()
        USER_PW1 = lines[1].strip()
        USER_CR1 = lines[2].strip()
        USER_CP1 = lines[3].strip()

    login_th = Thread(target=login_input,
                      kwargs={'user_id': USER_ID1,
                              'norm_pwd': USER_PW1,
                              'cert_pwd': USER_CR1,
                              'is_simulated': is_simulated})


    login_th.start()
    kiwoom.CommConnect()
    lock.release()  # process unlock

    print('process[{0}]'.format(idx))
    print('Login state : {0}'.format(kiwoom.GetConnectState()))
    print('Server : {0}'.format(kiwoom.GetLoginInfo("GetServerGubun")))
    print('Server : {0}'.format(kiwoom.GetLoginInfo("USER_ID")))
    # print('Server : {0}'.format(kiwoom.GetLoginInfo()))
    # app.exec_() # not to terminate process

class Kiwoom:
    # app = QtWidgets.QApplication(sys.argv)
    def __init__(self):
        self.bool_connected = False
        self.ocx = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')
        self.ocx.OnEventConnect.connect(self.OnEventConnect)

    def CommConnect(self):
        self.ocx.dynamicCall('CommConnect()')
        while not self.bool_connected:
            pythoncom.PumpWaitingMessages()

    def OnEventConnect(self, err_code):
        if err_code == 0:
            self.bool_connected = True
        print('err_code--->', err_code)

    def GetConnectState(self):
        """
        현재접속 상태를 반환하는 메서드
        :return: 0:미연결, 1: 연결완료
        """
        ret = self.ocx.dynamicCall("GetConnectState()")
        return ret

    def GetLoginInfo(self, tag):
        """
        로그인한 사용자 정보를 반환하는 메서드
        :param tag: ("ACCOUNT_CNT, "ACCNO", "USER_ID", "USER_NAME", "KEY_BSECGB", "FIREW_SECGB")
        :return: tag에 대한 데이터 값
        """
        data = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)

        if tag == "ACCNO":
            return data.split(';')[:-1]
        else:
            return data


if __name__ == '__main__':
    procs = []
    lock = Lock()
    start_time = time.time()
    for idx in range(2):
        proc = Process(target=multi, args=(idx, lock))
        procs.append(proc)
        proc.start()
    for proc in procs:
        proc.join()
    end_time = time.time()
    print('time : {0}'.format(end_time - start_time))
