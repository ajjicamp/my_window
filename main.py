import datetime
import sys
import time
from PyQt5 import QtWidgets, QAxContainer, uic
from multiprocessing import Process, Queue, Pool
from worker import Worker
from writer import Writer
from hoga import HogaWindow

# app =QtWidgets.QApplication(sys.argv)
form_class = uic.loadUiType('mywindow.ui')[0]

class MyWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        print('self: ', self)
        print('form_class', form_class)
        # self.show()
        # todo pyqtSlot 설정
        self.writer = Writer(windowQ)
        self.writer.data0.connect(self.UpdateTexedit)
        self.writer.data1.connect(self.DrawChart)
        self.writer.data2.connect(self.UpdateTablewidget)
        self.writer.start()
        # app.exec_()

    def UpdateTexedit(self,msg):
        now = datetime.datetime.now()
        self.textEdit.append(f'{str(now)} 수신시간 {msg[1]}')

    def DrawChart(self,data):
        pass

    def UpdateTablewidget(self):
        pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    windowQ, workerQ, hogaQ = Queue(), Queue(), Queue()
    # Process(target=Worker, name='name_worker', args=(windowQ, workerQ, hogaQ,), daemon=True).start()
    # Process(target=HogaWindow, args=(windowQ, hogaQ,), daemon=True).start()
    # p = Pool(5)
    # p.map(MyWindow(),[])
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()


