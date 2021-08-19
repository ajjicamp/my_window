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
        print('self: ', self)
        print('form_class', form_class)
        # self.show()
        # todo pyqtSlot 설정
        self.writer = Writer(windowQ)
        # self.writer.data0.connect(self.UpdateTexedit)
        self.writer.data0.connect(self.ExeOrder)
        self.writer.data1.connect(self.UpdateGwansim)
        self.writer.data2.connect(self.UpdateTablewidget)
        self.writer.start()

        # app.exec_()
    # @QtCore.pyqtSlot(list)
    def ExeOrder(self, msg):
        if msg[0] == '수신시간':
            now = datetime.datetime.now()
            self.textEdit.append(f'{str(now)} 수신시간 {msg[1]}')
        elif msg[0] == '관심종목코드':
            self.gwansim_code = msg[1]  # {관심종목코드, 관심종목이름} type(dict)
            print('관심종목코드:$$', self.gwansim_code)
            self.UpdateGwansim('temp')
    def UpdateGwansim(self, data): # 여기서 data는 관심종목 table에 add하기 위한 collection(듀플,리스트,dataframe 등)이다
        # todo
        for i , (code, name) in enumerate(self.gwansim_code.items()):

            # item = self.gwansim_code[i]
            print('관심종목리스트:$$', code, name)

        # 종목명을 indexkey로 찾아서 입력해야 한다.
        # item = data[]
        # self.table_gwansim =

    def DrawChart(self, data):
        pass

    def UpdateTablewidget(self):
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


