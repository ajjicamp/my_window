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

        '''
        나중 여기에 widget종류를 적어놓는다. 
        가능하면 단축키를 이용하여 콤보박스에서 선택하는 방식으로 해본다.
        self.table_gwansim
        self.table_account
        self.table_hoga
        '''
        self.table_gwansim.setColumnWidth(0, 120)
        self.table_account.setColumnWidth(0, 120)
        self.table_acc_eva.setColumnWidth(1, 100)

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

    def UpdateGwansim(self, data): # 여기서 data는 관심종목 table에 add하기 위한 collection(듀플,리스트,dataframe 등)이다

        if data[0] == 'initial':
            self.dict_code_name = data[1]  # dict, data = ('initial',self.dict_code_name )
            # name, code를 바꾸어서 name을 key로 code를 검색할 수 있도록 함.
            self.dict_name_code = { v:k for k, v in self.dict_code_name.items() }
            # print('self.dict_name_code', self.dict_name_code)

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
                item = format(code_info, ',')
                self.table_gwansim.item(row, col).setData(Qt.DisplayRole, item)
                # self.table_gwansim.item(row, col).setText(item)
                # todo 여기서 setText() 대신 굳이 setData()를 사용할 필요가 없다. sort할 일이 없으면
                self.table_gwansim.item(row, col).setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))

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
        # worker process에서 지정종목에 대한 호가/체결정보만 보내준다. 그냥 기업하면 됨
        # code = self.seleted_code   # 현재 선택된 종목 ; 호가창과 차트에 나타낼 종목, 주문도 할 종목
        if data[0] == 'hoga':    # data = ('real', hg_db리스트, hg_sr리스트, hg_ga리스트, per리스트)
            # print('updatehoga', data[1])

            hoga_data = data[1:]
            cnt = len(hoga_data[0])   # 리스트의 크기(대표적으로 hg_db기준) ; 22줄이다.

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
                    # todo self.table_hoga2.item(row,col).setText(item)

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


