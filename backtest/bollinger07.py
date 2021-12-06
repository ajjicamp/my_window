import os
import sys
import sqlite3
import pandas as pd
import datetime
import time
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtGui, uic
import mplfinance as mpf
from mplfinance.original_flavor import candlestick2_ohlc
from matplotlib import gridspec
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import logging
from multiprocessing import Pool, Process, Lock

plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False  # 한글 폰트 사용시 마이너스 폰트 깨짐 해결


PATH ="C:/Users/USER/PycharmProjects/my_window/backtest"
DB_KOSDAQ_DAY = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(day).db"
DB_KOSDAQ_MIN = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(1min).db"
DB_DEAL_DETAILS = f"{PATH}/bollinger07.db"
DB_DEAL_PROFIT = f"{PATH}/deal_profit07.db"

multiple = 1.2
max_width = 0.2


class BollingerTrader:
    def __init__(self):
        if os.path.exists(DB_DEAL_DETAILS):
            os.remove(DB_DEAL_DETAILS)

        if os.path.exists(DB_DEAL_PROFIT):
            os.remove(DB_DEAL_PROFIT)

        # sqlite3 db에서 코스닥 일봉데이터의 table_list를 가져와서 list에 저장
        con = sqlite3.connect(DB_KOSDAQ_DAY)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        self.table_list = [v[0] for v in cur.fetchall()]
        con.close()

        self.startTrader(self.table_list)

    def startTrader(self, table_list):
        self.df_deal = pd.DataFrame(columns=['종목번호', '매수시간', '매수가', '매도시간', '매도가', '순이익', '순이익률',
                                             '최고가', '최저가', '익일시가'])
        self.df_dealProfit = pd.DataFrame(columns=['밴드폭확장률', '매수가합계', '순이익합계', '순이익률'])

        # DB에서 종목별 일봉데어터를 가져와서 필요한 컬럼항목 추가하고 매수조건 필터링
        start_time = time.time()
        for i, table in enumerate(table_list):
            con = sqlite3.connect(DB_KOSDAQ_DAY)
            df_day = pd.read_sql(f"SELECT * FROM '{table}' WHERE 일자 >= 20201001 and 일자 <= 20211005 ORDER BY 일자", con,
                                 index_col='일자', parse_dates='일자')
            con.close()
            if len(df_day) == 0:
                continue    # 대상일봉데이터가 없는 경우는 아래 작업 취소하고 새로시작
            df_day.index.name = 'date'
            df_day.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
            df_day = df_day[['open', 'high', 'low', 'close', 'volume']]
            df_day['index'] = df_day.index.values
            df_day['before_index'] = df_day['index'].shift(1)
            # df_day['before_index'] = df_day.index.shift(freq=1)
            # print(df_day['before_index'])
            # input()
            # 밴드폭계산시 20일째날은 고가기준으로 밴드폭을 계산하여 종가기준시 빠지는 사례가 없도록 하자.
            # 종가밴드 설정
            df_day['volume_mean20'] = round(df_day['volume'].rolling(window=20).mean())
            df_day['volume_ratio'] = round(df_day['volume'] / df_day['volume_mean20'], 1)  # 거래량 증가율(직전평균대비)
            df_day['종고저평균'] = round((df_day['close'] + df_day['high'] + df_day['low']) / 3)
            df_day['밴드기준선'] = round(df_day['종고저평균'].rolling(window=20).mean())  # 밴드기준선
            df_day['밴드상단'] = round(df_day['밴드기준선'] + df_day['종고저평균'].rolling(window=20).std(ddof=0) * 2)
            df_day['밴드하단'] = round(df_day['밴드기준선'] - df_day['종고저평균'].rolling(window=20).std(ddof=0) * 2)
            df_day['밴드폭'] = round((df_day['밴드상단'] - df_day['밴드하단']) / df_day['밴드기준선'], 3)
            df_day['밴드돌파'] = df_day['high'] > df_day['밴드상단']
            df_day['전일밴드폭'] = df_day['밴드폭'].shift(1)
            df_day['전일밴드상단'] = df_day['밴드상단'].shift(1)
            df_day['밴드확장률OK'] = df_day['밴드폭'] > df_day['전일밴드폭'] * multiple
            df_day['밴드120폭최고'] = df_day['밴드폭'].shift(1).rolling(window=120).max()
            df_day['밴드120폭최저'] = df_day['밴드폭'].shift(1).rolling(window=120).min()
            df_day['밴드폭120하위'] = df_day['밴드폭'] < ((df_day['밴드120폭최고'] - df_day['밴드120폭최저']) * max_width)

            # 19일간은 종고저평균을 사용하고 20일째(당일)만 시가를 기준으로 밴드 설정  # 이건 시리즈의 리스트(즉, index + value)
            df_day['종고저19리스트'] = list(df_day['종고저평균'].shift(1).rolling(window=19))
            df_day['시가리스트'] = list(df_day['open'].rolling(window=1))

            def open_band(open_, x):
                sum_list = list(x.values) + list(open_.values)
                mean20 = np.mean(sum_list)
                std20 = np.std(sum_list)
                # print(table, type(x.values), x.values, open_.values, sum_list, mean20, std20)
                return mean20, std20

            df_day['시가밴드기준선'] = df_day.apply(lambda x: open_band(x['시가리스트'], x['종고저19리스트'])[0], axis=1)
            df_day['시가밴드std'] = df_day.apply(lambda x: open_band(x['시가리스트'], x['종고저19리스트'])[1], axis=1)
            df_day['시가밴드상단'] = df_day['시가밴드기준선'] + df_day['시가밴드std'] * 2
            df_day['시가밴드하단'] = df_day['시가밴드기준선'] - df_day['시가밴드std'] * 2
            df_day['시가밴드폭'] = (df_day['시가밴드상단'] - df_day['시가밴드하단']) / df_day['시가밴드기준선']
            df_day['시가밴드돌파'] = df_day['open'] > df_day['시가밴드상단']
            df_day['시가밴드확장률OK'] = df_day['시가밴드폭'] > df_day['전일밴드폭'] * multiple

            df_day['익일시가'] = df_day['open'].shift(-1)
            df_day['전일종가'] = df_day['close'].shift(1)

            # 시초가밴드 설정
            # print(f"시물레이션 중 {table}... {i + 1} / {len(self.table_list)}")
            self.codeTrading(table, df_day)  # 종목별로 날짜를 달리하여 여러개의 deal이 있을 수 있다.
        print('최종deal결과', self.df_deal)
        con = sqlite3.connect(DB_DEAL_DETAILS)
        table_name = f"deal_{str(round(multiple, 1))}"
        # table_name = 'boll_1.1'

        self.df_deal['매수시간'] = self.df_deal['매수시간'].apply(lambda _:
                                                          _.replace('-', '').replace(' ', '').replace(':', '')[:-2])
        self.df_deal.to_sql(table_name, con, if_exists='replace', index=False)
        con.close()

        profit_sum = self.df_deal['순이익'].sum()
        buy_sum = self.df_deal['매수가'].sum()
        profit_rate_sum = profit_sum / buy_sum * 100
        self.df_dealProfit.loc[len(self.df_dealProfit)] = (f"deal_{str(round(multiple, 1))}",
                                                           profit_sum, buy_sum, profit_rate_sum)
        con = sqlite3.connect(DB_DEAL_PROFIT)
        table_name = 'deal_summary'
        self.df_dealProfit.to_sql(table_name, con, if_exists='append', index=False)
        con.close()
        print(profit_rate_sum)

        print('소요시간', time.time() - start_time)

    def codeTrading(self, table, df_day):
        buy_cond_open = df_day['시가밴드돌파'] & df_day['시가밴드확장률OK'] & df_day['밴드폭120하위']\
                        & (df_day['전일밴드폭'] != 0) & (df_day.index >= '2021-03-01') & (df_day.index <= '2021-09-30')
        buy_cond = df_day['밴드돌파'] & df_day['밴드확장률OK'] & df_day['밴드폭120하위']\
                   & (df_day['전일밴드폭'] != 0) & (df_day.index >= '2021-03-01') & (df_day.index <= '2021-09-30')
        # df_day = df_day[buy_cond_open]
        df_day = df_day[buy_cond_open | buy_cond]
        print('필터링 df', table, len(df_day))
        count = 0
        for i, idx in enumerate(df_day.index):  # 10/5, 5/1, 8/31 등의 필터링된 일봉데이터 여러개
            position = False
            buy_price = None
            sell_price = None
            profit = None
            buy_time = None
            deal_not_open = False

            # 분봉데이터 설정
            df_min = self.set_minute_data(table, df_day, i, idx)
            # 전일동시간대 거래량체크하기 위하여 전날의 분봉도 가져옴.
            ydate = df_day.at[idx, 'before_index'].strftime("%Y%m%d")  # 날짜인덱스
            con = sqlite3.connect(DB_KOSDAQ_MIN)
            df_min_before = pd.read_sql(f"SELECT 체결시간, 거래량 FROM '{table}' WHERE 체결시간 LIKE '{ydate}%' ORDER BY 체결시간",
                                        con, index_col='체결시간', parse_dates='체결시간')
            con.close()
            df_min_before['누적거래량'] = df_min_before['거래량'].cumsum()
            df_min['position'] = 0

            if df_day.at[idx, '시가밴드돌파'] & df_day.at[idx, '시가밴드확장률OK'] & \
                    (df_day.at[idx, '전일밴드폭'] != 0):

                buy_price = df_day.at[idx, 'open']
                buy_time = idx.strftime("%Y-%m-%d") + ' 09:00:00'
                df_min.loc[buy_time, 'position'] = 1
                position = True

            if not position:
                cond1 = df_min['밴드돌파'] & df_min['밴드확장률OK'] & df_min['밴드폭120하위']
                data = df_min.loc[cond1]

                if len(data) != 0:
                    buy_price = data['close'][0]
                    buy_time = str(data.index.to_list()[0])
                    # print(buy_time, type(buy_time))
                    df_min.loc[buy_time, 'position'] = 1
                    position = True
                    deal_not_open = True

            if position:
                # trailing stop loss 설정 ; 매수후 최고가에서 1% 하락시 매도
                # 매수후 누적최고가 산출
                df_min['highest'] = df_min.loc[df_min['position'].cumsum().astype('bool'), 'high'].cummax()
                df_min['sell_signal'] = df_min['low'] < df_min['highest'] * 0.99

                sell_price_df = df_min.loc[df_min['sell_signal']]
                # print('sell_price_df', sell_price_series)
                if len(sell_price_df) != 0:
                    # sell_price = sell_price_df['close'][0]
                    sell_price = df_min['highest'][0] * 0.99 * 0.995  # 손절가에서 수수료, 세금 및 슬리피지 합하여 0.5% 공제
                    sell_time = sell_price_df.index[0].strftime("%Y%m%d%H%M")
                else:
                    sell_price = df_day.at[idx, '익일시가']
                    # 'i + 1'은 연속된 날짜의 뒷날이 아니다. 필터된 날 중 다음날이다.
                    sell_time = '익일시가'

                # print(f"{table} \n매수시간: {buy_time} \n매수가{buy_price} \nsell_price_df\n {sell_price_df} \n매도가: {sell_price}")
                # input()

                # if deal_not_open:
                #     print('길이비교', len(df_min), len(df_min['highest']), df_min['highest'], df_min['sell_signal'])
                #     input()


                # print('sell_pirce', sell_price)

                after_highest = df_min.loc[df_min['position'].cumsum().astype('bool'), 'high'].max()
                after_lowest = df_min.loc[df_min['position'].cumsum().astype('bool'), 'low'].min()
                # after_highest_index = df_min.loc[df_min['position'].cumsum().astype('bool'), 'high'].idxmax()
                # print('highest******\n', after_highest, after_highest_index)
                profit = sell_price - buy_price
                profit_rate = profit / buy_price * 100

                self.df_deal.loc[len(self.df_deal)] = [table, buy_time, buy_price, sell_time, sell_price, profit,
                                                       round(profit_rate, 2), after_highest, after_lowest,
                                                       df_day.at[idx, '익일시가']]

    def set_minute_data(self, table, df_day, i, idx):
        chl_avrg_list, chl_list = None, None
        def _mean20_cal(data, chl_avrg_list):
            # 일봉데이터의 19일치 종고저평균데이터
            chl_list = chl_avrg_list.copy()
            # 위 데어터에 분봉의 일중 실시간 데이터를 추가(하루데이터).
            chl_list.append(data)
            # 위 최종 자료를 기준으로 20일 평균 계산(이건 밴드기준선이기도 함)
            mean20 = round(np.mean(chl_list))
            # 표준편차, 밴드상단, 밴드하단 계산
            std20 = np.std(chl_list)
            upperB = round((mean20 + std20 * 2))
            lowerB = round((mean20 - std20 * 2))
            return mean20, upperB, lowerB

        xdate = idx.strftime("%Y%m%d")  # 날짜인덱스

        # 분봉차트에 일봉 볼린저밴드를 나타내기 위하여 일봉데이터의 19일치(1일전~20일전) 종고저데이터 리스트를 만듦.
        chl_avrg_list = []  # 리스트 초기화  # 초기화하지 않으면 계속 누적됨.
        chl_avrg_list = df_day['종고저평균'].to_list()[i - 19:i]  # 왜 i가 전일이 되는가 하면 슬라이싱할때 마지막 값은 포함하지 않기 때문임.

        # 분봉데이터 가져오기
        con = sqlite3.connect(DB_KOSDAQ_MIN)
        df_min = pd.read_sql(f"SELECT * FROM '{table}' WHERE 체결시간 LIKE '{xdate}%' ORDER BY 체결시간", con,
                             index_col='체결시간', parse_dates='체결시간')
        con.close()

        df_min.index.name = 'date'
        df_min.columns = ['close', 'open', 'high', 'low', 'volume']
        df_min = df_min[['open', 'high', 'low', 'close', 'volume']]
        # -----------------------------------------------
        df_min['next_open'] = df_min['open'].shift(-1)
        df_min['cum_volume'] = df_min['volume'].cumsum()
        df_min['volume_ratio'] = \
            df_min['cum_volume'].apply(lambda x: round(x / df_day.at[idx, 'volume_mean20'], 1))
        df_min['highest'] = df_min['high'].cummax()
        df_min['lowest'] = df_min['low'].cummin()
        df_min['종고저평균'] = (df_min['highest'] + df_min['lowest'] + df_min['close']) / 3

        # 일봉 볼린저밴드 계산
        df_min['day_mean20'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[0])
        df_min['day_upperB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[1])
        df_min['day_lowerB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[2])
        df_min['day_bandWidth'] = (df_min['day_upperB'] - df_min['day_lowerB']) / df_min['day_mean20']

        df_min['밴드돌파'] = df_min['close'] > df_min['day_upperB']
        df_min['밴드확장률OK'] = df_min['day_bandWidth'] > df_day.at[idx, '전일밴드폭'] * 1.1
        df_min['밴드폭120하위'] = df_min['day_bandWidth'] < \
                               ((df_day.at[idx, '밴드120폭최고'] - df_day.at[idx, '밴드120폭최저']) * max_width)

        return df_min


# class PointWindow(QMainWindow, form_class):
class DealProfit(QMainWindow):
    def __init__(self):
        super(DealProfit, self).__init__()
        # db_name = DB_DEAL_PROFIT
        table_name = 'deal_summary'
        con = sqlite3.connect(DB_DEAL_PROFIT)
        # print('dbname', db_name)
        df = pd.read_sql(f"SELECT * FROM {table_name}", con)
        df = df.astype({'순이익합계': 'int'})
        con.close()
        # print('df', df)

        column_count = len(df.columns)
        row_count = len(df)
        self.setGeometry(100, 100, 950, 1000)
        self.setWindowTitle('볼린저밴드 Width와 상단밴드 돌파를 이용한 Deal Profit 분석')
        self.table = QTableWidget(self)
        self.table.setGeometry(0, 0, 950, 1000)

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
        # print('selftable_모체객체', self.table)
        self.table.cellClicked.connect(self.deal_profit_cell_clicked)

    def deal_profit_cell_clicked(self, row, col):
        # db_name = DB_DEAL_DETAILS
        table_name = self.table.item(row, 0).text()
        # print('table_name', table_name)

        # todo self변수로 넣어야 작동한다. 즉, 단순하게 pointwindow로 해서는 안된다.
        # self.pointwindow = PointWindow(db_name, table_name)
        self.pointwindow = PointWindow(DB_DEAL_DETAILS, table_name)
        self.pointwindow.show()


class PointWindow(QWidget):
    def __init__(self, db_name, table_name):
        super(PointWindow, self).__init__()
        # print('359진입')
        self.bWidthMultiple = float(table_name[5:])
        # print('multiple', self.bWidthMultiple)

        # 종목이름을 code_name 텍스트파일에서 읽어와서 list에 저장  ==> 향후에는 utility.py에서 읽어옴.
        self.code_name = {}
        with open(f"{PATH}/code_name.txt", 'r') as f:

            while True:
                line = f.readline()
                code = line[:6]
                name = line[7:].strip('\n')
                self.code_name[code] = name
                if not line:
                    break
            # print('code_name', self.code_name)
        con = sqlite3.connect(db_name)
        # print('dbname', db_name)
        df = pd.read_sql(f"SELECT * FROM '{table_name}'", con)
        con.close()
        # df['0900'] = df['매수시간'].apply(lambda x: x[8:] == '0900')
        # df = df[df['0900']]

        column_count = len(df.columns)
        row_count = len(df)
        self.setGeometry(100, 100, 1800, 900)
        self.setWindowTitle(f'볼린저밴드 Deal 분석 확장배수: {self.bWidthMultiple}')
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
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(1, 130)

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
            code = self.table.item(row, 0).text()
            # print('row', row)
            deal_time = self.table.item(row, 1).text()  # 202109160909
            buy_price = float(self.table.item(row, 2).text())
            sell_price = float(self.table.item(row, 4).text())

            df_2 = self.get_day_data(code, deal_time)
            df_day = df_2[0]  # df_2 ; (df_day, df_jisu) tuple
            df_jisu = df_2[1]
            self.fig = None
            self.drawDayChart(code, df_day, deal_time, buy_price, sell_price, df_jisu)  # tdate ;  2021-09-16 형식

        # self.table.cellClicked.connect(self.cell_clicked)
        self.table.cellClicked.connect(cell_clicked)
        # print('self_table 객체', self.table)
        self.show()

    def get_day_data(self, code, deal_time):

        # 일봉차트 데이터 가져오기
        tdate = pd.to_datetime(deal_time[:8])
        start = tdate - datetime.timedelta(days=160)
        end = tdate + datetime.timedelta(days=40)
        start = str(start.strftime("%Y%m%d"))
        end = str(end.strftime("%Y%m%d"))

        print('start', start, type(start), end)

        con = sqlite3.connect(DB_KOSDAQ_DAY)
        df_day = pd.read_sql(f"SELECT * FROM '{code}' WHERE 일자 > {start} and 일자 <= {end} "
                             f"ORDER BY 일자", con, index_col='일자', parse_dates='일자')
        con.close()

        df_day.index.name = 'date'
        df_day.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
        df_day = df_day[['open', 'high', 'low', 'close', 'volume', 'amount']]

        df_day['전일종가'] = df_day['close'].shift(1)
        df_day['거래량20'] = round(df_day['volume'].rolling(window=20).mean(), 0).shift(1)  # todo 하루전 기준이라야 함.

        # bollinger band 추가
        df_day['종고저평균'] = round((df_day['close'] + df_day['high'] + df_day['low']) / 3, 0)
        df_day['밴드기준선'] = round(df_day['종고저평균'].rolling(window=20).mean(), 0)  # 밴드기준선
        df_day['밴드상단'] = round(df_day['밴드기준선'] + df_day['종고저평균'].rolling(window=20).std() * 2, 0)
        df_day['밴드하단'] = round(df_day['밴드기준선'] - df_day['종고저평균'].rolling(window=20).std() * 2, 0)
        df_day['밴드폭'] = round((df_day['밴드상단'] - df_day['밴드하단']) / df_day['밴드기준선'], 3)
        df_day['전일밴드폭'] = df_day['밴드폭'].shift(1)

        # 지수차트 가져오기
        con = sqlite3.connect(f"{PATH}/market_jisu.db")
        df_jisu = pd.read_sql(f"SELECT * FROM kosdaq_jisu WHERE date > {start} and date <= {end} "
                              f"ORDER BY date", con, index_col='date', parse_dates='date')
        con.close()

        print('df_day, df_jisu', df_day, df_jisu)

        return df_day, df_jisu

    # 구 mpl_finace를 이용하여 그리는 candle차트
    def drawDayChart(self, code, df_day, deal_time, buy_price, sell_price, df_jisu):
        # if not self.fig == None:
        plt.close()
        # plt.show()

        # 차트가 있으면 지우고 새로 그린다.
        tdate = pd.to_datetime(deal_time[:8])
        # print('tdate', tdate)
        fig = plt.figure(figsize=(15, 9))
        gs = gridspec.GridSpec(nrows=2,  # row 몇 개
                               ncols=1,  # col 몇 개
                               height_ratios=[3, 1],
                               width_ratios=[20]
                               )
        fig.subplots_adjust(left=0.10, bottom=0.10, right=0.95, top=0.95, wspace=0.1, hspace=0.01)
        # fig.subplots_adjust(left=0.10, bottom=0.10, right=0.95, top=0.95, wspace=0.1, hspace=1.01)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        candlestick2_ohlc(ax1, df_day['open'], df_day['high'], df_day['low'],
                          df_day['close'], width=0.8,
                          colorup='r', colordown='b')

        day_list = range(len(df_day.index))
        # print('day_list', day_list, day_list[0], day_list[-1])

        ax1.plot(day_list, df_day['밴드상단'], color='r', linewidth=2)
        ax1.plot(day_list, df_day['밴드기준선'], color='y', linewidth=2)
        ax1.plot(day_list, df_day['밴드하단'], color='b', linewidth=2)

        # 코스닥지수차트 그리기
        # ax11 = ax1.twinx()
        # ax11.plot(day_list, df_jisu['close'], color='y', linewidth=1.0, linestyle='solid', alpha=1.0)

        candlestick2_ohlc(ax1, df_day['open'], df_day['high'], df_day['low'],
                          df_day['close'], width=0.8,
                          colorup='r', colordown='b')
        ax1.set_title(f"{self.code_name[code]}({code}) 일봉차트", fontsize=20)
        ax1.legend(['B밴드상단', 'B밴드기준선', 'B밴드하단'])
        # ax1 xticklable은 보이지 않도록 함.
        ax1.tick_params(axis='x', top=False, labeltop=False, labelbottom=False, width=0.2, labelsize=11)
        ax1.grid(True, which='major', color='gray', linewidth=0.2)

        ax2.bar(day_list, df_day['volume'])
        ax2.set_xticks(range(0, len(df_day.index), 5))
        ax2.set_xticks(day_list, minor=True)
        name_list = [v.strftime("%y%m%d") for i, v in enumerate(df_day.index)]
        name_list = [name_list[i] for i in range(0, len(df_day.index), 5)]
        ax2.set_xticklabels(name_list, rotation=90)

        ytick_ = [int(y / 1000) for y in df_day['volume']]
        ax2.set_yticklabels(ytick_)
        ax2.set_ylabel("거래량(단위:천)", color='green', fontdict={'size': 11})
        ax2.grid(True, which='major', color='gray', linewidth=0.2)

        # annotation 설정
        # x_ = [i for i, idx in enumerate(df_day.index) if idx.strftime("%Y-%m-%d") == tdate.strftime("%Y-%m-%d")][0]
        x_ = df_day.index.to_list().index(tdate)
        y_ = buy_price
        ax1.annotate(f'매수:{str(int(buy_price))}', (x_, y_), xytext=(x_ - 20, y_),
                     arrowprops=dict(facecolor='green', shrink=0.05, width=0.5, headwidth=5, alpha=0.7),
                     fontsize=12, bbox=dict(facecolor='r', alpha=0.2))
        y2_ = sell_price
        ax1.annotate(f'매도:{str(int(sell_price))}', (x_ + 1, y2_), xytext=(x_ + 10, y2_ * 1.05),
                     arrowprops=dict(facecolor='green', shrink=0.05, width=0.5, headwidth=5, alpha=0.7),
                     fontsize=12, bbox=dict(facecolor='b', alpha=0.2))


        def motion_notify_event(event):
            # print(ax1.texts[0], len(ax1.texts))
            # print(event.x, event.y)
            if len(ax1.texts) > 2:
                for txt in ax1.texts:
                    txt.set_visible(False)
            ax1.texts[0].set_visible(True)
            ax1.texts[1].set_visible(True)

            if event.inaxes == ax1:
                xv = round(event.xdata)
                if (xv < len(df_day)) and (event.ydata <= df_day['high'][xv]) and (event.ydata >= df_day['low'][xv]):
                    # fig.canvas.flush_events()
                    print('xv', xv)
                    close_1 = df_day['전일종가'][xv]
                    open_ = df_day['open'][xv]
                    high_ = df_day['high'][xv]
                    low_ = df_day['low'][xv]
                    close_ = df_day['close'][xv]

                    if xv >= 19:
                        text = f"일자     :{df_day.index[xv].strftime('%Y-%m-%d')}\n" \
                               f"시가     :{open_} ({round((open_ / close_1 - 1) * 100, 2)}%)\n" \
                               f"고가     :{high_} ({round((high_ / close_1 - 1) * 100, 2)}%)\n" \
                               f"저가     :{low_} ({round((low_ / close_1 - 1) * 100, 2)}%)\n" \
                               f"종가     :{close_} ({round((close_ / close_1 - 1) * 100, 2)}%)\n" \
                               f"거래량   :{df_day['volume'][xv]}\n" \
                               f"\n" \
                               f"[볼린저 밴드]\n" \
                               f"밴드상단   :{int(df_day['밴드상단'][xv])}\n" \
                               f"밴드기준선  :{int(df_day['밴드기준선'][xv])}\n" \
                               f"밴드하단   :{int(df_day['밴드하단'][xv])}"
                    else:
                        text = f"일자     :{df_day.index[xv].strftime('%Y-%m-%d')}\n" \
                               f"시가     :{open_} ({round((open_ / close_1 - 1) * 100, 2)}%)\n" \
                               f"고가     :{high_} ({round((high_ / close_1 - 1) * 100, 2)}%)\n" \
                               f"저가     :{low_} ({round((low_ / close_1 - 1) * 100, 2)}%)\n" \
                               f"종가     :{close_} ({round((close_ / close_1 - 1) * 100, 2)}%)\n" \
                               f"거래량   :{df_day['volume'][xv]}"

                    ylim = ax1.axis()
                    if event.ydata > ((ylim[3] + ylim[2]) / 2):
                        yv = df_day['low'][xv] - (ylim[3] - ylim[2]) * 3 / 10
                    else:
                        yv = df_day['high'][xv] * 1.00

                else:
                    text = ''
                    yv = event.ydata
                ax1.text(xv + 1.5, yv, text, bbox=dict(facecolor='white', alpha=1.0))
                fig.canvas.draw()

        fig.canvas.mpl_connect("motion_notify_event", motion_notify_event)

        def mouse_click_event(event):
            i = round(event.xdata)
            date = df_day.index[i].strftime("%Y%m%d")  # 2021-04-06 00:00:00 날짜type --> 20210406
            chl19 = df_day['종고저평균'].to_list()[i - 19:i]  # 왜 i가 전일이 되는가 하면 슬라이싱할때 마지막 값은 포함하지 않기 때문임.
            df_min = self.get_minute_data(code, date, df_day['거래량20'][i], chl19, df_day['전일밴드폭'][i])
            start = 0
            end = len(df_min) - 1
            # print('start, end', start, end)
            self.draw_minite_chart(df_min, code, date, buy_price, deal_time, start, end)
            # print('분봉날짜', date)

        fig.canvas.mpl_connect("button_press_event", mouse_click_event)
        plt.show()
        # fig.show()
        # print('축정보', ax1.axis()[2])

    def get_minute_data(self, code, date, volume20, chl19, BWidth_1):  # BWidth_1 ; 전일밴드폭
        print("전일밴드폭, volume20:", BWidth_1, volume20)
        con = sqlite3.connect(DB_KOSDAQ_MIN)
        df_min = pd.read_sql(f"SELECT * FROM '{code}' WHERE 체결시간 LIKE '{date}%' ORDER BY 체결시간",
                             con, index_col='체결시간', parse_dates='체결시간')
        con.close()

        df_min.index.name = 'date'
        df_min.columns = ['close', 'open', 'high', 'low', 'volume']
        df_min = df_min[['open', 'high', 'low', 'close', 'volume']]
        # -----------------------------------------------
        df_min['전봉종가'] = df_min['close'].shift(1)
        df_min['cum_volume'] = df_min['volume'].cumsum()
        if volume20 != 0:
            df_min['volume_ratio'] = \
                df_min['cum_volume'].apply(lambda x: round(x / volume20, 1))  # todo 여기수정필요
        else:
            df_min['volume_ratio'] = 0

        df_min['highest'] = df_min['high'].cummax()
        df_min['lowest'] = df_min['low'].cummin()
        df_min['종고저평균'] = (df_min['highest'] + df_min['lowest'] + df_min['close']) / 3

        # 함수 _mean20_cal()
        def _mean20_cal(data, chl19):
            # 일봉데이터의 19일치 종고저평균데이터
            chl_list = chl19.copy()
            # 위 데어터에 분봉의 일중 실시간 데이터를 추가(하루데이터).
            chl_list.append(data)
            # 위 최종 자료를 기준으로 20일 평균 계산(이건 밴드기준선이기도 함)
            mean20 = round(np.mean(chl_list))
            # 표준편차, 밴드상단, 밴드하단 계산
            std20 = np.std(chl_list)
            upperB = round((mean20 + std20 * 2))
            lowerB = round((mean20 - std20 * 2))
            return mean20, upperB, lowerB

        df_min['day_mean20'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl19)[0])
        df_min['day_upperB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl19)[1])
        df_min['day_lowerB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl19)[2])
        df_min['day_bandWidth'] = (df_min['day_upperB'] - df_min['day_lowerB']) / df_min['day_mean20']
        # 전날부터 소급하여 19일간의 데이터가 없으면 BWidth_1이 0가 된다.
        if BWidth_1 != 0:
            df_min['bWidth_ratio'] = round(df_min['day_bandWidth'] / BWidth_1, 2)
        else:
            df_min['bWidth_ratio'] = 0
        # df_min['next_open'] = df_min['open'].shift(-1)
        # print('df_min', df_min)

        return df_min
        # print(df_min)

    def draw_minite_chart(self, df_min, code, date, buy_price, deal_time, start, end, redraw=False):
        """
        :param df_min: 분봉데이터
        :param code: 종목변호
        :param date: 일봉차트에서 클릭한 날짜(문자형 210512 스타일)
        :param buy_price: 매수가
        :param deal_time: 문자형 2105120934
        :param start: df_min에 사용할 인덱싱 시작번호
        :param end: df_min에 사용할 인덱싱 끝번호
        :param redraw: bool 새로 그리면 True
        :return:
        """

        self.start = start
        self.end = end
        df_query = df_min.iloc[self.start: self.end]
        # print('df_query', df_query)
        fig = plt.figure(figsize=(15, 9))
        gs = gridspec.GridSpec(nrows=3,  # row 몇 개
                               ncols=1,  # col 몇 개
                               height_ratios=[1, 6, 2],
                               width_ratios=[20]
                               )
        # fig.subplots_adjust(left=0.10, bottom=0.10, right=0.95, top=0.95, wspace=0.1, hspace=0.01)
        fig.subplots_adjust(left=0.10, bottom=0.10, right=0.95, top=0.95, wspace=0.1, hspace=0.00)

        ax1 = fig.add_subplot(gs[1])
        ax2 = fig.add_subplot(gs[2], sharex=ax1)
        ax0 = fig.add_subplot(gs[0], sharex=ax1)

        min_list = range(len(df_query.index))
        print('min_list', min_list, min_list[0], min_list[-1], df_query['volume_ratio'])

        ax1.plot(min_list, df_query['day_upperB'], color='black', linewidth=1)

        candlestick2_ohlc(ax1, df_query['open'], df_query['high'], df_query['low'],
                          df_query['close'], width=0.8,
                          colorup='r', colordown='b')

        ax1.legend(['일봉B밴드상단'])
        ax1.tick_params(axis='x', top=False, bottom=False, labeltop=False, labelbottom=False, width=0.2, labelsize=11)
        ax1.grid(True, which='major', color='gray', linewidth=0.2)

        ax0.set_title(f"{self.code_name[code]} 분봉차트 ({date})", fontsize=20)
        print('bWidth', df_query['bWidth_ratio'])
        # if df_query['bWidth_ratio'] == None:
        ax0.plot(min_list, df_query['bWidth_ratio'], color='c', linewidth=1)
        ax0.axhline(y=self.bWidthMultiple, color='r', linewidth=0.5, label='bWidthMultipl')
        ax0.legend(['밴드상단확장률'])
        ax0.tick_params(axis='x', top=False, bottom=False, labeltop=False, labelbottom=False, width=0.2, labelsize=11)

        ax0.grid(True, which='major', color='gray', linewidth=0.2)

        ax2.bar(min_list, df_query['volume'])
        name_list = [v.strftime("%H:%M") for i, v in enumerate(df_query.index)]

        if not redraw:
            print('redraw=False')
            ax2.set_xticks(range(0, len(df_query.index), 5))
            ax2.set_xticks(min_list, minor=True)
            name_list = [name_list[i] for i in range(0, len(df_query.index), 5)]
        else:
            print("redraw=True")
            ax2.set_xticks(min_list)
        ax2.set_xticklabels(name_list, rotation=90)

        ytick_ = [int(y / 1000) for y in df_query['volume']]
        ax2.set_yticklabels(ytick_)
        ax2.set_ylabel("거래량(단위:천)", color='green', fontdict={'size': 11})
        ax2.grid(True, which='major', color='gray', linewidth=0.2)

        if not df_query['volume_ratio'].any() == 0:
            ax22 = ax2.twinx()
            ax22.plot(min_list, df_query['volume_ratio'], color='r', linewidth=1)
            ax22.legend(['거래량증가배율'])

        # deal 날짜를 선택하면 매수/매도 타점을 annotate함
        if (date == deal_time[:8]) and (pd.to_datetime(deal_time) in df_query.index.to_list()):
            """
            date는 분봉차트를 그리기 위해서 선택하는 날짜임. deal_time은 bollinger05.db에 저장된 거래시간임.
            만약 같다면 분봉차트에서 줌하기 위하여 다시 클릭할때도 언제나 같다. 
            """
            # print('시간비교', df_query.index.to_list(), pd.to_datetime(deal_time))
            # zoom할 경우 50봉 범위안에 없을 수도 있다.
            x_ = df_query.index.to_list().index(pd.to_datetime(deal_time))
            y_ = buy_price
            xtext_ = x_ - 5 if redraw else x_ - 50
            ax1.annotate(f'매수:{str(int(buy_price))}', (x_, y_), xytext=(xtext_, y_),
                         arrowprops=dict(facecolor='green', shrink=0.05, width=0.5, headwidth=5, alpha=0.7),
                         fontsize=12, bbox=dict(facecolor='r', alpha=0.2))
        else:
            ax1.text(0.5, 0.97, f'매수일시: {deal_time}', bbox=dict(facecolor='y', alpha=0.5),
                     horizontalalignment='center',
                     verticalalignment='center', fontsize=12, transform=ax1.transAxes)

        def motion_notify_event(event):
            logging.info(f"592r, x좌표={event.xdata}, {event.inaxes == ax1}")
            if len(ax1.texts) > 1:
                for txt in ax1.texts:
                    txt.set_visible(False)
                ax1.texts[0].set_visible(True)

            if event.inaxes == ax1:
                logging.info(f"x좌표={event.xdata}")
                xv = round(event.xdata)
                if (xv < len(df_query)) and (event.ydata <= df_query['high'][xv]) and (
                        event.ydata >= df_query['low'][xv]):
                    # fig.canvas.flush_events()
                    close_1 = df_query['전봉종가'][xv]
                    open_ = df_query['open'][xv]
                    high_ = df_query['high'][xv]
                    low_ = df_query['low'][xv]
                    close_ = df_query['close'][xv]

                    text = f"시간     :{df_query.index[xv].strftime('%H:%M')}\n" \
                           f"시가     :{open_} ({round((open_ / close_1 - 1) * 100, 2)}%)\n" \
                           f"고가     :{high_} ({round((high_ / close_1 - 1) * 100, 2)}%)\n" \
                           f"저가     :{low_} ({round((low_ / close_1 - 1) * 100, 2)}%)\n" \
                           f"종가     :{close_} ({round((close_ / close_1 - 1) * 100, 2)}%)\n" \
                           f"거래량   :{df_query['volume'][xv]}\n" \
                           f"\n" \
                           f"[볼린저 밴드]\n" \
                           f"밴드상단   :{int(df_query['day_upperB'][xv])}\n" \
                           f"돌파B배율  :{df_query['bWidth_ratio'][xv]}"

                    if event.y > 400:
                        yv = df_query['low'][xv] * 1.00 - 100
                    else:
                        yv = df_query['high'][xv] * 1.00
                else:
                    text = ''
                    yv = event.ydata
                ax1.text(xv + 1.5, yv, text, bbox=dict(facecolor='white', alpha=1.0))
                fig.canvas.draw()

        fig.canvas.mpl_connect("motion_notify_event", motion_notify_event)

        # candle을 50개씩 짤라서 그래프를 확대출력하는 함수
        def mouse_click_event(event):
            i = round(event.xdata)  # xdata는 x축의 데이터 순서를 의미한다. index의 순서가 아니다.
            print('수정전 start,end', self.start, self.end)
            self.start = self.start + i - 25
            if self.start < 0:  self.start = 0
            if self.start > len(df_min.index) - 50:
                self.start = len(df_min.index) - 50
            self.end = self.start + 50

            # 50개분봉일 경우는 앞의 분봉차트를 지우고 새로 그린다
            if redraw:
                plt.close(fig)

            self.redraw_minute_chart50(df_min, code, date, buy_price, deal_time, self.start, self.end, redraw=True)
            print('s,e', len(df_min), start, end)

        fig.canvas.mpl_connect("button_press_event", mouse_click_event)
        fig.show()

    def redraw_minute_chart50(self, df_min, code, date, buy_price, deal_time, start, end, redraw):
        self.draw_minite_chart(df_min, code, date, buy_price, deal_time, start, end, redraw)

    def hogaUnit(self):

        table_list = self.sqlTableList(DB_KOSDAQ_MIN)
        print('table_list', table_list)


if __name__ == '__main__':
    bTrader = BollingerTrader()
    app = QApplication(sys.argv)
    deal_profit = DealProfit()
    deal_profit.show()
    app.exec_()
