import os
import sys
import sqlite3
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtGui, uic
from mplfinance.original_flavor import candlestick2_ohlc
from matplotlib import gridspec
import matplotlib.pyplot as plt
import numpy as np

plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False  # 한글 폰트 사용시 마이너스 폰트 깨짐 해결

# PATH ="C:/Users/USER/PycharmProjects/my_window/backtest"
PATH =os.getcwd()
DB_MARKET_JISU = f"{PATH}/market_jisu(1min).db"
DB_GOLDEN_CROSS_DEAL = f"{PATH}/golden_cross_deal.db"
DB_GOLDEN_CROSS_SUMMARY = f"{PATH}/golden_cross_summary.db"

START = '20210601'
END = '20210930'


class DealStrategy(QMainWindow):
    def __init__(self):
        super().__init__()
        con = sqlite3.connect(DB_GOLDEN_CROSS_SUMMARY)
        df = pd.read_sql(f"SELECT * FROM deal_summary", con)
        con.close()
        row_count = len(df)
        column_count = len(df.columns)
        self.setGeometry(100, 100, 1000, 1000)
        self.setWindowTitle("이평선 크로스 전략")
        self.table = QTableWidget(self)
        self.table.setGeometry(0, 0, 1000, 1000)

        self.table.setRowCount(row_count)
        self.table.setColumnCount(column_count)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalHeaderLabels(df.columns)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setFont(QtGui.QFont("맑은 고딕", 11))
        stylesheet = "::section{Background-color:rgb(190,1,1,30)}"
        self.table.horizontalHeader().setStyleSheet(stylesheet)
        self.table.setFont(QtGui.QFont("맑은 고딕", 11))
        self.table.setAlternatingRowColors(True)
        for i in range(0, 15):
            self.table.setColumnWidth(i, 95)
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 230)
        self.table.setColumnWidth(4, 130)

        for i, val in enumerate(df.values):
            for col in range(len(df.columns)):
                data = val[col]
                item = None
                if type(val[col]) == str:
                    item = QTableWidgetItem(data)
                    item.setTextAlignment(int(Qt.AlignCenter) | int(Qt.AlignVCenter))

                elif type(val[col]) == float or type(val[col]) == int:
                    item = QTableWidgetItem()
                    item.setData(Qt.DisplayRole, data)
                    item.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.table.setItem(i, col, item)

        def cell_clicked(row):
            gubun = self.table.item(row, 0).text()
            exitStrategy = self.table.item(row, 1).text()
            dealpoint = DealPoint(gubun, exitStrategy)
        self.table.cellClicked.connect(cell_clicked)

        self.show()


