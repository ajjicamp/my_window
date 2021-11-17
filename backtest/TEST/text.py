import sys

from PyQt5.QtWidgets import *
import matplotlib.pyplot as plt
from matplotlib.artist import Artist



class TextShow:
    # def __init__(self, redraw=False, event=None):
    def __init__(self):
        # self.redraw = redraw
        self.fig = plt.figure(figsize=(8, 5))
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2)

        x = [4, 8, 12, 16]
        val = [2, 3, 4, 5]
        self.ax1.plot(x, val)
        self.frame = None

        # xv = x[0]
        # yv = val[0]
        # text = val[yv]
        # if not self.redraw:
        # self.ax1.text(xv, yv, text, fontsize=20)
        # self.ax1.annotate("annotate", (12, 4))

        def notify_event(event):
            print('texts', self.ax1.texts)
            # for txt in self.ax1.texts:
            #     txt.set_visible(False)
            if self.frame is not None:
                # Artist.remove(self.frame)
                del self.ax1.texts[0]

            if event.inaxes == self.ax1:
                xv = event.xdata
                yv = event.ydata
                print(xv, yv)
                # self.redraw = True
                # text = "text****"
                y_ = round(yv)
                print(y_)
                text = None
                if y_ in val:
                    text = y_
                self.frame = self.ax1.text(xv, yv, text)
                self.fig.canvas.draw()

        self.fig.canvas.mpl_connect("button_press_event", notify_event)
        plt.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    textshow = TextShow()
    app.exec_()