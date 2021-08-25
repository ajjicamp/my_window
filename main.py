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
        '''
        나중 여기에 widget종류를 적어놓는다. 
        가능하면 단축키를 이용하여 콤보박스에서 선택하는 방식으로 해본다.
        self.table_gwansim
        self.table_account
        self.table_hoga
        '''
        self.table_gwansim.setColumnWidth(0, 120)
        self.table_account.setColumnWidth(0, 120)
        # 이벤트 설정
        self.table_gwansim.cellClicked.connect(self.gwansim_cellClicked)

        self.seleted_code = None
        self.code_index = {}  # 나중 update할때 종목코드가 위치한 row값을 찾기위해서 변수저장

        # print('self: ', self)
        # print('form_class', form_class)
        # self.show()

        # todo pyqtSlot 설정
        self.writer = Writer(windowQ)
        self.writer.UpdateTextedit.connect(self.UpdateTextedit)
        self.writer.UpdateGwansim.connect(self.UpdateGwansim)
        self.writer.UpdateJango.connect(self.UpdateJango)
        self.writer.UpdateHoga.connect(self.UpdateHoga)
        self.writer.UpdateChart.connect(self.UpdateChart)
        self.writer.start()

        # app.exec_()

    # 여기서 작업하고 나중에 옮긴다.
    def gwansim_cellClicked(self, row):
        # 관심종목 window에서 click한 종목의 코드를 self.selected_code로 저장
        data = self.table_gwansim.item(row, 0)    # 종목명을 찾아야 하므로 column num 0이다
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

    def UpdateGwansim(self, data): # 여기서 data는 관심종목 table에 add하기 위한 collection(듀플,리스트,dataframe 등)이다
        if data[0] == 'initial':

            self.dict_code_name = data[1]  # dict, data = ('initial',self.dict_code_name )
            self.dict_name_code = { v:k for k, v in self.dict_code_name.items() }
            # print('self.dict_name_code', self.dict_name_code)

            # todo 추적관찰필요.
            self.seleted_code = list(self.dict_code_name.keys())[0]
            print('선택된주식코드', self.seleted_code)

            # print('UpGwansim:codelist', self.dict_code_name)
            rows = len(self.dict_code_name)
            self.table_gwansim.setRowCount(rows)
            # self.table_gwansim.setColumnWidth(0, 120)
            for row, (code, name) in enumerate(self.dict_code_name.items()):
                item = QtWidgets.QTableWidgetItem(name)
                self.table_gwansim.setItem(row, 0, item)
                self.code_index[code] = row

        elif data[0] == 'real':     # data = ('real', code, name, c, db, per, cv, cva, ch)
            code = data[1]
            code_info = data[2:]
            row = self.code_index[code] # (name, c, db, per, cv, cva, ch)

            for col in range(7):  # table_gwansim columns 수
                item = str(code_info[col])
                # print('item', type(item), item)
                item = QtWidgets.QTableWidgetItem(item)
                self.table_gwansim.setItem(row, col, item)

    def UpdateJango(self, data):

        # print('Up_acc', data[1])
        if data[0] == '잔고없음':
            item = QtWidgets.QTableWidgetItem('보유잔고없음')
            self.table_account.setItem(0, 0, item)
        elif data[0] == '잔고있음':
            jango = data[1]  # data[1] = [(name, quan, buy_prc, cur, Y_rate, EG, EA),반복]
            cnt = len(jango)
            # print('cnt', cnt)
            # column단위로 item값을 정렬하는 명령어를 찾아서 사용해야 한다. name = 좌측 기타 숫자는 우측 정렬 필요.

            for index1 in range(cnt):
                for index2 in range(7):
                    item = jango[index1][index2]
                    item = QtWidgets.QTableWidgetItem(item)
                    self.table_account.setItem(index1, index2, item)

    # 호가창 처음 설정
    def UpdateHoga(self, data):

        # 체결수량을 가져와서 같이 작업필요.
        # code를 사용하여 선택된 자료를 송출할 필요가 있다.
        # 그 보다도 선택된 종목에 대한 호가정보만 가져와야 한다.
        code = self.seleted_code   # 현재 선택된 종목 ; 호가창과 차트에 나타낼 종목, 주문도 할 종목

        if data[0] == 'hoga':    # data = ('real', hg_db리스트, hg_sr리스트, hg_ga리스트, per리스트)
            # print('updatehoga', data[1])

            hoga_data = data[1:]
            cnt = len(hoga_data[0])   # 리스트의 크기(대표적으로 hg_db기준)

            # table cell의 설정.(처음 한번만 하면 된다)
            for index in range(4):    # hg_db, hg_sr, hg_ga, per 순회
                for index2 in range(cnt):
                    row, col = index2, index + 2
                    self.table_hoga2.setItem(row, col, QtWidgets.QTableWidgetItem())
                    self.table_hoga2.item(row,col).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))

            for index in range(4):    # hg_db, hg_sr, hg_ga, per 순회
                for index2 in range(cnt):
                    item = hoga_data[index][index2]
                    # item = QtWidgets.QTableWidgetItem(item)
                    row, col = index2, index + 2
                    item = format(item, ",")
                    self.table_hoga2.item(row,col).setData(Qt.DisplayRole, item)

            '''
            for index in range(4):    # hg_db, hg_sr, hg_ga, per 순회
                for index2 in range(cnt):
                    item = str(hoga_data[index][index2])
                    item = QtWidgets.QTableWidgetItem(item)
                    row, col = index2, index + 2
                    self.table_hoga2.setItem(row, col, item)
            '''

        elif data[0] == 'chaegyeol':    # data = ('chaegyeol', v)

            volume = data[1]
            volume_copy = None

            if self.table_hoga2.item(0,1) == None:    # 0,1 cell이 None이라는 건 맨 처음이라는 뜻.
                # cell item의 QtableWidgetItem() 및 Alignment를 설정한다.
                for row in range(22):
                    self.table_hoga2.setItem(row, 1, QtWidgets.QTableWidgetItem())
                    self.table_hoga2.item(row, 1).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))

                # 0,1 값을 넣고 return
                if volume < 0:
                    self.table_hoga2.item(0, 1).setForeground(QtGui.QBrush(Qt.red))
                elif volume > 0:
                    self.table_hoga2.item(0, 1).setForeground(QtGui.QBrush(Qt.blue))

                self.table_hoga2.item(0, 1).setData(Qt.DisplayRole, volume)
                return
            else:
                volume_copy = self.table_hoga2.item(0,1).text()

                if volume < 0:
                    self.table_hoga2.item(0, 1).setForeground(QtGui.QBrush(Qt.red))
                elif volume > 0:
                    self.table_hoga2.item(0, 1).setForeground(QtGui.QBrush(Qt.blue))

                self.table_hoga2.item(0, 1).setData(Qt.DisplayRole, volume)

            # print('item_copy', item_copy)
            for row in range(1,22):
                if self.table_hoga2.item(row,1).text() == "":   # cell의 설정을 해 둔 상태이므로 text()값만 점검하면 된다.
                    self.table_hoga2.item(row,1).setData(Qt.DisplayRole, volume_copy)
                    return

                volume = self.table_hoga2.item(row,1).text()
                print('type', type(volume))
                # volume = self.table_hoga2.item(row,1).data(Qt.DisplayRole)

                # if int(volume_copy) < 0:
                if int(volume_copy) < 0:
                    self.table_hoga2.item(row, 1).setForeground(QtGui.QBrush(Qt.red))
                elif int(volume_copy) > 0:
                    self.table_hoga2.item(row, 1).setForeground(QtGui.QBrush(Qt.blue))

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


