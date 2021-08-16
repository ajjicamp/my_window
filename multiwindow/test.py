#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from multiprocessing import Process, current_process

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 윈도우 설정
        self.setGeometry(300, 300, 400, 300)  # x, y, w, h
        self.setWindowTitle('Status Window')

        # QButton 위젯 생성
        self.button = QPushButton('Dialog Button', self)
        self.button.clicked.connect(self.dialog_open)
        self.button.setGeometry(10, 10, 200, 50)

        self.button_2 = QPushButton('Dialog Button', self)
        self.button_2.clicked.connect(self.dialog_open)
        self.button_2.setGeometry(10, 80, 200, 50)

        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setRowCount(20)
        self.table.setGeometry(10, 150, 350, 150)
        # self.table.show()

        # QDialog 설정
        self.dialog = QDialog()
        self.updateWindow()
        # Process(target=UpdateWindow, args= (self,)).start()

    # 버튼 이벤트 함수
    def dialog_open(self):
        # 버튼 추가
        btnDialog = QPushButton("OK", self.dialog)
        btnDialog.move(100, 100)
        btnDialog.clicked.connect(self.dialog_close)

        # QDialog 세팅
        self.dialog.setWindowTitle('Dialog')
        # self.dialog.setWindowModality(Qt.ApplicationModal)
        self.dialog.setWindowModality(Qt.NonModal)
        self.dialog.resize(500, 400)
        # todo 이것이 중요
        self.dialog.show()

    # Dialog 닫기 이벤트
    def dialog_close(self):
        self.dialog.close()

    def updateWindow(self):
        # print('parent:', self.p)
        print('cur_proc:', current_process())
        print('name:', __name__)
        print('pid: ', os.getpid(), os.getppid())
        item = 'testupdate'
        item = QTableWidgetItem(item)
        self.table.setItem(1, 1, item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())