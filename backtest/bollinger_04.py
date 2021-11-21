import sys
import datetime
import sqlite3
import time
import pandas as pd
import numpy as np
from kiwoom import Kiwoom
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtGui, uic
import mplfinance as mpf
from mplfinance.original_flavor import candlestick2_ohlc
from matplotlib import gridspec
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import logging

# logging.basicConfig(level=logging.INFO)
# logging.basicConfig(filename="../log.txt", level=logging.ERROR)
# logging.basicConfig(filename="../log.txt", level=logging.INFO)

# 한글폰트 깨짐방지
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False   # 한글 폰트 사용시 마이너스 폰트 깨짐 해결

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
        # self.df_deal = pd.DataFrame(columns=['종목번호', '체결시간', '매수가', '매도가', '순이익', '순이익률',
        #                                      '직전V평균', 'V증가율', '밴드상단', '돌파밴드상단', '시가', '고가', '종가',
        #                                      '돌파V', '돌파V배율', '주가상승률', '지수상승률',
        #                                      ])
        # 키움에서 업종지수 가져옴
        # self.get_market_jisu()

        # sqlite3에서 업종지수를 읽어와서  DATAFRAME에 저장; '익일시가' 컬럼을 추가 입력
        con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/backtest/market_jisu.db")
        self.df_kosdaq_jisu = pd.read_sql("SELECT * FROM kosdaq_jisu", con, index_col='date', parse_dates='date')
        self.df_kosdaq_jisu['익일시가'] = self.df_kosdaq_jisu['open'].shift(-1)
        # print('코스닥지수/n', self.df_kosdaq_jisu)
        con.close()

        # sqlite3 db에서 코스닥 일봉데이터의 table_list를 가져와서 list에 저장
        con = sqlite3.connect(DB_KOSDAQ_DAY)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_list = [v[0] for v in cur.fetchall()]
        con.close()

        # table_list에 대한 종목명 가져오기
        # self.get_code_name(table_list)

        # code_name 텍스트파일 읽어와서 list에 저장
        self.code_name = {}
        with open('C:/Users/USER/PycharmProjects/my_window/backtest/code_name.txt', 'r') as f:

            while True:
                line = f.readline()
                code = line[:6]
                name = line[7:].strip('\n')
                self.code_name[code] = name
                if not line:
                    break
            # print('code_name', self.code_name)

        # 종목별 시물레이션 시작
        # for i in np.arange(1.1, 2.6, 0.1):
        for i in np.arange(2.6, 4.1, 0.1):
            self.df_deal = pd.DataFrame(columns=['종목번호', '체결시간', '매수가', '매도가', '순이익', '순이익률',
                                                 '직전V평균', 'V증가율', '밴드상단', '돌파밴드상단', '시가', '고가', '종가',
                                                 '돌파V', '돌파V배율', '주가상승률', '지수상승률',
                                                 ])

            df_dealProfit = pd.DataFrame(columns=['밴드폭확장률', '총건수', '매수가합계', '순이익합계', '순이익률', 'V증가율',
                                                  '돌파V배율', '주가상승률', '지수상승률'])

            self.startTrader(table_list, i)

            # 시물레이션 결과 요약 출력
            # print(f"순이익 {self.df_deal['순이익'].sum()} 순이익률 "
            #       f"{round(self.df_deal['순이익'].sum() / self.df_deal['매수가'].sum() * 100, 2)}")

            # 시물레이션 결과를 건별로 sqlite3 db에 저장
            self.df_deal['체결시간'] = self.df_deal['체결시간'].apply(lambda _: datetime.datetime.strftime(_, "%Y%m%d%H%M"))
            self.df_deal['체결시간'].head(5)
            con = sqlite3.connect('bollinger04.db')
            table_name = f"deal_{str(round(i,1))}"
            # self.df_deal.to_sql(table_name, con, if_exists='replace', index=False)
            self.df_deal.to_sql(table_name, con, if_exists='append', index=False)
            con.commit()
            con.close()

            # deal 결과 요약저장
            profit_ratio = round(self.df_deal['순이익'].sum() / self.df_deal['매수가'].sum() * 100, 2)
            df_dealProfit.loc[len(df_dealProfit)] = [f"deal_{str(round(i, 1))}",
                                                     self.df_deal['매수가'].count(),
                                                     self.df_deal['매수가'].sum(),
                                                     self.df_deal['순이익'].sum(),
                                                     profit_ratio,
                                                     round(self.df_deal['V증가율'].mean(), 1),
                                                     round(self.df_deal['돌파V배율'].mean(), 1),
                                                     round(self.df_deal['주가상승률'].mean(), 2),
                                                     round(self.df_deal['지수상승률'].mean(), 2)
                                                     ]
            print('deal결과\n', df_dealProfit)

            con = sqlite3.connect("deal_profit.db")
            df_dealProfit.to_sql('deal_summary', con, if_exists='append', index=False)
            con.commit()
            con.close()

    def get_market_jisu(self):
        # 키움에서 코스피/코스닥업종지수 일봉데이터 가져오기
        kiwoom = Kiwoom()
        df_kosdaq_jisu = kiwoom.block_request('opt20006', 업종코드='101', 기준일자='20210930', output='업종일봉조회', next=0)
        df_kosdaq_jisu = df_kosdaq_jisu[['일자', '시가', '고가', '저가', '현재가', '거래량', '거래대금']]
        df_kosdaq_jisu.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        df_kosdaq_jisu = df_kosdaq_jisu.reset_index(drop=True).set_index('date')
        df_kosdaq_jisu = df_kosdaq_jisu.astype(int)
        # kiwoom 연결 끊기 해야함.

        # 업종지수 sqlite3에 저장
        con = sqlite3.connect("market_jisu.db")
        df_kosdaq_jisu.to_sql('kosdaq_jisu', con, if_exists='replace')
        con.commit()
        con.close()

    def get_code_name(self, code_list):
        kiwoom = Kiwoom()
        code_name = []
        for code in code_list:
            name = kiwoom.GetMasterCodeName(code)
            code_name.append(f"{code} {name}")

        # print('code_name', code_name)
        with open('C:/Users/USER/PycharmProjects/my_window/backtest/code_name.txt', 'w') as f:
            for c_n in code_name:
                f.write(c_n+'\n')

    # 종목별로 시물레이션하기 위하여 sqlite3 db에서 일봉데이터를 가져와서 dataframe에 저장하고 시물레이션 실시
    def startTrader(self, table_list, multiple):
        starttime = time.time()
        for i, table in enumerate(table_list):
            # sqlite3 db에서 종목별 일봉데이터를 가져와서 인덱스, 컬럼조정 및 볼린저밴드 컬럼 추가
            con = sqlite3.connect(DB_KOSDAQ_DAY)
            # cur = con.cursor()
            df_day = pd.read_sql(f"SELECT * FROM '{table}' WHERE 일자 > 20210101 ORDER BY 일자", con,
                                 index_col='일자', parse_dates='일자')
            con.close()
            df_day.index.name = 'date'
            df_day.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
            df_day = df_day[['open', 'high', 'low', 'close', 'volume']]

            df_day['volume_mean20'] = round(df_day['volume'].rolling(window=20).mean())
            df_day['volume_ratio'] = round(df_day['volume'] / df_day['volume_mean20'], 1)
            df_day['종고저평균'] = round((df_day['close'] + df_day['high'] + df_day['low']) / 3)
            df_day['밴드기준선'] = round(df_day['종고저평균'].rolling(window=20).mean())  # 밴드기준선
            df_day['밴드상단'] = round(df_day['밴드기준선'] + df_day['종고저평균'].rolling(window=20).std(ddof=0) * 2)
            df_day['밴드하단'] = round(df_day['밴드기준선'] - df_day['종고저평균'].rolling(window=20).std(ddof=0) * 2)
            df_day['밴드폭'] = round((df_day['밴드상단'] - df_day['밴드하단']) / df_day['밴드기준선'], 3)
            df_day['전일밴드폭'] = df_day['밴드폭'].shift(1)
            df_day['밴드돌파'] = df_day['high'] > df_day['밴드상단']
            df_day['익일시가'] = df_day['open'].shift(-1)

            # 대상기간을 압축하여하여 시물레이션 시작
            period = (df_day.index >= "2021-02-01") & (df_day.index <= "2021-09-30")
            print(f"시물레이션 중 {table}... {i + 1} / {len(table_list)}")

            self.code_trading(table, df_day.loc[period], multiple)  # 종목별로 날짜를 달리하여 여러개의 deal이 있을 수 있다.
        # print("소요시간", time.time() - starttime)

    def code_trading(self, table, df_day, multiple):  # '돌파한 날만' filtering하면 안된다. ---> 돌파이전 상황도 중요.
        chl_avrg_list, chl_list = None, None

        # 분봉에 일봉볼린저밴드를 나타내기 위하여 일봉데어터로부터 기초데어터를 가져와서 계산하는 함수.
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

        for i, idx in enumerate(df_day.index):

            # 대상기간 전데이터는 제외 ---> 그럼에도 불구하고 시작일부터 20일 전까지의 데이터는 볼린저밴드 계산을 위해서 필요하므로 자료확보.
            if idx < datetime.datetime.strptime('2021-03-01', '%Y-%m-%d'):
                continue

            # 고가돌파한 당일의 분봉데이터 가져와서 조건검색 ===> # 이조건에 해당하는 날짜가 여러개일 수 있다.
            if df_day.at[idx, 'high'] > df_day.at[idx, '밴드상단'] \
                    and df_day.at[idx, '밴드폭'] > df_day.at[idx, '전일밴드폭'] * multiple:     # multiple = 1.5

                # -----------------------------
                start = time.time()

                self.count += 1
                xdate = idx.strftime("%Y%m%d")  # 날짜인덱스

                # 분봉차트에 일봉 볼린저밴드를 나타내기 위하여 일봉데이터의 19일치(1일전~20일전) 종고저데이터 리스트를 만듦.
                chl_avrg_list = []  # 리스트 초기화  # 초기화하지 않으면 계속 누적됨.
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

                # 함수 _mean20_cal()
                df_min['day_mean20'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[0])
                df_min['day_upperB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[1])
                df_min['day_lowerB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[2])
                df_min['day_bandWidth'] = (df_min['day_upperB'] - df_min['day_lowerB']) / df_min['day_mean20']
                df_min['next_open'] = df_min['open'].shift(-1)
                # print('분봉\n', df_min)
                # print(f"당일상단, 일봉{df_day.at[idx, '밴드상단']}, 분봉{df_min['day_upperB'][-1]}")
                # input()

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
                        self.df_deal.loc[len(self.df_deal)] = [table, m_idx,
                                                               buy_price, sell_price,
                                                               profit, profit_per,
                                                               int(df_day.at[idx, 'volume_mean20']),
                                                               df_day.at[idx, 'volume_ratio'],
                                                               df_day.at[idx, '밴드상단'],
                                                               df_min.at[m_idx, 'day_upperB'],
                                                               df_day.at[idx, 'open'],
                                                               df_day.at[idx, 'high'],
                                                               df_day.at[idx, 'close'],
                                                               df_min.at[m_idx, 'cum_volume'],
                                                               df_min.at[m_idx, 'volume_ratio'],
                                                               juga_ratio, jisu_ratio,
                                                               ]
                        logging.info(f"DealPoint {table} {m_idx} {buy_price} {sell_price} {df_min.at[m_idx, 'day_upperB']} "
                                     f"{df_day.at[idx, '밴드상단']} {df_day.at[idx, 'close']}")

                        break   # 첫돌파만 매수, 나머지는 pass


# class PointWindow(QMainWindow, form_class):
class DealProfit(QMainWindow):
    def __init__(self):
        super(DealProfit, self).__init__()
        db_name = "C:/Users/USER/PycharmProjects/my_window/backtest/deal_profit.db"
        table_name = 'deal_summary'
        con = sqlite3.connect(db_name)
        # print('dbname', db_name)
        df = pd.read_sql(f"SELECT * FROM '{table_name}'", con)
        con.close()
        # print('df', df)

        column_count = len(df.columns)
        row_count = len(df)
        self.setGeometry(100, 100, 1800, 900)
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
        db_name = "C:/Users/USER/PycharmProjects/my_window/backtest/bollinger04.db"
        table_name = self.table.item(row, 0).text()
        # print('table_name', table_name)

        # todo self변수로 넣어야 작동한다. 즉, 단순하게 pointwindow로 해서는 안된다.
        self.pointwindow = PointWindow(db_name, table_name)
        self.pointwindow.show()


class PointWindow(QWidget):
    def __init__(self, db_name, table_name):
        super(PointWindow, self).__init__()
        # print('359진입')
        self.bWidthMultiple = float(table_name[5:])
        # print('multiple', self.bWidthMultiple)

        # 종목이름을 code_name 텍스트파일에서 읽어와서 list에 저장  ==> 향후에는 utility.py에서 읽어옴.
        self.code_name = {}
        with open('C:/Users/USER/PycharmProjects/my_window/backtest/code_name.txt', 'r') as f:

            while True:
                line = f.readline()
                code = line[:6]
                name = line[7:].strip('\n')
                self.code_name[code] = name
                if not line:
                    break
            # print('code_name', self.code_name)
        '''
        con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/backtest/bollinger04.db")
        df = pd.read_sql("SELECT * FROM bollinger_deal", con)
        con.close()
        '''
        con = sqlite3.connect(db_name)
        # print('dbname', db_name)
        df = pd.read_sql(f"SELECT * FROM '{table_name}'", con)
        con.close()
        # print('df_b4', df)

        column_count = len(df.columns)
        row_count = len(df)
        self.setGeometry(100, 100, 1800, 900)
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

        self.table.cellClicked.connect(self.cell_clicked)
        # print('self_table 객체', self.table)
        self.show()
    # 마우스이벤트 예시
    def mouseMoveEvent(self, event):
        it = self.item(self.rowCount(), 1)
        it.QToolTip.showText('Insert')
        self.onHovered()

    def cell_clicked(self, row, col):
        code = self.table.item(row, 0).text()
        # print('row', row)
        deal_time = self.table.item(row, 1).text()  # 202109160909
        buy_price = float(self.table.item(row, 2).text())
        sell_price = float(self.table.item(row, 3).text())

        # 일봉차트 그리기
        tdate = pd.to_datetime(deal_time[:8])
        start = tdate - datetime.timedelta(days=160)
        end = tdate + datetime.timedelta(days=40)
        start = str(start.strftime("%Y%m%d"))
        end = str(end.strftime("%Y%m%d"))

        # print('start', start, type(start))
        con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/db/kosdaq(day).db")
        df_day = pd.read_sql(f"SELECT * FROM '{code}' WHERE 일자 > {start} and 일자 <= {end} "
                             f"ORDER BY 일자", con, index_col='일자', parse_dates='일자')
        con.close()
        df_day.index.name = 'date'
        df_day.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
        df_day = df_day[['open', 'high', 'low', 'close', 'volume', 'amount']]

        # bollinger band 추가
        df_day['종고저평균'] = round((df_day['close'] + df_day['high'] + df_day['low']) / 3, 0)
        df_day['밴드기준선'] = round(df_day['종고저평균'].rolling(window=20).mean(), 0)  # 밴드기준선
        df_day['밴드상단'] = round(df_day['밴드기준선'] + df_day['종고저평균'].rolling(window=20).std() * 2, 0)
        df_day['밴드하단'] = round(df_day['밴드기준선'] - df_day['종고저평균'].rolling(window=20).std() * 2, 0)
        df_day['거래량20'] = round(df_day['volume'].rolling(window=20).mean(), 0)
        df_day['밴드폭'] = round((df_day['밴드상단'] - df_day['밴드하단']) / df_day['밴드기준선'], 3)
        df_day['전일밴드폭'] = df_day['밴드폭'].shift(1)

        # 지수차트 가져오기
        con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/backtest/market_jisu.db")
        df_jisu = pd.read_sql(f"SELECT * FROM kosdaq_jisu WHERE date > {start} and date <= {end} "
                              f"ORDER BY date", con, index_col='date', parse_dates='date')
        con.close()

        self.dayChart(code, df_day, deal_time, buy_price, sell_price, df_jisu)  # tdate ;  2021-09-16 형식

    # 구 mpl_finace를 이용하여 그리는 candle차트
    def dayChart(self, code, df_day, deal_time, buy_price, sell_price, df_jisu):
        tdate = pd.to_datetime(deal_time[:8])

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

        ytick_ = [int(y/1000) for y in df_day['volume']]
        ax2.set_yticklabels(ytick_)
        ax2.set_ylabel("거래량(단위:천)", color='green', fontdict={'size': 11})
        ax2.grid(True, which='major', color='gray', linewidth=0.2)

        # annotation 설정
        # x_ = [i for i, idx in enumerate(df_day.index) if idx.strftime("%Y-%m-%d") == tdate.strftime("%Y-%m-%d")][0]
        x_ = df_day.index.to_list().index(tdate)
        print('x_', x_)
        y_ = buy_price
        ax1.annotate(f'매수:{str(int(buy_price))}', (x_, y_), xytext=(x_ - 20, y_),
                     arrowprops=dict(facecolor='green', shrink=0.05, width=0.5, headwidth=5, alpha=0.7),
                     fontsize=12, bbox=dict(facecolor='r', alpha=0.2))
        y2_ = sell_price
        ax1.annotate(f'매도:{str(int(sell_price))}', (x_+1, y2_), xytext=(x_ + 10, y2_ * 1.05),
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
                    text = f"일자     :{df_day.index[xv].strftime('%Y-%m-%d')}\n" \
                           f"시가     :{df_day['open'][xv]}\n" \
                           f"고가     :{df_day['high'][xv]}\n" \
                           f"저가     :{df_day['low'][xv]}\n" \
                           f"종가     :{df_day['close'][xv]}\n" \
                           f"거래량   :{df_day['volume'][xv]}\n" \
                           f"\n" \
                           f"[볼린저 밴드]\n" \
                           f"밴드상단   :{int(df_day['밴드상단'][xv])}\n" \
                           f"밴드기준선  :{int(df_day['밴드기준선'][xv])}\n" \
                           f"밴드하단   :{int(df_day['밴드하단'][xv])}\n"

                    if event.y > 550:
                        yv = df_day['low'][xv] * 0.85
                    else:
                        yv = df_day['high'][xv] * 1.00

                else:
                    text = ''
                    yv = event.ydata
                ax1.text(xv+1.5, yv, text, bbox=dict(facecolor='c', alpha=1.0))
                fig.canvas.draw()
        fig.canvas.mpl_connect("motion_notify_event", motion_notify_event)

        def mouse_click_event(event):
            i = round(event.xdata)
            date = df_day.index[i].strftime("%Y%m%d")  # 2021-04-06 00:00:00 날짜type --> 20210406
            chl19 = df_day['종고저평균'].to_list()[i - 19:i]  # 왜 i가 전일이 되는가 하면 슬라이싱할때 마지막 값은 포함하지 않기 때문임.
            df_min = self.get_minute_data(code, date, df_day['거래량20'][i], chl19, df_day['전일밴드폭'][i])
            start = 0
            end = len(df_min) - 1
            self.draw_minite_chart(df_min, code, date, buy_price, deal_time, start, end)
            # print('분봉날짜', date)

        fig.canvas.mpl_connect("button_press_event", mouse_click_event)

        fig.show()

    def get_minute_data(self, code, date, volume20, chl19, BWidth_1):
        con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/db/kosdaq(1min).db")
        df_min = pd.read_sql(f"SELECT * FROM '{code}' WHERE 체결시간 LIKE '{date}%' ORDER BY 체결시간",
                             con, index_col='체결시간', parse_dates='체결시간')
        con.close()

        df_min.index.name = 'date'
        df_min.columns = ['close', 'open', 'high', 'low', 'volume']
        df_min = df_min[['open', 'high', 'low', 'close', 'volume']]
        # -----------------------------------------------
        df_min['cum_volume'] = df_min['volume'].cumsum()
        df_min['volume_ratio'] = \
            df_min['cum_volume'].apply(lambda x: round(x / volume20, 1))   # todo 여기수정필요
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
        df_min['bWidth_ratio'] = round(df_min['day_bandWidth'] / BWidth_1, 2)
        df_min['next_open'] = df_min['open'].shift(-1)
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
        # print('min_list', min_list, min_list[0], min_list[-1])

        ax1.plot(min_list, df_query['day_upperB'], color='r', linewidth=1)

        candlestick2_ohlc(ax1, df_query['open'], df_query['high'], df_query['low'],
                          df_query['close'], width=0.8,
                          colorup='r', colordown='b')

        ax0.set_title(f"{self.code_name[code]} 분봉차트 ({date})", fontsize=20)
        ax1.legend(['일봉B밴드상단'])
        ax1.tick_params(axis='x', top=False, bottom=False, labeltop=False, labelbottom=False, width=0.2, labelsize=11)
        # ax1.xaxis.set_visible(False)
        ax1.grid(True, which='major', color='gray', linewidth=0.2)

        ax0.plot(min_list, df_query['bWidth_ratio'], color='c', linewidth=1)
        ax0.tick_params(axis='x', top=False, bottom=False, labeltop=False, labelbottom=False, width=0.2, labelsize=11)
        # ax0.xaxis.set_visible(False)
        # ax0.axhline(y=1.5, color='r', linewidth=0.5)
        ax0.axhline(y=self.bWidthMultiple, color='r', linewidth=0.5, label='bWidthMultipl')
        ax0.legend(['밴드상단확장률'])
        ax0.grid(True, which='major', color='gray', linewidth=0.2)

        ax2.bar(min_list, df_query['volume'])
        ax2.set_xticks(range(0, len(df_query.index), 5))
        ax2.set_xticks(min_list, minor=True)
        name_list = [v.strftime("%H:%M") for i, v in enumerate(df_query.index)]
        name_list = [name_list[i] for i in range(0, len(df_query.index), 5)]
        ax2.set_xticklabels(name_list, rotation=90)

        ytick_ = [int(y / 1000) for y in df_query['volume']]
        ax2.set_yticklabels(ytick_)
        ax2.set_ylabel("거래량(단위:천)", color='green', fontdict={'size': 11})
        ax2.grid(True, which='major', color='gray', linewidth=0.2)
        ax22 = ax2.twinx()
        ax22.plot(min_list, df_query['volume_ratio'], color='r', linewidth=1)
        ax22.legend(['거래량증가배율'])

        # deal 날짜를 선택하면 매수/매도 타점을 annotate함
        if (date == deal_time[:8]) and (pd.to_datetime(deal_time) in df_query.index.to_list()):
            """
            date는 분봉차트를 그리기 위해서 선택하는 날짜임. deal_time은 bollinger04.db에 저장된 거래시간임.
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
                if (xv < len(df_query)) and (event.ydata <= df_query['high'][xv]) and (event.ydata >= df_query['low'][xv]):
                    # fig.canvas.flush_events()
                    text = f"시간     :{df_query.index[xv].strftime('%H:%M')}\n" \
                           f"시가     :{df_query['open'][xv]}\n" \
                           f"고가     :{df_query['high'][xv]}\n" \
                           f"저가     :{df_query['low'][xv]}\n" \
                           f"종가     :{df_query['close'][xv]}\n" \
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
                ax1.text(xv + 1.5, yv, text, bbox=dict(facecolor='c', alpha=1.0))
                fig.canvas.draw()
        fig.canvas.mpl_connect("motion_notify_event", motion_notify_event)

        # candle을 50개씩 짤라서 그래프를 확대출력하는 함수
        def mouse_click_event(event):
            i = round(event.xdata)   # xdata는 x축의 데이터 순서를 의미한다. index의 순서가 아니다.
            print('수정전 start,end', self.start, self.end)
            self.start = self.start + i - 25
            if self.start > len(df_min.index) - 50:
                self.start = len(df_min.index) - 50
            self.end = self.start + 50

            # 50개분봉일 경우는 앞의 분봉차트를 지우고 새로 그린다
            if redraw:
                plt.close(fig)

            self.redraw_minute_chart50(df_min, code, date, buy_price, deal_time, self.start, self.end, redraw=True)
        fig.canvas.mpl_connect("button_press_event", mouse_click_event)
        fig.show()

    def redraw_minute_chart50(self, df_min, code, date, buy_price, deal_time, start, end, redraw):
        self.draw_minite_chart(df_min, code, date, buy_price, deal_time, start, end, redraw)

    def hogaUnit(self):

        table_list = self.sqlTableList(DB_KOSDAQ_MIN)
        print('table_list', table_list)


if __name__ == '__main__':
    # btest = BollingerTesting()
    app = QApplication(sys.argv)
    deal_profit = DealProfit()
    deal_profit.show()
    # pwindow = PointWindow()
    # pwindow.show()
    app.exec_()






































