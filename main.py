import datetime
import sys
import time
from PyQt5 import QtWidgets, QtGui, QAxContainer, uic
from PyQt5.QtCore import Qt
from multiprocessing import Process, Queue, Pool
from worker import Worker
from writer import Writer
from hoga import HogaWindow

# app =QtWidgets.QApplication(sys.argv)
form_class = uic.loadUiType('C:/Users/USER/PycharmProjects/my_window/mywindow.ui')[0]

class MyWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.workerQ = workerQ
        self.seleted_code = None
        self.dict_code_name = {}
        self.dict_name_code = {}

        '''
        나중 여기에 widget종류를 적어놓는다. 
        가능하면 단축키를 이용하여 콤보박스에서 선택하는 방식으로 해본다.
        self.table_gwansim
        self.table_account
        self.table_hoga
        '''
        self.table_gwansim.setColumnWidth(0, 120)
        self.table_gwansim.setColumnWidth(3, 60)
        self.table_gwansim.setColumnWidth(6, 60)
        self.table_account.setColumnWidth(0, 120)
        self.table_acc_eva.setColumnWidth(1, 100)

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

        self.code_index = {}  # 나중 update할때 종목코드가 위치한 row값을 찾기위해서 변수저장

        # todo pyqtSlot 설정
        self.writer = Writer(windowQ)
        self.writer.UpdateTextedit.connect(self.UpdateTextedit)
        self.writer.UpdateGwansim.connect(self.UpdateGwansim)
        self.writer.UpdateJango.connect(self.UpdateJango)
        self.writer.UpdateHoga.connect(self.UpdateHoga)
        self.writer.UpdateChart.connect(self.UpdateChart)
        self.writer.start()

    # 여기서 작업하고 나중에 옮긴다.
    def gwansim_cellClicked(self, row):
        # 관심종목 window에서 click한 종목의 코드를 self.selected_code로 저장
        data = self.table_gwansim.item(row, 0)    # 종목명을 찾아야 하므로 column num 0이다
        if data == None:
            return
        self.seleted_code = self.dict_name_code[data.text()]
        # hoga table 체결수량 column 내용 삭제

        for row in range(22):
            self.table_hoga2.item(row, 1).setText("")

        print('selected_code', self.seleted_code)


        # 작업을 위하여 worker process에 전달 todo
        self.workerQ.put(['VAR','self.selected_code', self.seleted_code])

    def account_cellClicked(self, row):
        # 관심종목 window에서 click한 종목의 코드를 self.selected_code로 저장
        data = self.table_account.item(row, 0)    # 종목명을 찾아야 하므로 column num 0이다
        if data == None:
            return
        # data item의 text()값;종목명을 읽어와서 dict_name_code에서 종목코드를 찾아 self.selected_code에 저장
        self.seleted_code = self.dict_name_code[data.text()]
        print('selected_code', self.seleted_code)

        # 작업을 위하여 worker process에 전달 todo
        self.workerQ.put(['VAR','self.selected_code', self.seleted_code])

    # @QtCore.pyqtSlot(list)
    def UpdateTextedit(self, msg):
        if msg[0] == '수신시간':
            now = datetime.datetime.now()
            self.textEdit.append(f'{str(now)} : {msg[2]}')

        else:
            self.textEdit.append(msg[1])

    def UpdateGwansim(self, data): # data = ('initial', self.dict_code_name, self.dict_name_code)

        if data[0] == 'initial':
            self.dict_code_name = data[1]  # dict, data = ('initial',self.dict_code_name )
            self.dict_name_code = data[2]

            # 1차로 수동으로 지정하기 전에 관심종목중 첫째 항목을 지정종목으로 감시 시작,
            self.seleted_code = list(self.dict_code_name.keys())[0]
            print('선택된주식코드', self.seleted_code)

            # print('UpGwansim:codelist', self.dict_code_name)
            rows = len(self.dict_code_name)
            self.table_gwansim.setRowCount(rows)
            # 관심종목명만 우선 table에 기재(0번 칼럼)
            for row, (code, name) in enumerate(self.dict_code_name.items()):
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

    def UpdateJango(self, data):
        # data

        # print('Up_acc', data[1])
        if data[0] == '계좌잔고':
            if data[1] == '':
                item = QtWidgets.QTableWidgetItem('보유잔고없음')
                self.table_account.setItem(0, 0, item)
            else:
                jango = data[1]  # data[1] = [(name, quan, buy_prc, cur, Y_rate, EG, EA),반복]
                cnt = len(jango) # tuple이 몇개냐??

                for index1 in range(cnt):
                    for index2 in range(7):
                        self.table_account.setItem(index1, index2, QtWidgets.QTableWidgetItem())
                        item = jango[index1][index2]
                        # print('type', type(item))

                        if type(item) == int or type(item) == float:
                            item = format(item,',')
                            self.table_account.item(index1,index2).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))

                        # self.table_account.item(index1,index2).setData(Qt.DisplayRole, item)
                        self.table_account.item(index1,index2).setText(item)
        elif data[0] == '계좌평가결과':
            acc_eva_info = data[1]   # (accno, E_Assets, Y_rate, eva_profit, eva_amount, buy_amount)
            print('acc_eva_info', acc_eva_info)
            item = None
            for index in range(6):  # col == 6
                col = index
                self.table_acc_eva.setItem(0, col, QtWidgets.QTableWidgetItem())
                item = acc_eva_info[index]
                if type(item) == int or type(item) == float:
                    item = format(item, ',')
                    self.table_acc_eva.item(0, col).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.table_acc_eva.item(0, col).setText(item)
    # 호가창 처음 설정
    def UpdateHoga(self, data):

        if data[0] == 'hoga':    # data = ('real', hg_db리스트, hg_sr리스트, hg_ga리스트, per리스트)
            # print('updatehoga', data[1])

            hoga_data = data[1:]
            cnt = len(hoga_data[0])   # 리스트의 크기(대표적으로 hg_db기준) ; 22줄이다.

            for index in range(4):    # hg_db, hg_sr, hg_ga, per 순회
                for index2 in range(cnt):
                    item = hoga_data[index][index2]
                    # item = QtWidgets.QTableWidgetItem(item)
                    row, col = index2, index + 2
                    item = format(item, ",")
                    self.table_hoga2.item(row,col).setData(Qt.DisplayRole, item)

        elif data[0] == 'chaegyeol':    # data = ('chaegyeol', v)

            volume = data[1]
            # todo 아래는 인식되지 않는다. 고쳐라 처음 클릭하면 cell을 다 지워야 한다.
            if self.table_hoga2.item(0,1) == None:    # 0,1 cell이 None이라는 건 맨 처음이라는 뜻.
                print('체결창 처음$$')

                # cell(0,1) 값을 넣고 return
                color = QtGui.QBrush(Qt.red) if volume > 0 else QtGui.QBrush(Qt.blue)
                self.table_hoga2.item(0, 1).setForeground(color)
                self.table_hoga2.item(0, 1).setData(Qt.DisplayRole, volume)
                return

            else:
                volume_copy = self.table_hoga2.item(0,1).text()
                color = QtGui.QBrush(Qt.red) if volume > 0 else QtGui.QBrush(Qt.blue)
                self.table_hoga2.item(0, 1).setForeground(color)
                self.table_hoga2.item(0, 1).setData(Qt.DisplayRole, volume)

            for row in range(1,22):
                if self.table_hoga2.item(row,1).text() == "":   # cell의 설정을 해 둔 상태이므로 text()값만 점검하면 된다.
                    self.table_hoga2.item(row,1).setData(Qt.DisplayRole, volume_copy)
                    return

                volume = self.table_hoga2.item(row,1).text()

                color = QtGui.QBrush(Qt.red) if int(volume_copy) > 0 else QtGui.QBrush(Qt.blue)
                self.table_hoga2.item(row, 1).setForeground(color)
                self.table_hoga2.item(row, 1).setData(Qt.DisplayRole, volume_copy)
                volume_copy = volume

    def UpdateChart(self, data):
        pass

if __name__ == '__main__':

    windowQ, workerQ, hogaQ = Queue(), Queue(), Queue()
    Process(target=Worker, name='name_worker', args=(windowQ, workerQ, hogaQ,), daemon=True).start()
    # Process(target=HogaWindow, args=(windowQ, hogaQ,), daemon=True).start()

    app = QtWidgets.QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()


