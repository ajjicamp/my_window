import sys

from PyQt5.QtWidgets import *
import matplotlib.pyplot as plt

class TextShow:
    def __init__(self):
        fig = plt.figure(figsize=(15, 10))
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)

        x = [4, 8, 12, 16]
        val = [2, 3, 4, 5]
        ax1.plot(x, val)
        ax1.text(9, 3, "text")
        ax1.annotate("annotate", (12, 4))
        plt.show()
        # fig.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    textshow = TextShow()
    app.exec_()