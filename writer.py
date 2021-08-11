# windowQ를 get()하여 pyqtsignal을 통해 Window.py로 보낸다. Window.py의 signal슬롯에서 작업수행
# QThread이다. pyqtsignal을 처리하기 위하여 QThread를 이용하였다.
import sys
import time
import pandas as pd
from PyQt5 import QtCore
import datetime
class Writer(QtCore.QThread):
    data0 = QtCore.pyqtSignal(list)
    data1 = QtCore.pyqtSignal(pd.DataFrame)
    data2 = QtCore.pyqtSignal(pd.DataFrame)

    def __init__(self, windowQ):
        super().__init__()
        self.windowQ = windowQ
        self.int_elst = 0.000001

    def run(self):
        while True:
            if not self.windowQ.empty():
                time.sleep(self.int_elst)
                data = self.windowQ.get()
                if data[0] == '호가갱신':
                    self.data0.emit([datetime.datetime.now(), data[1]])
                print('windowQ size: ', self.windowQ.qsize() )
                # if type(data) == str:
                #     if '이벤트루프 슬립시간' in data:
                #         self.int_elst = float(data.split(" ")[-1])
                # elif type(data) == list:
                #     self.data0.emit(data)
                #     if data[0] == 1 and data[1] == '시스템 종료':
                #         sys.exit()
                # elif type(data) == pd.DataFrame:
                #     if '현재가' in data.columns[0]:
                #         self.data1.emit(data)
                #     else:
                #         self.data2.emit(data)
