# windowQ를 get()하여 pyqtsignal을 통해 Window.py로 보낸다. Window.py의 signal슬롯에서 작업수행
# QThread이다. pyqtsignal을 처리하기 위하여 QThread를 이용하였다.
import sys
import time
import pandas as pd
from PyQt5 import QtCore
import datetime
class Writer(QtCore.QThread):
    UpdateTextedit= QtCore.pyqtSignal(tuple)  # 실시간 수신로그 및
    UpdateGwansim = QtCore.pyqtSignal(tuple)
    UpdateJango = QtCore.pyqtSignal(tuple)
    UpdateHoga    = QtCore.pyqtSignal(tuple)
    UpdateChart   = QtCore.pyqtSignal(tuple)

    def __init__(self, windowQ):
        super().__init__()
        self.windowQ = windowQ
        self.int_elst = 0.000001

    def run(self):
        while True:
            if not self.windowQ.empty():
                data = self.windowQ.get()
                if data[0] == 'LOG':
                    self.UpdateTextedit.emit(data[1])
                elif data[0] == 'GSJM':   # 관심종목
                    self.UpdateGwansim.emit(data[1])
                elif data[0] == 'ACC':   # 계좌잔고/평가
                    self.UpdateJango.emit(data[1])
                elif data[0] == 'HOGA':   # 호가
                    self.UpdateHoga.emit(data[1])
                elif data[0] == 'Chart':   # 관심종목
                    self.UpdateChart.emit(data[1])
