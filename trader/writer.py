# windowQ를 get()하여 pyqtsignal을 통해 Window.py로 보낸다. Window.py의 signal슬롯에서 작업수행
# QThread이다. pyqtsignal을 처리하기 위하여 QThread를 이용하였다.

import sys
import time
import pandas as pd
from PyQt5 import QtCore
import datetime

class Writer(QtCore.QThread):
    UpdateTextedit= QtCore.pyqtSignal(tuple)    # 실시간 수신로그
    UpdateGwansim = QtCore.pyqtSignal(tuple)    # 관심종목 real update
    UpdateAccJango = QtCore.pyqtSignal(str)      # 계좌잔고 tr update
    UpdateAccEvaluation = QtCore.pyqtSignal(tuple)      # 계좌평가 tr update
    UpdateHoga    = QtCore.pyqtSignal(tuple)    # 호가창 real update
    UpdateChart   = QtCore.pyqtSignal(tuple)    # 차트 real update

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
                elif data[0] == 'AccJango':   # 계좌잔고
                    self.UpdateAccJango.emit(data[0])
                elif data[0] == 'AccEvaluation':   # 계좌평가
                    self.UpdateAccEvaluation.emit(data[1])
                elif data[0] == 'HOGA':   # 호가
                    self.UpdateHoga.emit(data[1])
                elif data[0] == 'Chart':   # 관심종목
                    self.UpdateChart.emit(data[1])
