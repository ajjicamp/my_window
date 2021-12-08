import sqlite3
import sys
from kiwoom import Kiwoom
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtGui, uic
import mplfinance as mpf
from mplfinance.original_flavor import candlestick2_ohlc
from matplotlib import gridspec
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import numpy as np

plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False  # 한글 폰트 사용시 마이너스 폰트 깨짐 해결

PATH ="C:/Users/USER/PycharmProjects/my_window/backtest"
DB_KOSPI_MIN = "C:/Users/USER/PycharmProjects/my_window/db/kospi(1min).db"
DB_KOSDAQ_MIN = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(1min).db"
DB_GOLDEN_CROSS_DEAL = "C:/Users/USER/PycharmProjects/my_window/db/golden_cross_deal.db"

START = '20210601'
END = '20210930'

class GoldenCrossDeal:
    def __init__(self):
        # 지수차트 가져오기
        # 지수차트 분봉을 가져와야 한다.
        con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/db/market_jisu(1min).db")
        df = pd.read_sql(f"SELECT * FROM kosdaq WHERE 체결시간 >= {START} and 체결시간 <= {END} "
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
        df['5이평'] = df['close'].rolling(window=5).mean()
        df['20이평'] = df['close'].rolling(window=20).mean()
        # print('3분봉', len(df))

        df['new_index'] = df.index.values
        # print(df['new_index'])

        df_groupby = df['new_index'].groupby(df['new_index'].apply(lambda x: str(x)[:10]))
        day_list = df_groupby.size().keys().tolist()
        self.df_deal = pd.DataFrame(columns=['매수시간', '매수가', '매도시간', '매도가', '순이익', '순이익률'])
        self.trading(df, day_list)
        print('deal결과\n', self.df_deal)

        con = sqlite3.connect(DB_GOLDEN_CROSS_DEAL)
        table_name = 'dead_cross'
        self.df_deal.to_sql(table_name, con, if_exists='replace', index=False)
        con.close()

        profit_sum = self.df_deal['순이익'].sum()
        buy_sum = self.df_deal['매수가'].sum()
        profit_rate = round(profit_sum / buy_sum * 100, 2)
        print(f"총이익 {profit_sum} 총매수가 {buy_sum} 이익률 {profit_rate}")

    def trading(self, df, day_list):
        df['signal'] = 0.0
        df['signal'] = np.where(df['5이평'] > df['20이평'], 1.0, 0.0)
        df['position'] = df['signal'].diff()

        # df['golden_cross'] = df['5이평'] > df['20이평']
        # df['dead_cross'] = df['20이평'] > df['5이평']
        hold = False
        buy_time = None
        buy_price = None
        sell_time = None
        sell_price = None
        # print('df\n', df, day_list)

        # 하루치 분봉만 가지고 트레이딩 한다.
        for day in day_list:
            if day < '2021-07-01':
                continue
            # print('날짜', day, type(day))
            df_1day = df.loc[day]
            # print('df\n', df)
            for idx in df_1day.index:
                if df_1day.at[idx, 'position'] == 1 and (not hold):
                    buy_time = idx.strftime("%Y%m%d%H%M")
                    buy_price = df_1day.at[idx, 'close']  # 골든크로스가 발생한 봉의 종가에 매수하는 것으로 함.
                    hold = True

                if df_1day.at[idx, 'position'] == -1 and hold:
                    sell_time = idx.strftime("%Y%m%d%H%M")
                    sell_price = df_1day.at[idx, 'close']  # 골든크로스가 발생한 봉의 종가에 매도하는 것으로 함.
                    hold = False
                    profit = sell_price - buy_price
                    self.df_deal.loc[len(self.df_deal)] = [buy_time,
                                                           buy_price,
                                                           sell_time,
                                                           sell_price,
                                                           profit,
                                                           round((profit / buy_price) * 100, 2)
                                                           ]

                if idx == df_1day.index.values[-1] and hold:
                    sell_time = idx.strftime("%Y%m%d%H%M")
                    sell_price = df_1day.at[idx, 'close']  # 종가를 기준으로 평가익을 계산
                    profit = sell_price - buy_price
                    hold = False
                    self.df_deal.loc[len(self.df_deal)] = [buy_time,
                                                           buy_price,
                                                           sell_time,
                                                           sell_price,
                                                           profit,
                                                           round((profit / buy_price) * 100, 2)
                                                           ]


class DealPoint(QWidget):
    def __init__(self):
        super().__init__()
        con = sqlite3.connect(DB_GOLDEN_CROSS_DEAL)
        df = pd.read_sql("SELECT * FROM dead_cross", con)
        con.close()
        print('db에서 읽어온 df\n', df)
        column_count = len(df.columns)
        row_count = len(df)
        self.setGeometry(100, 100, 1800, 900)
        self.setWindowTitle(f'골든크로스 TRADING')
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
        self.table.setColumnWidth(0, 130)
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
        df = self.get_minute_data()
        def cell_clicked(row):
            # code = self.table.item(row, 0).text()
            # print('row', row)
            buy_time = self.table.item(row, 0).text()  # 202109160909
            buy_price = float(self.table.item(row, 1).text())
            sell_time = self.table.item(row, 2).text()  # 202109160909
            sell_price = float(self.table.item(row, 3).text())

            # todo
            df_1day = df.loc[buy_time[:8]]
            # start_num = df_1day.index.shift[-20]
            # end_num = df_1day.index[-1].shift[20]
            deal_df = df.loc[start_num: end_num]
            # input()

            self.fig = None
            self.drawDayChart(deal_df, buy_time, buy_price, sell_time, sell_price)  # tdate ;  2021-09-16 형식
            # self.drawDayChart(df_1day_minute, deal_time)

        # self.table.cellClicked.connect(self.cell_clicked)
        self.table.cellClicked.connect(cell_clicked)
        # print('self_table 객체', self.table)
        self.show()

    def get_minute_data(self):
        # 시초가부터 이평선을 그리기 위하여 하루치 분봉만 가져와서는 안되므로 전부 다 가져와서 slicing 해서 사용.
        con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/db/market_jisu(1min).db")
        df = pd.read_sql(f"SELECT * FROM kosdaq WHERE 체결시간 >= {START} and 체결시간 <= {END} "
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
        df['5이평'] = df['close'].rolling(window=5).mean()
        df['20이평'] = df['close'].rolling(window=20).mean()
        df['signal'] = np.where(df['5이평'] > df['20이평'], 1.0, 0.0)
        df['position'] = df['signal'].diff()
        print('3분봉', df)


        return df

    def drawDayChart(self, df, buy_time, buy_price, sell_time, sell_price):
        # super().__init__()
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
        # print('min_list', min_list, min_list[0], min_list[-1], df_query['volume_ratio'])

        candlestick2_ohlc(ax1, df['open'], df['high'], df['low'],
                          df['close'], width=0.8,
                          colorup='r', colordown='b')
        ax1.plot(x_axes, df['5이평'], color='green', linewidth=2)
        ax1.plot(x_axes, df['20이평'], color='yellow', linewidth=2)
        # ax1.plot(df[df[‘position’] == 1].index, df[‘20이평’][df[‘position’] == 1])

                                   # ‘ ^ ’, markersize = 15, color = ‘g’, label = 'buy')
        ax1.set_title(f"{buy_time[:8]} 분봉차트", fontsize=20)
        ax1.set_facecolor('lightgray')
        ax1.legend(['5이평', '20이평'])
        ax1.tick_params(axis='x', top=False, bottom=False, labeltop=False, labelbottom=False, width=0.2, labelsize=11)
        ax1.grid(True, which='major', color='gray', linewidth=0.2)

        ax2.bar(x_axes, df['volume'])
        ax2.set_xticks(range(0, len(df.index), 5))
        ax2.set_xticks(x_axes, minor=True)
        name_list = [v.strftime("%H:%M") for i, v in enumerate(df.index)]
        name_list = [name_list[i] for i in range(0, len(df.index), 5)]
        ax2.set_xticklabels(name_list, rotation=90)
        ax2.set_facecolor('lightgray')
        ax2.grid(True, which='major', color='gray', linewidth=0.2)

        # annotation; 매수가 설정
        # x_ = [i for i, idx in enumerate(df_day.index) if idx.strftime("%Y-%m-%d") == tdate.strftime("%Y-%m-%d")][0]
        # x,y 좌표값
        x_ = df.index.to_list().index(pd.to_datetime(buy_time))
        y_ = buy_price

        # x,y text좌표값,
        x_text = x_
        y_highest = df['high'].max()
        y_lowest = df['low'].min()
        y_mid = y_lowest + (y_highest - y_lowest) / 2
        if y_ >= y_mid:
            y_text = y_ - (y_highest - y_lowest) / 4
        else:
            y_text = y_ + (y_highest - y_lowest) / 4

        # ax1.annotate(f'매수:{str(int(buy_price))}', (x_, y_), xytext=(x_text, y_text),
        ax1.annotate(f'매수:{str(int(buy_price))}', (x_, y_), xytext=(x_text, y_text),
                     arrowprops=dict(edgecolor='c', facecolor='yellow', shrink=0.05, width=0.5, headwidth=5, alpha=0.7),
                     fontsize=12, bbox=dict(facecolor='r', alpha=0.2))

        # 매도가겨 annotation
        x2_ = df.index.to_list().index(pd.to_datetime(sell_time))
        y2_ = sell_price
        x2_text = x2_
        if y2_ >= y_mid:
            y2_text = y2_ - (y_highest - y_lowest) / 3
        else:
            y2_text = y2_ + (y_highest - y_lowest) / 3

        ax1.annotate(f'매도:{str(int(sell_price))}', (x2_, y2_), xytext=(x2_text, y2_text),
                     arrowprops=dict(edgecolor='c', facecolor='yellow', shrink=0.05, width=0.5, headwidth=5, alpha=0.7),
                     fontsize=12, bbox=dict(facecolor='b', alpha=0.2))

        plt.show()


if __name__ == '__main__':
    # deal = GoldenCrossDeal()
    app = QApplication(sys.argv)
    deal_point = DealPoint()
    # drawchart = DrawChart()
    # drawchart.show()
    app.exec_()

