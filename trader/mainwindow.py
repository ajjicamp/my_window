import os
import sys
import datetime
import time
from PyQt5 import QtWidgets, QtGui, QAxContainer, uic
from PyQt5.QtCore import Qt
from multiprocessing import Process, Queue, Pool, Value, Array, Manager
from worker import Worker
from writer import Writer
# from hoga import HogaWindow
# from Utility import *

SYSTEM_PATH = "C:/Users/USER/PycharmProjects/my_window"
# app =QtWidgets.QApplication(sys.argv)
form_class = uic.loadUiType('C:/Users/USER/PycharmProjects/my_window/trader/mywindow.ui')[0]


class MyWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.workerQ = workerQ
        # self.seleted_code = None
        # self.dict_code_name = {}
        # self.dict_name_code = {}
        '''
        나중 여기에 widget종류를 적어놓는다. 
        가능하면 단축키를 이용하여 콤보박스에서 선택하는 방식으로 해본다.
        self.table_gwansim
        self.table_account
        self.table_hoga
        '''
        self.table_gwansim.setColumnWidth(0, 120)
        self.table_gwansim.setColumnWidth(3, 70)
        self.table_gwansim.setColumnWidth(6, 70)
        self.table_account.setColumnWidth(0, 120)
        self.table_acc_eva.setColumnWidth(1, 100)
        self.table_hoga1.setColumnWidth(0, 120)

        # hoga2 table의 0,6 column의 색상을 gray로 설정, 1번 column의 alignment 정의
        for row in range(22):
            self.table_hoga2.setItem(row, 0, QtWidgets.QTableWidgetItem())
            # self.table_hoga2.item(row, 0).setBackground(QtGui.QBrush(Qt.gray))
            self.table_hoga2.item(row, 0).setBackground(QtGui.QColor(100, 100, 100, 50))

            self.table_hoga2.setItem(row, 6, QtWidgets.QTableWidgetItem())
            self.table_hoga2.item(row, 6).setBackground(QtGui.QColor(100, 100, 100, 50))

            self.table_hoga2.setItem(row, 1, QtWidgets.QTableWidgetItem())
            self.table_hoga2.item(row, 1).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))

        # hoga2 table의 매도호가를 옅은 붉은색으로 매수호가를 옅은 푸른색으로 설정
        for index in range(4):    # hg_db, hg_sr, hg_ga, per 순회
            for index2 in range(11):
                row, col = index2, index + 2
                self.table_hoga2.setItem(row, col, QtWidgets.QTableWidgetItem())
                self.table_hoga2.item(row,col).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.table_hoga2.item(row,col).setBackground(QtGui.QColor(0, 0, 100, (index2+1) * 7))

            for index2 in range(11, 22):
                row, col = index2, index + 2
                self.table_hoga2.setItem(row, col, QtWidgets.QTableWidgetItem())
                self.table_hoga2.item(row,col).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.table_hoga2.item(row,col).setBackground(QtGui.QColor(100, 0, 0, (22 - index2) * 7))

        # 이벤트 설정
        self.table_gwansim.cellClicked.connect(self.gwansim_cellClicked)
        self.table_account.cellClicked.connect(self.account_cellClicked)
        self.gwansimNaccount.tabBarClicked.connect(self.gwansimNaccount_tabBarClicked)

        self.code_index = {}  # 나중 update할때 종목코드가 위치한 row값을 찾기위해서 변수저장

        # todo pyqtSlot 설정
        self.writer = Writer(windowQ)
        self.writer.UpdateTextedit.connect(self.UpdateTextedit)
        self.writer.UpdateGwansim.connect(self.UpdateGwansim)
        self.writer.UpdateAccJango.connect(self.UpdateAccJango)
        self.writer.UpdateAccEvaluation.connect(self.UpdateAccEvaluation)
        self.writer.UpdateChart.connect(self.UpdateChart)
        self.writer.start()

    def gwansimNaccount_tabBarClicked(self):
        print(f'{self.gwansimNaccount.currentIndex()}가 clicked되었습니다.')
        self.workerQ.put("GetAccountJango")
        self.workerQ.put("GetAccountEvaluation")

    # 종목클릭시  종목코드 탐색, 윈도우 초기화 및 호가창(1)에 종목명을 입력
    def jongmok_clicked_exec(self, jongmok_name):  # 클릭한 종목의 이름이 넘어온다.
        if jongmok_name == None: return
        N_.code = D_GSJM_code[jongmok_name.text()]  # 클릭한 종목명으로 종목코드를 찾아서 변수에 저장

        # 호가창 하단부 초기화
        for row in range(22):
            for col in range(7):
                self.table_hoga2.item(row, col).setText("")

        # hoga1 window 호가종목 name 입력
        self.table_hoga1.setItem(0, 0, QtWidgets.QTableWidgetItem())
        self.table_hoga1.item(0, 0).setText(jongmok_name.text())

        self.workerQ.put('GetAccountJango')   # 보유주식잔고 tr조회
        print('laccjango103', L_ACC_jango)
        jango_list = [i[0] for i in L_ACC_jango]    # 보유잔고의 종목코드만으로 구성된 리스트

        if N_.code in jango_list:          # 보유잔고 중 지정종목이 있으면
            index_num = jango_list.index(N_.code)    # 몇번째에 있는지 확인
            print("잔고리스트 안에 지정종목이 있습니다.")

            for index in range(2, 8):
                col = index - 1
                self.table_hoga1.setItem(0, col, QtWidgets.QTableWidgetItem())
                item = L_ACC_jango[index_num][index]

                if type(item) == int or type(item) == float:
                    item = format(item, ',')
                    self.table_hoga1.item(0, col).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))

                self.table_hoga1.item(0, col).setData(Qt.DisplayRole, item)
                # print('type', type(item))
        else:
            print('잔고리스트 안에 지정종목이 없습니다.')

    def gwansim_cellClicked(self, row):  # 호가창에서 감시할 종목 선정
        jongmok_name = self.table_gwansim.item(row, 0)    # row; clicked row, col ; 0 (종목명, 현재가, 대비, ....)
        self.jongmok_clicked_exec(jongmok_name)

    def account_cellClicked(self, row):
        jongmok_name = self.table_account.item(row, 0)    # 종목명을 찾아야 하므로 column num 0이다
        self.jongmok_clicked_exec(jongmok_name)

    # @QtCore.pyqtSlot(list)
    def UpdateTextedit(self, msg):
        if msg[0] == '수신시간':
            now = datetime.datetime.now()
            self.textEdit.append(f'{str(now)} : {msg[2]}')

        else:
            self.textEdit.append(msg[1])
    
    # 관심종목창 업데이트
    def UpdateGwansim(self, data): # data = ('initial', "", "")

        if data[0] == 'initial':
            # 1차로 수동으로 지정하기 전에 관심종목중 첫째 항목을 지정종목으로 감시 시작
            print('선택된주식코드', N_.code)

            rows = len(D_GSJM_name)
            self.table_gwansim.setRowCount(rows)

            # 관심종목명만 우선 table에 기재(0번 칼럼)
            for row, (code, name) in enumerate(D_GSJM_name.items()):
                # todo 아래 코드도 일관되게 고쳐야 한다.
                item = QtWidgets.QTableWidgetItem(name)
                self.table_gwansim.setItem(row, 0, item)
                # 관심종목의 코드별로 해당 row값을 저장
                self.code_index[code] = row

        elif data[0] == 'real':     # data = ('real', code, name, c, db, per, cv, cva, ch)
            code = data[1]
            code_info = data[2:] # (name, c, db, per, cv, cva, ch)

            row = self.code_index[code]  # code_index dict에서 row값 검색 {code:row, code:row ...}
            for col in range(7):  # table_gwansim columns 수
                self.table_gwansim.setItem(row, col, QtWidgets.QTableWidgetItem())
                item = code_info[col]
                if type(item) == int or type(item) == float:
                    item = format(item, ',')
                    self.table_gwansim.item(row, col).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.table_gwansim.item(row, col).setData(Qt.DisplayRole, item)

    # 계좌잔고창, 계좌평가창 업데이트
    def UpdateAccJango(self):
        print("updatejango 작업시작")
        jango = L_ACC_jango
        if jango == []:
            self.table_account.setItem(0, 0, QtWidgets.QTableWidgetItem())
            item = "잔고없음"
            self.table_account.item(0, 0).setData(Qt.DisplayRole, item)
            return

        cnt = len(jango)  # tuple이 몇개냐??
        print('cnt', cnt)
        for index1 in range(cnt):  # data[1]의 tuple index겸 row값 설정
            row = index1
            for index2 in range(1, 8):  # jango index값 설정 ; 2번째 name부터 마지막까지
                col = index2 - 1
                self.table_account.setItem(row, col, QtWidgets.QTableWidgetItem())
                item = jango[index1][index2]

                # print('item', item)
                if type(item) == int or type(item) == float:
                    item = format(item, ',')
                    self.table_account.item(row, col).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                print('nonetype object', row, col, self.table_account.item)
                self.table_account.item(row, col).setData(Qt.DisplayRole, item)
                # self.table_account.item(row, col).setText(item)

    def UpdateAccEvaluation(self, data):
        # print('acc evaluation', data)
        acc_eva_info = data
        for index in range(6):  # col == 6
            col = index
            self.table_acc_eva.setItem(0, col, QtWidgets.QTableWidgetItem())
            item = acc_eva_info[index]
            if type(item) == int or type(item) == float:
                item = format(item, ',')
                self.table_acc_eva.item(0, col).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
            self.table_acc_eva.item(0, col).setText(item)

    # 호가창 업데이트: 실시간 호가데이터, 체결데이터를 받아서 update
    def UpdateHoga(self, data):

        if data[0] == 'hoga':    # data = ('real', hg_db리스트, hg_sr리스트, hg_ga리스트, per리스트)
            # print('updatehoga', data[1])

            hoga_data = data[1:]
            cnt = len(hoga_data[0])   # 리스트의 크기(대표적으로 hg_db기준) ; 22줄이다.

            for index in range(4):    # hg_db, hg_sr, hg_ga, per 순회
                for index2 in range(cnt):
                    # 시작부분에서 호가창 cell 전체에 미리 setItem() 정의
                    item = hoga_data[index][index2]
                    row, col = index2, index + 2
                    item = format(item, ",")
                    self.table_hoga2.item(row, col).setData(Qt.DisplayRole, item)

        elif data[0] == 'chaegyeol':    # data = ('chaegyeol', v)

            volume = data[1]
            def update(volume, row):
                # print(type(volume), volume)
                # if not volume == '':
                color = QtGui.QBrush(Qt.red) if int(volume) > 0 else QtGui.QBrush(Qt.blue)
                self.table_hoga2.item(row, 1).setForeground(color)
                self.table_hoga2.item(row, 1).setData(Qt.DisplayRole, volume)

            for row in range(22):
                # if self.table_hoga2.item(row,1) == '':
                # print('row값:' ,self.table_hoga2.item(row,1).text())
                if self.table_hoga2.item(row,1).text() == "":
                    print("값이 ''입니다.")
                    update(volume, row)
                    return
                else:
                    temp = self.table_hoga2.item(row,1).text()
                    print(type(volume), volume)
                    if volume == '':
                        print('volume값은 없음입니다.')
                    update(volume, row) # initial ; 위 첫줄 volume값 다음부터는 아랫줄 volome
                    volume = temp

    def UpdateChart(self, data):
        pass

if __name__ == '__main__':

    windowQ, workerQ, hogaQ = Queue(), Queue(), Queue()
    # with Manager() as manager:
    N_ = Manager().Namespace()           # 공유변수 관심종목 code = N_.code
    L_ACC_jango = Manager().list()       # 계좌보유잔고 종목코드 리스트
    D_GSJM_name = Manager().dict()       # 공유변수 관심종목 {code: name}
    D_GSJM_code = Manager().dict()       # 공유변수 관심종목 {name: code}

    # kiwoom 버전처리
    os.system(f"python {SYSTEM_PATH}/login/versionupdater.py")
    os.system(f"python {SYSTEM_PATH}/login/autologin02.py")

    p = Process(target=Worker, name='name_worker', args=(N_, L_ACC_jango, D_GSJM_name, D_GSJM_code,
                                                         windowQ, workerQ, hogaQ,), daemon=True)
    p.start()

    app = QtWidgets.QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()