class DealPoint(QWidget):
    def __init__(self, gubun, exitStrategy):
        super().__init__()
        table = f"{gubun}_{exitStrategy}"
        con = sqlite3.connect(DB_GOLDEN_CROSS_DEAL)
        df = pd.read_sql(f"SELECT * FROM '{table}'", con)
        con.close()
        # print('db에서 읽어온 df\n', df)
        column_count = len(df.columns)
        row_count = len(df)
        self.setGeometry(100, 100, 1800, 900)
        self.setWindowTitle(f"CrossUp & {exitStrategy}")
        self.table = QTableWidget(self)
        self.table.setGeometry(0, 0, 1750, 900)

        self.table.setRowCount(row_count)
        self.table.setColumnCount(column_count)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalHeaderLabels(df.columns)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setFont(QtGui.QFont("맑은 고딕", 11))
        stylesheet = "::section{Background-color:rgb(190,1,1,30)}"
        self.table.horizontalHeader().setStyleSheet(stylesheet)
        self.table.setFont(QtGui.QFont("맑은 고딕", 11))
        self.table.setAlternatingRowColors(True)
        for i in range(0, 15):
            self.table.setColumnWidth(i, 95)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(2, 130)

        for i, val in enumerate(df.values):
            for col in range(len(df.columns)):
                data = val[col]
                item = None
                if type(val[col]) == str:
                    item = QTableWidgetItem(data)
                    item.setTextAlignment(int(Qt.AlignCenter) | int(Qt.AlignVCenter))

                elif type(val[col]) == float or type(val[col]) == int:
                    item = QTableWidgetItem()
                    item.setData(Qt.DisplayRole, data)
                    item.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.table.setItem(i, col, item)

        df = self.get_minute_data(gubun)
        def cell_clicked(row):
            buy_time = self.table.item(row, 0).text()  # 202109160909
            buy_price = float(self.table.item(row, 1).text())
            sell_time = self.table.item(row, 2).text()  # 202109160909
            sell_price = float(self.table.item(row, 3).text())

            # todo
            df_1day = df.loc[buy_time[:8]]
            start_num = df.index.to_list().index(df_1day.index[0])
            end_num = df.index.to_list().index(df_1day.index[-1])
            deal_df = df.iloc[start_num - 20: end_num + 20]

            self.fig = None
            self.drawDayChart(deal_df, buy_time, buy_price, sell_time, sell_price, start_num, end_num)  # tdate ;  2021-09-16 형식

        self.table.cellClicked.connect(cell_clicked)
        self.show()

    def get_minute_data(self, gubun):
        # 시초가부터 이평선을 그리기 위하여 하루치 분봉만 가져와서는 안되므로 전부 다 가져와서 slicing 해서 사용.
        con = sqlite3.connect(DB_MARKET_JISU)
        df = pd.read_sql(f"SELECT * FROM '{gubun}' WHERE 체결시간 >= {START} and 체결시간 <= {END} "
                         f"ORDER BY 체결시간", con, index_col='체결시간', parse_dates='체결시간')
        con.close()
        df.index.name = 'date'
        df.columns = ['close', 'open', 'high', 'low', 'volume']
        df = df[['open', 'high', 'low', 'close', 'volume']]

        df1 = df['open'].resample('3T').first()
        df2 = df['high'].resample('3T').max()
        df3 = df['low'].resample('3T').min()
        df4 = df['close'].resample('3T').last()
        df5 = df['volume'].resample('3T').sum()

        df = pd.concat([df1, df2, df3, df4, df5], axis=1)
        # 결측치 데이터 삭제
        df = df.dropna()
        df['전봉종가'] = df['close'].shift(1)
        df['5이평'] = df['close'].rolling(window=5).mean()
        df['20이평'] = df['close'].rolling(window=20).mean()
        df['signal'] = np.where(df['5이평'] > df['20이평'], 1.0, 0.0)
        df['trigger'] = df['signal'].diff()

        return df

    def drawDayChart(self, df, buy_time, buy_price, sell_time, sell_price, start_num, end_num):  # df; deal_df
        plt.close()
        fig = plt.figure(figsize=(15, 9))
        gs = gridspec.GridSpec(nrows=2,  # row 몇 개
                               ncols=1,  # col 몇 개
                               height_ratios=[3, 1],
                               width_ratios=[20]
                               )
        fig.subplots_adjust(left=0.10, bottom=0.10, right=0.95, top=0.95, wspace=0.1, hspace=0.01)

        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        x_axes = range(len(df.index))

        candlestick2_ohlc(ax1, df['open'], df['high'], df['low'],
                          df['close'], width=0.8,
                          colorup='r', colordown='b')
        ax1.plot(x_axes, df['5이평'], color='green', linewidth=2)
        ax1.plot(x_axes, df['20이평'], color='yellow', linewidth=2)

        df_crossUp = [df.at[i, '5이평'] * 0.9998 if df.at[i, 'trigger'] == 1 else np.nan for i in df.index]
        ax1.scatter(x_axes, df_crossUp, marker='^', color='white', edgecolor='black', s=100)

        df_crossDown = [df.at[i, '5이평'] * 1.0002 if df.at[i, 'trigger'] == -1 else np.nan for i in df.index]
        ax1.scatter(x_axes, df_crossDown, marker='v', color='lime', edgecolor='black', s=100)

        ax1.set_title(f"{buy_time[:8]} 분봉차트", fontsize=20)
        ax1.set_facecolor('gainsboro')
        ax1.legend(['5이평', '20이평'])
        ax1.tick_params(axis='x', top=False, bottom=False, labeltop=False, labelbottom=False, width=0.2, labelsize=11)
        ax1.grid(True, which='major', color='gray', linewidth=0.2)

        ax2.bar(x_axes, df['volume'])
        ax2.set_xticks(range(0, len(df.index), 5))
        ax2.set_xticks(x_axes, minor=True)
        name_list = [v.strftime("%H:%M") for i, v in enumerate(df.index)]
        name_list = [name_list[i] for i in range(0, len(df.index), 5)]
        ax2.set_xticklabels(name_list, rotation=90)
        ax2.set_facecolor('gainsboro')
        ax2.grid(True, which='major', color='gray', linewidth=0.2)

        my_color = 'c'
        right_vline = len(x_axes) - 18.5 if not buy_time[:8] == df.index[-1].strftime("%Y%m%d%H%M")[:8] else len(x_axes)
        ax1.axvline(19.5, 0, 1, color=my_color, linestyle='--', linewidth=2)
        ax1.axvline(right_vline, 0, 1, color=my_color, linestyle='--', linewidth=2)
        ax2.axvline(19.5, 0, 1, color=my_color, linestyle='--', linewidth=2)
        ax2.axvline(right_vline, 0, 1, color=my_color, linestyle='--', linewidth=2)

        # annotation; 매수가격 설정
        x_ = df.index.to_list().index(pd.to_datetime(buy_time))
        y_ = buy_price

        # x,y text 좌표값,
        x_text = x_
        y_highest = df['high'].max()
        y_lowest = df['low'].min()
        y_mid = y_lowest + (y_highest - y_lowest) / 2
        if y_ >= y_mid:
            y_text = y_ - (y_highest - y_lowest) / 4
        else:
            y_text = y_ + (y_highest - y_lowest) / 4

        ax1.annotate(f'매수:{str(int(buy_price))}', (x_, y_), xytext=(x_text, y_text),
                     arrowprops=dict(edgecolor='black', facecolor='yellow', shrink=0.05, width=0.5, headwidth=5, alpha=0.7),
                     fontsize=12, bbox=dict(facecolor='r', alpha=0.2))

        # 매도가격 annotation
        x2_ = df.index.to_list().index(pd.to_datetime(sell_time))
        y2_ = sell_price
        x2_text = x2_
        if y2_ >= y_mid:
            y2_text = y2_ - (y_highest - y_lowest) / 3
        else:
            y2_text = y2_ + (y_highest - y_lowest) / 3

        ax1.annotate(f'매도:{str(int(sell_price))}', (x2_, y2_), xytext=(x2_text, y2_text),
                     arrowprops=dict(edgecolor='black', facecolor='yellow', shrink=0.05, width=0.5, headwidth=5, alpha=0.7),
                     fontsize=12, bbox=dict(facecolor='b', alpha=0.2))

        def motion_notify_event(event):
            # logging.info(f"592r, x좌표={event.xdata}, {event.inaxes == ax1}")
            if len(ax1.texts) > 2:
                for txt in ax1.texts:
                    txt.set_visible(False)
                ax1.texts[0].set_visible(True)
                ax1.texts[1].set_visible(True)

            if event.inaxes == ax1:
                # logging.info(f"x좌표={event.xdata}")
                xv = round(event.xdata)
                if (xv < len(df)) and (event.ydata <= df['high'][xv]) and (
                        event.ydata >= df['low'][xv]):
                    # fig.canvas.flush_events()
                    close_1 = df['전봉종가'][xv]
                    open_ = df['open'][xv]
                    high_ = df['high'][xv]
                    low_ = df['low'][xv]
                    close_ = df['close'][xv]

                    text = f"시간     :{df.index[xv].strftime('%H:%M')}\n" \
                           f"시가     :{open_} ({round((open_ / close_1 - 1) * 100, 2)}%)\n" \
                           f"고가     :{high_} ({round((high_ / close_1 - 1) * 100, 2)}%)\n" \
                           f"저가     :{low_} ({round((low_ / close_1 - 1) * 100, 2)}%)\n" \
                           f"종가     :{close_} ({round((close_ / close_1 - 1) * 100, 2)}%)\n" \
                           f"거래량   :{df['volume'][xv]}\n" \
                           f"\n" \
                           f"[이평선]\n" \
                           f"5이평선   :{int(df['5이평'][xv])}\n" \
                           f"20이평선  :{df['20이평'][xv]}"

                    # y좌표설정
                    y_highest = df['high'].max()
                    y_lowest = df['low'].min()
                    y_mid = y_lowest + (y_highest - y_lowest) / 2

                    if event.ydata >= y_mid:
                        yv = event.ydata - (y_highest - y_lowest) / 3
                    else:
                        yv = event.ydata + (y_highest - y_lowest) / 10
                else:
                    text = ''
                    yv = event.ydata
                ax1.text(xv + 1.5, yv, text, bbox=dict(facecolor='white', alpha=1.0))
                fig.canvas.draw()

        fig.canvas.mpl_connect("motion_notify_event", motion_notify_event)
        plt.show()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    deal_strategy = DealStrategy()
    app.exec_()

