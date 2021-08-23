# 호가창을 업데이트하는 모듈
# 여기서는 selected_stock에 대한 hoga_window 출력과 매수매도주문처리를 위한 사전 작업, 그리고 계좌잔고의 관리를 담당한다.
# 실시간 데이터(체결틱, 호가데이터)를 받는다.

import datetime
import sys
import time
from PyQt5 import QtWidgets, QAxContainer, uic
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt

# 한글폰트 깨짐방지
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False #한글 폰트 사용시 마이너스 폰트 깨짐 해결

hoga_window = uic.loadUiType('C:/Users/USER/PycharmProjects/my_window/hoga_window.ui')[0]

class HogaWindow(QtWidgets.QWidget, hoga_window):
    def __init__(self, windowQ, hogaQ):
        super().__init__()
        print(self)
        self.windowQ = windowQ
        self.hogaQ = hogaQ
        self.setupUi(self)
        self.show()

        self.start()

    def start(self):
        while True:
            if not self.hogaQ.empty():
                hoga = self.hogaQ.get()
                self.hoga_draw(hoga)

    def hoga_draw(self, hoga):
        for i in range(20):
            row = i + 1
            for i in range(4):
                col = i + 1
                print('좌표:', row,col)
                # 직전대비
                item_db = format(hoga[2][row], ",")
                item_db = QtWidgets.QTableWidgetItem(str(item_db))
                item_db.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.tableWidget.setItem(row,col, item_db)

                # 수량
                item_sr = format(hoga[3][row], ",")
                item_sr = QtWidgets.QTableWidgetItem(str(item_sr))
                item_sr.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.tableWidget.setItem(row,col, item_sr)

                # 금액
                item_ga = format(hoga[4][row], ",")
                print(item_ga)
                item_ga = QtWidgets.QTableWidgetItem(str(item_ga))
                item_ga.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.tableWidget.setItem(row,col, item_ga)


            # 현재가 미수신상태 ==>수신한 후 코드 복원
            # item_4 = format(int(data['현재가'].loc[xpos-i]), ',')
            # item_4 = QTableWidgetItem(str(item_4))
            # item_4.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
            # self.tableWidget.setItem(row,1,item_4)
        # self.move(20, 10)
    '''
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        # elif e.key() == Qt.Key_F:
        #     self.showFullScreen()
        # elif e.key() == Qt.Key_N:
        #     self.showNormal()

        elif e.key() == Qt.Key_Left :       # Left라고 입력하니 안되던데, .프롬프터 창에서 key를 선택하고 - 입력후 또 창에서 선택하니 되더라.
            # self.close()
            mywindow.x_pos_nw -=1
            # self.new_window = NewWindow(mywindow.x_pos_nw, mywindow.code_data)
            # self.new_window.show()
            self.hoga_draw(mywindow.x_pos_nw, mywindow.code_data)

        elif e.key() == Qt.Key_Right :
            # self.close()
            mywindow.x_pos_nw +=1
            # self.new_window = NewWindow(mywindow.x_pos_nw, mywindow.code_data)
            # self.new_window.show()
            self.hoga_draw(mywindow.x_pos_nw, mywindow.code_data)
        '''


