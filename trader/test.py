import sys

from PyQt5.QtWidgets import *

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1800,1000)
        # self.cetralWidget = QWidget(self)
        # self.cetralWidget.resize(2000,1500)
        #
        # self.tab_widget = QTabWidget(self.cetralWidget)
        self.tab_widget = QTabWidget(self)
        self.tab_widget.resize(1800,1000)

        self.tab1 = QTableWidget()
        self.tab2 = QWidget()

        self.tab_widget.addTab(self.tab1, 'tab1')
        self.tab_widget.addTab(self.tab2, 'tab2')

        self.tab1.setColumnCount(8)
        self.tab1.setRowCount(18)
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    app.exec_()
