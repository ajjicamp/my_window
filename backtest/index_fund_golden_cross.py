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

class GoldenCrossDeal:
    def __init__(self):
        kiwoom = Kiwoom()
        kiwoom.CommConnect()
        # 코스닥지수 다운로드
        df = kiwoom.block_request('opt20005', 업종코드='101', 틱범위=1,
                                                    output='업종분봉조회', next=0)

        # todo 여기 작업중
        int_column = ['현재가', '시가', '고가', '저가', '거래량']
        df[int_column] = df[int_column].replace('', 0)
        df[int_column] = df[int_column].astype(int).abs()
        columns = ['체결시간', '현재가', '시가', '고가', '저가', '거래량']
        df = df[columns].copy()
        dfs.append(df)

        df_kospi_min = kiwoom.block_request('opt20005', 업종코드='001', 틱범위=1,
                                                   output='업종분봉조회', next=0)

        )



        df_kosdaq_jisu = df_kosdaq_jisu[['일자', '시가', '고가', '저가', '현재가', '거래량', '거래대금']]
        df_kosdaq_jisu.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        df_kosdaq_jisu = df_kosdaq_jisu.reset_index(drop=True).set_index('date')
        df_kosdaq_jisu = df_kosdaq_jisu.astype(int)



        # 지수차트 가져오기
        start = '20210601'
        end = '20210930'

        # 지수차트 분봉을 가져와야 한다.
        con = sqlite3.connect(f"{PATH}/market_jisu.db")
        df_kosdaq = pd.read_sql(f"SELECT * FROM kosdaq_jisu WHERE date >= {start} and date <= {end} "
                               f"ORDER BY date", con, index_col='date', parse_dates='date')
        con.close()

        df1 = df_kosdaq['open'].resample('3T').first()
        df2 = df_kosdaq['high'].resample('3T').max()
        df3 = df_kosdaq['low'].resample('3T').min()
        df4 = df_kosdaq['close'].resample('3T').last()
        df5 = df_kosdaq['volume'].resample('3T').sum()

        df = pd.concat([df1, df2, df3, df4, df5], axis=1)
        # 결측치 데이터 삭제
        df = df.dropna()
        df['5이평'] = df['close'].rolling(window=5).mean()
        df['20이평'] = df['close'].rolling(window=20).mean()
        print('3분봉', df)
        self.trading(df)

    def trading(self, df):
        df['golden_cross'] = df['5이평'] > df['20이평']
        df['dead_cross'] = df['20이평'] > df['5이평']
        hold = False
        buy_price = None
        sell_price = None
        df_deal = pd.DataFrame(columns=['일자', '매수가', '매도가', '순이익', '순이익률'])

        for idx in df.index:
            if df['golden_cross'] and (not hold):
                buy_price = df.at[idx, 'close']  # 골든크로스가 발생한 봉의 종가에 매수하는 것으로 함.
                hold = True

            if df['dead_cross'] and hold:
                sell_price = df.at[idx, 'close'] # 골든크로스가 발생한 봉의 종가에 매도하는 것으로 함.
                hold = False
                profit = sell_price - buy_price
                df_deal.loc[len(df_deal)] = [idx.strftime("%Y%m%d"),
                                             buy_price,
                                             sell_price,
                                             profit,
                                             round((profit / buy_price) * 100, 2)
                                             ]


            if idx == df.index.values[-1] and hold:
                sell_price = df.at[idx, 'close']  # 종가를 기준으로 평가익을 계산
                profit = sell_price - buy_price
                hold = False
                df_deal.loc[len(df_deal)] = [idx.strftime("%Y%m%d"),
                                             buy_price,
                                             sell_price,
                                             profit,
                                             round((profit / buy_price) * 100, 2)
                                             ]

        # drawchart = DrawChart(df[20:60])


class DrawChart:
    def __init__(self, df):
        # super().__init__()
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

        ax1.plot(x_axes, df['5이평'], color='red', linewidth=2)
        ax1.plot(x_axes, df['20이평'], color='yellow', linewidth=2)

        candlestick2_ohlc(ax1, df['open'], df['high'], df['low'],
                          df['close'], width=0.8,
                          colorup='r', colordown='b')

        ax1.legend(['5이평', '20이평'])
        ax1.tick_params(axis='x', top=False, bottom=False, labeltop=False, labelbottom=False, width=0.2, labelsize=11)
        ax1.grid(True, which='major', color='gray', linewidth=0.2)

        ax2.bar(x_axes, df['volume'])
        ax2.set_xticks(range(0, len(df.index), 5))
        ax2.set_xticks(x_axes, minor=True)
        name_list = [v.strftime("%y%m%d") for i, v in enumerate(df.index)]
        name_list = [name_list[i] for i in range(0, len(df.index), 5)]
        ax2.set_xticklabels(name_list, rotation=90)

        plt.show()


if __name__ == '__main__':
    deal = GoldenCrossDeal()
    app = QApplication(sys.argv)
    # drawchart = DrawChart()
    # drawchart.show()
    app.exec_()

