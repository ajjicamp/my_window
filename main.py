import sys
import sys
from PyQt5 import QtWidgets, QAxContainer, uic
form_class = uic.loadUiType('mywindow.ui')[0]

class MyWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()


