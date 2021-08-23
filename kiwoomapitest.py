import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
import pythoncom
import datetime
from RealType import *
import pandas as pd
import logging
from multiprocessing import Process, Queue, current_process
app = QApplication(sys.argv)
logging.basicConfig(filename="../log.txt", level=logging.ERROR)
# logging.basicConfig(level=logging.INFO)

class Kiwoom:
    def __init__(self, login=False):
        if not QApplication.instance():
            app = QApplication(sys.argv)
        self.connected = False              # for login event
        self.received = False               # for tr event
        self.tr_remained = False
        self.condition_loaded = False

        self.dict_code_name = {} # 조건검색결과 종목코드리스트의 {종목코드:종목명, 종목코드: 종목명 ,,,,,}

        self.tr_items = None                # tr input/output items
        self.tr_data = None                 # tr output data
        self.tr_record = None

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_tr)
        # self.ocx.OnReceiveRealData.connect(self._handler_real)
        # self.ocx.OnReceiveConditionVer.connect(self._handler_condition_load)
        # self.ocx.OnReceiveTrCondition.connect(self._handler_tr_condition)
        # self.ocx.OnReceiveMsg.connect(self._handler_msg)
        # self.ocx.OnReceiveChejanData.connect(self._handler_chejan)
        self.start()

    def start(self):
        self.ocx.dynamicCall("CommConnect()")
        while not self.connected:
            pythoncom.PumpWaitingMessages()

        accno = self.ocx.dynamicCall("GetLoginInfo(QString)","ACCNO")
        print(accno)

        self.ocx.dynamicCall("SetInputValue(QString,Qstring)", "계좌번호", "8000707411")
        self.ocx.dynamicCall("SetInputValue(QString,Qstring)", "비밀번호", "0000")
        self.ocx.dynamicCall("SetInputValue(QString,Qstring)", "비밀번호입력매체구분", "00")

        data = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "체결잔고요청", "opw00005", 0, "1001")
        print('accinfo', data)

        app.exec_()

    def _handler_login(self, err_code):
        logging.info(f"hander login {err_code}")
        if err_code == 0:
            self.connected = True

    def _handler_tr(self, screen, rqname, trcode, record, next):
        logging.info(f"OnReceiveTrData {screen} {rqname} {trcode} {record} {next}")
        if rqname == '체결잔고요청':
            print('체결잔고요청')



if __name__ == '__main__':
    kiwoom = Kiwoom()


