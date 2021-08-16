import sys
from PyQt5.QtWidgets import *
import time
from multiprocessing import Process, Queue, current_process, Pipe

class MainWindow(QMainWindow):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        # self.pipe = Pipe()
        self.resize(1000, 500)
        self.setWindowTitle('MainWindow')

        self.pushbutton = QPushButton('hoga', self)
        self.pushbutton.move(10, 10)
        # self.pushbutton.clicked.connect(self.hogaWindow)
        self.hogaWindow()

        # self.tabwidget = QTabWidget()

    def hogaWindow(self):
        print('호가윈도우입니다.')
        self.widget = QTableWidget(self)
        self.widget.show()
        self.widget.move(10,150)
        self.widget.resize(500, 200)

        self.widget.setColumnCount(6)
        self.widget.setRowCount(20)

        self.do_process(self.widget)
        # Process(name='widget', target=UpdateWindow).start()

    def do_process(self, widget):
        pipe_a, pipe_b = Pipe()
        pipe_a.send(widget)
        Process(name='widget', target=UpdateWindow, args=(pipe_b,)).start()

        # print('cur_pros', current_process().name)
        # if current_process().name == 'widget':
        # UpdateWindow(widget)


    # def proexe(self, queue):
    #     self.queue = queue
    #     if not self.queue.empty():
    #         widget = self.queue.get()
    #         UpdateWindow(widget)
class UpdateWindow:
    def __init__(self,pipe_b):
        widget = pipe_b.recv()
        val = 'TEST$$$'
        item = QTableWidgetItem(val)
        # self.widget.setItem(1, 1, item)
        widget.setItem(1, 1, item)

    '''
    # print('UpdateWindow')
    def __init__(self, queue):
        self.queue = queue
        print('qsize', self.queue.qsize())
        # window = None
        while True:
            if not self.queue.empty():
                window = self.queue.get()
                val = 'TEST$$$'
                item = QTableWidgetItem(val)
                window.setItem(1, 1, item)
    '''
if __name__ == '__main__':
    app = QApplication(sys.argv)
    queue = Queue()
    main = MainWindow(queue)
    main.show()
    app.exec_()