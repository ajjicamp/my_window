# windowQ를 get()하여 pyqtsignal을 통해 Window.py로 보낸다. Window.py의 signal슬롯에서 작업수행
# QThread이다. pyqtsignal을 처리하기 위하여 QThread를 이용하였다.
import sys
import time
import pandas as pd
from PyQt5 import QtCore
import datetime
class Writer(QtCore.QThread):
    data0 = QtCore.pyqtSignal(tuple)  # 실시간 수신로그 및
    data1 = QtCore.pyqtSignal(pd.DataFrame)
    data2 = QtCore.pyqtSignal(pd.DataFrame)

    def __init__(self, windowQ):
        super().__init__()
        self.windowQ = windowQ
        self.int_elst = 0.000001

    def run(self):
        while True:
            if not self.windowQ.empty():
                data = self.windowQ.get()
                self.data0.emit(data)    # tuple[0] ; 수신시간, 관심종목코드 tuple[1] : value
                print('write_data', data)