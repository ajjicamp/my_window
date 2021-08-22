import datetime
import sys
import time
from PyQt5 import QtWidgets, QtCore, QAxContainer, uic
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

        '''
        나중 여기에 widget종류를 적어놓는다. 
        가능하면 단축키를 이용하여 콤보박스에서 선택하는 방식으로 해본다.
        self.table_gwansim
        self.table_account
        self.table_hoga
        '''
        self.table_gwansim.setColumnWidth(0, 120)
        self.table_account.setColumnWidth(0, 120)

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

    # @QtCore.pyqtSlot(list)
    def UpdateTextedit(self, msg):
        if msg[0] == '수신시간':
            now = datetime.datetime.now()
            self.textEdit.append(f'{str(now)} 수신시간 {msg[1]}')

        else:
            self.textEdit.append(msg[1])

    def UpdateGwansim(self, data): # 여기서 data는 관심종목 table에 add하기 위한 collection(듀플,리스트,dataframe 등)이다
        code_index = {}  # 나중 update할때 종목코드가 위치한 row값을 찾기위해서 변수저장
        if data[0] == 'initial':
            # print(type(data[1]))
            dict_code_name = data[1]  # dict, data = ('initial',self.dict_code_name )
            # print('UpGwansim:codelist', dict_code_name)
            rows = len(dict_code_name)
            self.table_gwansim.setRowCount(rows)
            # self.table_gwansim.setColumnWidth(0, 120)
            for row, (code, name) in enumerate(dict_code_name.items()):
                item = QtWidgets.QTableWidgetItem(name)
                self.table_gwansim.setItem(row, 0, item)
                code_index[code] = row

        elif data[0] == 'real':     # data = ('real', code, name, c, db, per, cv, cva, ch)
            code = data[1]
            row = code_index[code]

            for col in range(7):  # table_gwansim columns 수
                item = QtWidgets.QTableWidgetItem(data[2:][col])
                self.table_gwansim.setItems(row, col, item)

    def UpdateJango(self, data):
        print('Up_acc', data[1])
        if data[0] == '잔고없음':
            item = QtWidgets.QTableWidgetItem('보유잔고없음')
            self.table_account.setItem(0, 0, item)
        elif data[0] == '잔고있음':
            jango = data[1]  # data[1] = [(name, quan, buy_prc, cur, Y_rate, EG, EA),반복]
            cnt = len(jango)
            # print('cnt', cnt)
            for index1 in range(cnt):
                for index2 in range(7):
                    item = jango[index1][index2]
                    item = QtWidgets.QTableWidgetItem(item)
                    self.table_account.setItem(index1, index2, item)

    def UpdateHoga(self, data):
        # 체결수량을 가져와서 같이 작업필요.
        # code를 사용하여 선택된 자료를 송출할 필요가 있다.
        # 그 보다도 선택된 종목에 대한 호가정보만 가져와야 한다.

        code = None   # 현재 선택된 종목 ; 호가창과 차트에 나타낼 종목, 주문도 할 종목
        if data[0] == 'real' and data[1] == code :    # data = ('real', code, hg_db, hg_sr, hg_ga, per)

            hoga_data = data[2:]
            cnt = len(hoga_data)
            for row in range(cnt):
                for index in range(2,6):
                    item = hoga_data[index]
                    item = QtWidgets.QTableWidgetItem(item)
                    col = index + 0  # 우연히 일치한다.
                    self.table_hoga.setItem(row, col, item)

            pass
        elif data[0] == 'chaegyeol':

        pass

    def UpdateChart(self, data):
        pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    windowQ, workerQ, hogaQ = Queue(), Queue(), Queue()
    Process(target=Worker, name='name_worker', args=(windowQ, workerQ, hogaQ,), daemon=True).start()
    # Process(target=HogaWindow, args=(windowQ, hogaQ,), daemon=True).start()
    # p = Pool(5)
    # p.map(MyWindow(),[])
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()


