import datetime
import sqlite3
import time
import pandas as pd
import mplfinance as mpf
import numpy as np
from kiwoom import Kiwoom

DB_KOSDAQ_DAY = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(day).db"
DB_KOSDAQ_MIN = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(1min).db"

volume_multiple = [1, 2, 3, 5, 10]
avrg_volume_period = [20, 40, 60, 120]
bandWidth_ratio = [1.2, 1.5, 2.0, 3.0]
max_min_ratio = [0.1, 0.2, 0.3, 0.5]
goal_ratio = [1.03, 1.04, 1.05, 1.06, 1.07, 1.1]
trailing_stop_price = [1, 1.05, 1.06, 1.07, 1.08, 1.10]
trailing_stop_ratio = [0.01, 0.02, 0.03]


class BollingerTesting:
    def __init__(self):
        self.df_day = pd.DataFrame()
        self.df_min = pd.DataFrame()
        self.df_kosdaq_jisu = pd.DataFrame()
        self.start = None
        self.end = None
        self.buy_price = 0
        self.sell_price = 0
        self.count = 0

        # self.df_trading = pd.DataFrame(columns=['매수가', '매도가', '순수익', '밴드상단'])
        self.df_deal = pd.DataFrame(columns=['종목번호', '체결시간', '매수가', '매도가', '순이익', '순이익률',
                                             '직전V평균', 'V증가율', '밴드상단', '고가', '종가',
                                             '돌파V', '돌파V배율', '주가상승률', '지수상승률',
                                             ])
        """
        kiwoom = Kiwoom()
        df_kosdaq_jisu = kiwoom.block_request('opt20006', 업종코드='101', 기준일자='20210930', output='업종일봉조회', next=0)
        df_kosdaq_jisu = df_kosdaq_jisu[['일자', '시가', '고가', '저가', '현재가', '거래량', '거래대금']]
        df_kosdaq_jisu.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        df_kosdaq_jisu = df_kosdaq_jisu.reset_index(drop=True).set_index('date')
        df_kosdaq_jisu = df_kosdaq_jisu.astype(int)

        con = sqlite3.connect("market_jisu.db")
        df_kosdaq_jisu.to_sql('kosdaq_jisu', con, if_exists='replace')
        con.commit()
        con.close()
        """

        con = sqlite3.connect("market_jisu.db")
        self.df_kosdaq_jisu = pd.read_sql("SELECT * FROM kosdaq_jisu", con, index_col='date', parse_dates='date')
        self.df_kosdaq_jisu['익일시가'] = self.df_kosdaq_jisu['open'].shift(-1)
        # print('코스닥지수\n', self.df_kosdaq_jisu)
        con.close()

        con = sqlite3.connect(DB_KOSDAQ_DAY)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_list = [v[0] for v in cur.fetchall()]
        con.close()

        self.startTrader(table_list)
        print(f"순이익 {self.df_deal['순이익'].sum()} 순이익률 "
              f"{round(self.df_deal['순이익'].sum() / self.df_deal['매수가'].sum() * 100, 2)}")

        self.df_deal['체결시간'] = self.df_deal['체결시간'].apply(lambda _: datetime.datetime.strftime(_, "%Y%m%d%H%m"))
        con = sqlite3.connect('bollinger04.db')
        self.df_deal.to_sql('bollinger_deal', con, if_exists='replace', index=False)
        con.commit()
        con.close()

    def startTrader(self, table_list):
        # # 전종목의 일봉데이터를 가져와서 볼린저밴드지표를 설정하고 시물레이션 시작
        starttime = time.time()
        for i, table in enumerate(table_list):
            con = sqlite3.connect(DB_KOSDAQ_DAY)
            # cur = con.cursor()
            df_day = pd.read_sql(f"SELECT * FROM '{table}' WHERE 일자 > 20210101 ORDER BY 일자", con,
                                 index_col='일자', parse_dates='일자')
            con.close()
            df_day.index.name = 'date'
            df_day.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
            df_day = df_day[['open', 'high', 'low', 'close', 'volume']]

            df_day['volume_mean20'] = round(df_day['volume'].rolling(window=20).mean(), 0)
            df_day['volume_ratio'] = round(df_day['volume'] / df_day['volume_mean20'], 1)
            df_day['종고저평균'] = round((df_day['close'] + df_day['high'] + df_day['low']) / 3, 0)
            df_day['밴드기준선'] = round(df_day['종고저평균'].rolling(window=20).mean(), 0)  # 밴드기준선
            df_day['밴드상단'] = round(df_day['밴드기준선'] + df_day['종고저평균'].rolling(window=20).std() * 2, 0)
            df_day['밴드하단'] = round(df_day['밴드기준선'] - df_day['종고저평균'].rolling(window=20).std() * 2, 0)
            df_day['밴드폭'] = round((df_day['밴드상단'] - df_day['밴드하단']) / df_day['밴드기준선'], 3)
            df_day['전일밴드폭'] = df_day['밴드폭'].shift(1)
            df_day['밴드돌파'] = df_day['high'] > df_day['밴드상단']
            df_day['익일시가'] = df_day['open'].shift(-1)

            # 종목별 대상기간을 설정하여 시물레이션 시작
            period = (df_day.index >= "2021-02-01") & (df_day.index <= "2021-09-30")
            print(f"시물레이션 중 {table}... {i + 1} / {len(table_list)}")
            self.code_trading(table, df_day.loc[period])  # 종목별로 날짜를 달리하여 여러개의 deal이 있을 수 있다.
            # if i == 10:
            #     break

            # self.drawPlot(df_day)
            # self.drawPlot2(df_day)
            # self.drawPlot3(df_day)
            # self.drawPlot4(df_day)
            # break

        # print("소요시간", time.time() - starttime)

    def code_trading(self, table, df_day):  # '돌파한 날만' filtering하면 안된다. ---> 돌파이전 상황도 중요.

        def _mean20_cal(data, chl_avrg_list):
            chl_list = chl_avrg_list.copy()
            chl_list.append(data)
            mean20 = round(np.mean(chl_list), 0)
            std20 = np.std(chl_list)
            upperB = round((mean20 + std20 * 2), 0)
            lowerB = round((mean20 - std20 * 2), 0)

            return mean20, upperB, lowerB

        for i, idx in enumerate(df_day.index):

            # 대상기간 전데이터는 제외 ---> 시작일부터 20일 전까지의 데이터는 볼린저밴드 계산을 위해서 필요.
            if idx < datetime.datetime.strptime('2021-03-01', '%Y-%m-%d'):
                continue

            # 고가돌파한 당일의 분봉데이터 가져와서 조건검색 ===> # 이조건에 해당하는 날짜가 여러개일 수 있다.
            if df_day.at[idx, 'high'] > df_day.at[idx, '밴드상단'] \
                    and df_day.at[idx, '밴드폭'] > df_day.at[idx, '전일밴드폭'] * 1.5:

                # -----------------------------
                start = time.time()

                self.count += 1
                chl_avrg_list = []  # 리스트 초기화
                xdate = idx.strftime("%Y%m%d")  # 날짜인덱스

                # 분봉차트에 일봉 볼린저밴드를 나타내기 위하여 일봉데이터의 19일치(1일전~20일전) 종고저데이터 리스트를 만듦.
                chl_avrg_list = df_day['종고저평균'].to_list()[i-19:i]   # 왜 i가 전일이 되는가 하면 슬라이싱할때 마지막 값은 포함하지 않기 때문임.

                # 분봉데이터 가져오기
                con = sqlite3.connect(DB_KOSDAQ_MIN)
                df_min = pd.read_sql(f"SELECT * FROM '{table}' WHERE 체결시간 LIKE '{xdate}%' ORDER BY 체결시간", con,
                                     index_col='체결시간', parse_dates='체결시간')
                con.close()
                df_min.index.name = 'date'
                df_min.columns = ['close', 'open', 'high', 'low', 'volume']
                df_min = df_min[['open', 'high', 'low', 'close', 'volume']]
                # -----------------------------------------------
                df_min['cum_volume'] = df_min['volume'].cumsum()
                df_min['volume_ratio'] = \
                    df_min['cum_volume'].apply(lambda x: round(x / df_day.at[idx, 'volume_mean20'], 1))
                df_min['highest'] = df_min['high'].cummax()
                df_min['lowest'] = df_min['low'].cummin()
                df_min['종고저평균'] = (df_min['highest'] + df_min['lowest'] + df_min['close']) / 3
                df_min['day_mean20'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[0])
                df_min['day_upperB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[1])
                df_min['day_lowerB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[2])
                df_min['day_bandWidth'] = (df_min['day_upperB'] - df_min['day_lowerB']) / df_min['day_mean20']
                df_min['next_open'] = df_min['open'].shift(-1)
                # print('분봉\n', df_min)

                position, buy_price, sell_price = False, 0, 0
                for mi, m_idx in enumerate(df_min.index):
                    # 매수는 하루에 한번뿐이다. 한번하면 stop
                    if (df_min.at[m_idx, 'close'] > df_min.at[m_idx, 'day_upperB']) \
                            and (df_min.at[m_idx, 'day_bandWidth'] > df_day.at[idx, '전일밴드폭'] * 1.5)\
                            and (not position):

                        buy_price = df_min.at[m_idx, 'close']
                        position = True
                        sell_price = df_day.at[idx, '익일시가']

                        profit = sell_price - buy_price
                        profit_per = round(profit / buy_price * 100, 2)
                        # print('deal', table, m_idx, buy_price, sell_price, '순손익', profit)

                        juga_ratio = round((df_day.at[idx, '익일시가'] - df_day.at[idx, 'close']) / df_day.at[idx, 'close']
                                           * 100, 2)
                        df_kosdaq = self.df_kosdaq_jisu.loc[self.df_kosdaq_jisu.index == idx]
                        jisu_ratio = round((df_kosdaq.at[idx, '익일시가'] - df_kosdaq.at[idx, 'close']) /
                                           df_kosdaq.at[idx, 'close'] * 100, 2)
                        self.df_deal.loc[len(self.df_deal)] = [table, m_idx, buy_price, sell_price,
                                                               profit, profit_per,
                                                               df_day.at[idx, 'volume_mean20'],
                                                               df_day.at[idx, 'volume_ratio'],
                                                               df_day.at[idx, '밴드상단'], df_day.at[idx, 'high'],
                                                               df_day.at[idx, 'close'],
                                                               df_min.at[m_idx, 'cum_volume'],
                                                               df_min.at[m_idx, 'volume_ratio'],
                                                               juga_ratio, jisu_ratio,
                                                               ]
                        break   # 첫돌파만 매수, 나머지는 pass

#  bollinger_deal DB애서 data를 가져와서 tableWidget 출력 및 그래프 출력
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import uic
import mplfinance as mpf
# form_class =


# class PointWindow(QMainWindow, form_class):
class PointWindow(QMainWindow):
    def __init__(self):
        super(PointWindow, self).__init__()
        con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/backtest/bollinger04.db")
        df = pd.read_sql("SELECT * FROM bollinger_deal", con)
        # df = df[]
        column_count = len(df.columns)
        row_count = len(df)
        self.setGeometry(100, 100, 1800, 900)
        self.table = QTableWidget(self)
        self.table.setGeometry(0, 0, 1790, 880)

        self.table.setRowCount(row_count)
        self.table.setColumnCount(column_count)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalHeaderLabels(df.columns)

        row = 0
        for idx, value in df.items():
            print(idx, value[0], type(idx[0]))
            input()

            # for col in range(len(df.columns)):
            #     self.table.setItem(row, col, QTableWidgetItem(str(value[col])))
            #     print('columns0', df.columns[0])
            #     print('------------')
            #     print(item)
            # if idx == 10:
            #     break
            # row += 1
            # self.show()


    def drawPlot(self, df_day):
        colorSet = mpf.make_marketcolors(up='tab:red', down='tab:blue', volume='tab:blue')
        s = mpf.make_mpf_style(base_mpf_style='default', marketcolors=colorSet)

        adp = mpf.make_addplot(df_day[['밴드상단', '밴드기준선', '밴드하단']])
        mpf.plot(df_day, type='candle', volume=True, title='DAY_CHART',
                 addplot=adp, style=s, figscale=2.4, tight_layout=True)

    def drawPlot2(self, df_day):
        fig = mpf.figure(style='default', figsize=(7, 8))
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)
        mpf.plot(df_day, ax=ax1, volume=ax2)
        fig.canvas.mpl_connect("button_press_event", self.clicked_graph)  # <= 이렇게 하면 마우스버튼을 클릭하면 동작하게 된다.
        mpf.show()

    def drawPlot3(self, df_day):
        fig = mpf.figure(figsize=(12, 8))
        ax1 = fig.add_subplot(2, 2, 1, style='yahoo')
        ax2 = fig.add_subplot(2, 2, 2, style='blueskies')

        s = mpf.make_mpf_style(base_mpl_style='fast', base_mpf_style='nightclouds')
        ax3 = fig.add_subplot(2, 2, 3, style=s)
        ax4 = fig.add_subplot(2, 2, 4, style='starsandstripes')

        mpf.plot(df_day, ax=ax1, axtitle='blueskies', xrotation=15)
        mpf.plot(df_day, type='candle', ax=ax2, axtitle='yahoo', xrotation=15)
        mpf.plot(df_day, ax=ax3, type='candle', axtitle='nightclouds')
        mpf.plot(df_day, type='candle', ax=ax4, axtitle='starsandstripes')
        fig.canvas.mpl_connect("button_press_event", self.clicked_graph)  # <= 이렇게 하면 마우스버튼을 클릭하면 동작하게 된다.
        mpf.show()

    def drawPlot4(self, df_day):
        fig = mpf.figure(style='blueskies', figsize=(7, 8))
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = ax1.twinx()
        ax4 = fig.add_subplot(2, 1, 2)
        ap = mpf.make_addplot(df_day[['밴드상단', '밴드하단']], ax=ax2, ylabel='Bollinger Bands')
        mpf.plot(df_day, ax=ax1, volume=ax4, addplot=ap, xrotation=10, type='candle')
        fig.canvas.mpl_connect("button_press_event", self.clicked_graph)  # <= 이렇게 하면 마우스버튼을 클릭하면 동작하게 된다.
        fig.canvas.mpl_connect("fig_leave_event", self.notify_event)
        fig.canvas.mpl_connect("motion_notify_event", self.notify_event)
        mpf.show()

    def clicked_graph(self, event):
        # 여기서 일봉차트의 클릭한 날짜의 그래프를 그린다.
        print('event', event)

    def notify_event(self, event):
        if event.xdata == None:
            print("None")
            return
        print('notify', event)

    def hogaUnit(self):

        table_list = self.sqlTableList(DB_KOSDAQ_DAY)
        print('table_list', table_list)

    def bringDB(self, sqlDB, table):
        con =sqlite3.connect(sqlDB)
        self.df_day = pd.read_sql(f"SELECT * FROM '{table}' WHERE ")


if __name__ == '__main__':
    # btest = BollingerTesting()
    app = QApplication(sys.argv)
    pwindow = PointWindow()
    app.exec_()
