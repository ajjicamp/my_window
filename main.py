import sys
import time
from PyQt5 import QtWidgets, QAxContainer, uic
from multiprocessing import Process, Queue
from worker import Worker

form_class = uic.loadUiType('mywindow.ui')[0]

class MyWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self, hogaQ):
        super().__init__()
        self.setupUi(self)
        # self.start_process()
        self.hogaQ = hogaQ

if __name__ == '__main__':
    hogaQ = Queue()
    Process(target=Worker, args=(hogaQ,), daemon=True).start()
    app = QtWidgets.QApplication(sys.argv)
    mywindow = MyWindow(hogaQ)
    mywindow.show()
    app.exec_()


