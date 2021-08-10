import sys
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
        # self.updateECNHoga()


    # def updateECNHoga(self):

if __name__ == '__main__':

    # queue = Queue
    hogaQ = Queue()
    Process(target=Worker, args=(hogaQ,), daemon=True).start()
    # Process(target=Worker, args=(queue,), daemon=False).start()
    # p = Process(target=Worker, args=(queue,), daemon=False)
    # worker = Worker(queue)
    # worker.start()
    app = QtWidgets.QApplication(sys.argv)
    mywindow = MyWindow(hogaQ)
    mywindow.show()
    app.exec_()


