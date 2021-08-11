import sys
import time
from PyQt5 import QtWidgets, QAxContainer, uic
from multiprocessing import Process, Queue
from worker import Worker
from writer import Writer
from hoga import Hoga

form_class = uic.loadUiType('mywindow.ui')[0]

class MyWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.start_process()
        # todo pyqtSlot 설정
        self.writer = Writer(windowQ)
        self.writer.data0.connect(self.UpdateTexedit)
        self.writer.data1.connect(self.DrawChart)
        self.writer.data2.connect(self.UpdateTablewidget)
        self.writer.start()

    def UpdateTexedit(self,msg):
        self.textEdit.append(f'{str(msg[0])} {msg[1]}')
        # self.textEdit.append(str(msg[0]))

    def DrawChart(self,data):
        pass

    def UpdateTablewidget(self):
        pass

if __name__ == '__main__':
    windowQ, workerQ, hogaQ = Queue(), Queue(), Queue()
    Process(target=Worker, args=(windowQ, workerQ, hogaQ,), daemon=True).start()
    Process(target=Hoga, args=(windowQ, hogaQ,), daemon=True).start()
    app = QtWidgets.QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()


