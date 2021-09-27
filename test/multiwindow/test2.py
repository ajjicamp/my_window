import sys
import time
import multiprocessing
from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class start_gui():
    def __init__(self):
        # from PyQt5 import QtWidgets
        # Set up QApplication
        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication(sys.argv)
        # Make GUi
        # import gui
        self.win = MainWindow()
        dialog = Dialog(self.win)
        widget = Widget(self.win)
        # Widget(win)

        # MainWindow()
        app.exec_()

def start2_gui():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    # Make GUi
    # import gui
    # dialog = Dialog()
    # widget = Widget()
    # # MainWindow()
    app.exec_()

# def show():

class MainWindow(QtWidgets.QMainWindow):
    print('class Mainwindow')
    def __init__(self):
        # call super class constructor
        super(MainWindow, self).__init__()
        self.resize(1000, 500)

        widget = QtWidgets.QWidget(self)
        widget.move(10, 10)
        widget.resize(300,200)

        # build the objects one by one
        layout = QtWidgets.QGridLayout(widget)
        self.pb_load = QtWidgets.QPushButton('Load')
        self.pb_clear = QtWidgets.QPushButton('Clear')
        self.edit = QtWidgets.QTextEdit()
        layout.addWidget(self.edit)
        layout.addWidget(self.pb_load)
        layout.addWidget(self.pb_clear)
        # connect the callbacks to the push-buttons
        self.pb_load.clicked.connect(self.callback_pb_load)
        self.pb_clear.clicked.connect(self.callback_pb_clear)
        self.show()

    def callback_pb_load(self):
        self.edit.append('hello world')

    def callback_pb_clear(self):
        self.edit.clear()

class Dialog(QtWidgets.QDialog):
    def __init__(self, parent):
        # call super class constructor
        super(Dialog, self).__init__(parent)
        self.move(150, 50)
        self.resize(300, 200)
        self.setWindowTitle("Dialog##")
        # self.setWindowModality(Qt.NonModal)
        self.show()

class Widget(QtWidgets.QWidget):
    def __init__(self, parent):
        # call super class constructor
        super(Widget, self).__init__(parent)
        self.move(550, 50)
        self.resize(300,100)
        self.setWindowTitle('Widget##')
        self.show()


if __name__ == '__main__':
    thread = multiprocessing.Process(target=start_gui)
    thread.start()

    # thread2 = multiprocessing.Process(target=start2_gui)
    # thread2.start()


    # show()
    print('This happens now')
    # show()
    # Task that takes 5 seconds
    time.sleep(5)
    print('This happens later')
