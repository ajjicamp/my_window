import sys
import time
from PyQt5 import QtWidgets, uic
from multiprocessing import Process
from PyQt5.QtCore import Qt


# from mWindow import MWindow

form_class01 = uic.loadUiType('C:/Users/USER/PycharmProjects/my_window/multiwindow/subwindow01.ui')[0]
# form_class02 = uic.loadUiType('C:/Users/USER/PycharmProjects/my_window/multiwindow/subwindow02.ui')[0]

class SubWindow01(QtWidgets.QMainWindow, form_class01):
    def __init__(self, parent, queue):
        # app = QtWidgets.QApplication(sys.argv)
        super(SubWindow01, self).__init__(parent)
        self.parent = parent
        self.q = queue
        self.setupUi(self)
        self.show()
        self.start()
        # app.exec_()

        # time.sleep(0.0003)

    def start(self):
        item_0 = "test sub"
        item_0 = QtWidgets.QTableWidgetItem(item_0)
        item_0.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
        self.parent.tableWidget.setItem(4, 2, item_0)

        '''
        stime = time.time()
        x1, y1 = 0, 0
        for i in range(50000):
            x1 = i * i
            y1 += x1
            # print(f'y1: {y1}')
        print(f'sub01_runtime: {time.time() - stime}')
         '''
        print('sub01_name:', __name__)
        # print('sub01_current name: ', current_process())

class SubWindowWrite(Process):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent =parent
        print('subwindowwrite')