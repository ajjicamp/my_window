# -*- coding: utf-8 -*-
from threading import Thread
from multiprocessing import Process, Lock
# from config import configUpdate  # user-defined
# from qpkg import Kiwoom  # user-defined
import time
import sys


def login_input(user_id, norm_pwd, cert_pwd, is_simulated=False):
    import pywinauto
    # sys.coinit_flags=0
    while True:
        procs = pywinauto.findwindows.find_elements()
        for proc in procs:
            if proc.name == 'Open API Login':
                break
        if proc.name == 'Open API Login':
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
    app = Kiwoom.QApplication(sys.argv)
    kiwoom = Kiwoom.Kiwoom()

    if idx % 2 == 0:  # check mock invest server mode
        is_simulated = True
    else:
        is_simulated = False
    lock.acquire()  # process lock
    login_th = Thread(target=login_input,
                      kwargs={'user_id': configUpdate.KIWOOM[idx // 2]['USER_ID'],
                              'norm_pwd': configUpdate.KIWOOM[idx // 2]['NORM_PWD'],
                              'cert_pwd': configUpdate.KIWOOM[idx // 2]['CERT_PWD'],
                              'is_simulated': is_simulated})
    login_th.start()
    kiwoom.comm_connect()
    lock.release()  # process unlock

    print('process[{0}]'.format(idx))
    print('Login state : {0}'.format(kiwoom.get_connect_state()))
    print('Server : {0}'.format(kiwoom.get_login_info("GetServerGubun")))
    # app.exec_() # not to terminate process


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
