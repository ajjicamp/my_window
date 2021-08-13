# 복수의 윈도우를 띄우는 방법은 mainwindow에서 sub window를 호출하는 방법(호출할때 인자로 self를 보낸다)이 가장 무난하다.
# 이 경우는 main 위에 sub가 뜨게 된다. sub가 여러개일 경우에는 현재창(클릭한 창)이 가장 위에 있게 된다.
# 또한 app = QApplication과 app.exec_()는 메인창에 하나만 설치하면 되고, sub window창에 별도로 설치할 필요가 없다.
# main에서 click event를 사용해서 sub를 호출하면 별문제 없이 뜨게 되나, 직접 여러개를 호출하면 문제가 발생한다.
# sub window class는 같은 파일이 아니라도 상관없다. 분리해도 똑 같은 방법으로 사용할 수 있다.
# multiprocess로 호출하는 방식은 if __name__ == '__main__'에서만 호출가능하여 현재로서는 선택조건이 아니라 무조건 띄울 수 밖에 없어서 무용이다.
# 복수의 window를 여러개 사용하면서 cpu부하를 줄일 수 있는 방식이 무엇인지 모르겠다.

import sys
import time
import datetime
from PyQt5 import QtWidgets, QAxContainer, uic
from multiprocessing import Process, Queue, Pool, current_process
from subwindow import SubWindow01
import pythoncom

form_class = uic.loadUiType('C:/Users/USER/PycharmProjects/my_window/multiwindow/mwindow01.ui')[0]
# form_class01 = uic.loadUiType('C:/Users/USER/PycharmProjects/my_window/multiwindow/subwindow01.ui')[0]
form_class02 = uic.loadUiType('C:/Users/USER/PycharmProjects/my_window/multiwindow/subwindow02.ui')[0]

class MWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        super().__init__()
        queue = Queue()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.subWindow01_clicked)
        self.pushButton_2.clicked.connect(self.subWindow02_clicked)

        self.show()
        self.start()

        app.exec_()


    def start(self):
        print('Process run')
        print('main_current name: ',current_process() )

    def subWindow01_clicked(self,queue):
        # sub01 = SubWindow01(self)
        SubWindow01(self, queue)

    def subWindow02_clicked(self, queue):
        sub02 = SubWindow02(self, queue)

'''
class SubWindow01(QtWidgets.QMainWindow, form_class01):
    def __init__(self,parent):
        # app = QtWidgets.QApplication(sys.argv)
        super(SubWindow01, self).__init__(parent)
        self.setupUi(self)
        self.show()
        self.start()
        # app.exec_()

        # time.sleep(0.0003)
    def start(self):
        stime = time.time()
        x1, y1 = 0, 0
        for i in range(50000):
            x1 = i * i
            y1 += x1
            # print(f'y1: {y1}')
        print(f'sub01_runtime: {time.time() - stime }')
        print('name:', __name__)
        print('sub01_current name: ',current_process() )
'''

class SubWindow02(QtWidgets.QDialog, form_class02):
    def __init__(self, parent, queue):
        # app = QtWidgets.QApplication(sys.argv)
        super(SubWindow02, self).__init__(parent)
        self.q = queue
        self.setupUi(self)
        self.show()
        self.start()
        # time.sleep(0.0003)
        # app.exec_()
    def start(self):
        stime = time.time()
        x2, y2 = 0, 0
        for i in range(100000):
            x2 = i * i
            y2 += x2
            # print(f'y: {y2}')
        print(f'sub02_runtime: {time.time() - stime }')
        print(__name__)

def timedelta_sec(second, std_time=None):
    if std_time is None:
        next_time = now() + datetime.timedelta(seconds=second)
    else:
        next_time = std_time + datetime.timedelta(seconds=second)
    return next_time

def now():
    return datetime.datetime.now()

if __name__ == "__main__":
    # app = QtWidgets.QApplication(sys.argv)

    # Process(target=MWindow, args=()).start()
    # Process(target=SubWindow01, args=()).start()
    # Process(target=SubWindow02, args=()).start()

    mwindow = MWindow()
    # subwindow01 = SubWindow01()
    # subwindow02 = SubWindow02()


    # app.exec_()