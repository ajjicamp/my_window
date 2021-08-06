import sys
import sys
from PyQt5 import QtWidgets, QAxContainer, uic
from multiprocessing import Process, Queue
from worker import Worker

form_class = uic.loadUiType('mywindow.ui')[0]

class MyWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.start_process()

    # def start_process(self):
    #     queue = Queue
    #     p = Process(target= Worker, args= (queue, ), daemon = False)
    #     p.start()
    #     p.join()



if __name__ == '__main__':

    # queue = Queue
    queue = "Queue"
    Process(target=Worker, args=(queue,), daemon=True).start()
    # Process(target=Worker, args=(queue,), daemon=False).start()
    # p = Process(target=Worker, args=(queue,), daemon=False)
    # worker = Worker(queue)
    # worker.start()
    app = QtWidgets.QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()


