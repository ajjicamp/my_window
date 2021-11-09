import sqlite3
import time

import pandas as pd
import mplfinance as mpf
import numpy as np

DB_KOSDAQ_DAY = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(day).db"
DB_KOSDAQ_MIN = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(1min).db"

volume_multiple = [1, 2, 3, 5, 10]
avrg_volume_period = [20, 40, 60, 120]
bandWidth_ratio = [1.2, 1.5, 2.0, 3.0]
max_min_ratio = [0.1, 0.2, 0.3, 0.5]
goal_ratio = [1.03, 1.04, 1.05, 1.06, 1.07, 1.1]
trailing_stop_price = [1, 1.05, 1.06, 1.07, 1.08, 1.10]
trailing_stop_ratio = [0.01, 0.02, 0.03]

# 범용으로 자주 써먹을 함수 미리 정의
def cross(self, args, args2):
    if args > args2:
        return True
    else:
        return False

class BollingerTesting:
    def __init__(self):
        self.df_day = pd.DataFrame()
        self.df_min = pd.DataFrame()
        self.start = None
        self.end = None
        self.buy_price = 0
        self.sell_price = 0
        self.position = {}
        self.df_trading = pd.DataFrame(columns=['매수가', '매도가', '순수익', '밴드상단'])

        con = sqlite3.connect(DB_KOSDAQ_DAY)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_list = [v[0] for v in cur.fetchall()]
        con.close()
        # print(table_list)
        self.startTrader(table_list)
        print('트레이딩 결과\n', self.df_trading)

    def startTrader(self, table_list):
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

            df_day['종고저평균'] = round((df_day['close'] + df_day['high'] + df_day['low']) / 3, 0)
            df_day['밴드기준선'] = round(df_day['종고저평균'].rolling(window=20).mean(), 0)  # 밴드기준선
            df_day['밴드상단'] = round(df_day['밴드기준선'] + df_day['종고저평균'].rolling(window=20).std() * 2, 0)
            df_day['밴드하단'] = round(df_day['밴드기준선'] - df_day['종고저평균'].rolling(window=20).std() * 2, 0)
            df_day['밴드폭'] = round((df_day['밴드상단'] - df_day['밴드하단']) / df_day['밴드기준선'], 3)
            df_day['밴드돌파'] = df_day['high'] > df_day['밴드상단']
            df_day['익일시가'] = df_day['open'].shift(-1)
            # df_day['밴도']
            # 향후 분봉차트에 일봉 볼리저밴드를 그리기 위하여 종고저평균 19일치(1일전~19일전)데이터를 리스트로 저장.
            # for df_day['종고저평균']
            # print(df_day)

            # 종목별 대상기간을 설정하여 시물레이션

            period = (df_day.index >= "2021-03-01") & (df_day.index <= "2021-09-30")
            self.code_trading(table, df_day.loc[period])
            print(f"시물레이션 중...{table}")
            if i == 10:
                break
            # print('필터 df', df_day.loc[period])

            # self.drawPlot(df_day)
            # self.drawPlot2(df_day)
            # self.drawPlot3(df_day)
            # self.drawPlot4(df_day)
            # break
        print("소요시간", time.time() - starttime)

    def code_trading(self, table, df_day):  # filtering 된 df_day
        def cross_upperB():
            pass

        # 일단 검색범위를 좁히기 위하여 일봉 고가를 기준으로 볼린저밴드상단을 돌파한 날을 찾아서 시물레이션

        # df_day = df_day[df_day['밴드돌파']]
        print('밴드돌파', df_day)

        def avrg20_cal(data, chl_avrg_list):
            print(chl_avrg_list)
            chl_list = chl_avrg_list.copy()
            chl_list.append(data)
            avrg20 = round(np.mean(chl_list), 0)
            std20 = np.std(chl_list)
            upperB = round((avrg20 + std20 * 2), 0)
            lowerB = round((avrg20 - std20 * 2), 0)
            # print('band_values', avrg20, upperB, lowerB)
            return (avrg20, upperB, lowerB)

        for i, idx in enumerate(df_day.index):
            print('107', df_day['종고저평균'])
            chl_avrg_list=[]
            if df_day.at[idx, 'high'] > df_day.at[idx, '밴드상단']:
                # 고가돌파한 당일의 분봉데이터 가져와서 조건검색
                xdate = idx.strftime("%Y%m%d")  # 날짜인덱스
                # print('i idx bandW', i, idx, df_day.at[idx, '밴드폭'])

                # 분봉차트에 일봉 볼린저밴드를 나타내기 위하여 일봉데이터의 19일치(1일전~20일전) 종고저데이터 리스트를 만듦.
                chl_avrg_list = df_day['종고저평균'].to_list()[i-19:i]   # 왜 i가 전일이 되는가 하면 슬라이싱할때 마지막 값은 포함하지 않기 때문임.
                print('종고저평균리스트\n', chl_avrg_list, len(chl_avrg_list))

                # period = (df_day.index >= "2021-03-01") & (df_day.index <= "2021-04-22")
                # print('trade_df\n', df_day.loc[period])

                con = sqlite3.connect(DB_KOSDAQ_MIN)
                df_min = pd.read_sql(f"SELECT * FROM '{table}' WHERE 체결시간 LIKE '{xdate}%' ORDER BY 체결시간", con,
                                     index_col='체결시간', parse_dates='체결시간')
                con.close()
                df_min.index.name = 'date'
                df_min.columns = ['close', 'open', 'high', 'low', 'volume']
                df_min = df_min[['open', 'high', 'low', 'close', 'volume']]
                # df_min['highest'] = df_min.apply(lambda x: highcol(x['high'], x['highest']), axis=1)
                df_min['highest'] = df_min['high'].cummax()
                df_min['lowest'] = df_min['low'].cummin()
                df_min['종고저평균'] = (df_min['highest'] + df_min['lowest'] + df_min['close']) / 3
                df_min['day_avrg20'] = df_min['종고저평균'].apply(lambda x: avrg20_cal(x, chl_avrg_list)[0])
                df_min['day_upperB'] = df_min['종고저평균'].apply(lambda x: avrg20_cal(x, chl_avrg_list)[1])
                df_min['day_lowerB'] = df_min['종고저평균'].apply(lambda x: avrg20_cal(x, chl_avrg_list)[2])

                print('분봉\n', df_min)
                break

                for mi, midx in enumerate(df_min.index):

                    # 일봉 볼린저밴드 계산
                    close = df_min.at[midx, 'close']
                    highest = max(df_min['high'][:mi+1])
                    lowest = min(df_min['low'][:mi+1])

                    chl_avrg = (highest + lowest + close) / 3
                    chl_avrg_list.append(chl_avrg)
                    avrg20 = np.mean(chl_avrg_list)
                    std20 = np.std(chl_avrg_list)
                    upperB = avrg20 + std20 * 2
                    lowerB = avrg20 - std20 * 2
                    bandWidth = upperB - lowerB

                    # if (df_min.at[midx, 'close'] > upperB) & (bandWidth > df_day.at[idx, '밴드폭'] * 2.0):
                    if df_min.at[midx, 'close'] > upperB:
                        buy_price = df_min.at[midx, 'close'] * 1.003  # 슬리피지 감안 종가에 0.3% 더한값을 buy_price로 계산
                        position = True
                        sell_price = df_day.at[idx, '익일시가']
                        profit = sell_price - buy_price

                        # self.df_trading.loc[table] = [buy_price, sell_price, profit, upperB]
        # break


        '''
        pre_cross_cond = df_day.at[i, 'pre_cross']

        # 정확하게 하려면 볼린저밴드는 일봉기준으로 돌파기준은 분봉기준 현재가로 해야 한다.
        cross_cond = df.at[i, 'close'] > df.at[i, 'upperB']

        volume_cond = df.at[i, 'volume'] > df.at[i, 'volume_avrg20'] * volume_multiple[1]
        bandWidth_cond = df.at[i, 'bandWidth'] > df.at[i, 'pre_bandWidth'] * bandWidth_ratio[1]
        price_max_min_cond = ((max(df.at[i, 'max_price20']) - min(df.at[i, 'max_price20'])) /
                              min(df.at[i, 'max_price20'])) < max_min_ratio[1]

        # 분봉 동원하여 trailing stop 매도하는 건 보류
        if not pre_cross_cond and cross_cond and volume_cond \
            and bandWidth_cond and price_max_min_cond:
            """             
            # 위 조건은 일봉기준으로 할 경우 종가가 볼린저밴드 상단을 돌파했다는 의미이고 
            #  매수가격을 돌파시점에 매수한다는 건 맞지 않다(즉 돌파후 종가가 하락할 수 있다)
            # 엄밀히 하려면 볼린저밴드는 일봉기준으로 만들고 돌파지점은 분봉기준으로 보아야 한다.
            """

            # buy_price = df.at[i, 'upperB'] * 1.003  # 슬리피지 감안 upperB에서 0.3% up
            buy_price = df.at[i, 'close']

            # stoploss 설정 당일 3% 이하로 내려가면 stoploss 설정하는 부분은 다음에 코딩
            sell_price = df.at[i, 'next_open']
            profit = sell_price - buy_price
            profit_ratio = profit / buy_price
        '''

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




    '''
        v_ = volume_multiple[0]
        m_ = max_min_ratio[0]
        b_ = bandWidth_ratio[0]


    def traderBollinger(self, df, table):
        for i in df.index:
            pre_cross_cond = df.at[i, 'pre_cross']

            # 정확하게 하려면 볼린저밴드는 일봉기준으로 돌파기준은 분봉기준 현재가로 해야 한다.
            cross_cond = df.at[i, 'close'] > df.at[i, 'upperB']

            volume_cond = df.at[i, 'volume'] > df.at[i, 'volume_avrg20'] * volume_multiple[1]
            bandWidth_cond = df.at[i, 'bandWidth'] > df.at[i, 'pre_bandWidth'] * bandWidth_ratio[1]
            price_max_min_cond = ((max(df.at[i, 'max_price20']) - min(df.at[i, 'max_price20'])) /
                                  min(df.at[i, 'max_price20'])) < max_min_ratio[1]

            # 분봉 동원하여 trailing stop 매도하는 건 보류
            if not pre_cross_cond and cross_cond and volume_cond \
                and bandWidth_cond and price_max_min_cond:

                """             
                # 위 조건은 일봉기준으로 할 경우 종가가 볼린저밴드 상단을 돌파했다는 의미이고 
                #  매수가격을 돌파시점에 매수한다는 건 맞지 않다(즉 돌파후 종가가 하락할 수 있다)
                # 엄밀히 하려면 볼린저밴드는 일봉기준으로 만들고 돌파지점은 분봉기준으로 보아야 한다.
                """
                
                # buy_price = df.at[i, 'upperB'] * 1.003  # 슬리피지 감안 upperB에서 0.3% up
                buy_price = df.at[i, 'close']

                # stoploss 설정 당일 3% 이하로 내려가면 stoploss 설정하는 부분은 다음에 코딩
                sell_price = df.at[i, 'next_open']
                profit = sell_price - buy_price
                profit_ratio = profit / buy_price



    def hogaUnit(self):


        if not df['preCross'] and df['cross'] and volume_cond
        # def strategy(self):
        # if


        table_list = self.sqlTableList(DB_KOSDAQ_DAY)
        print('table_list', table_list)
        self.df_day = self.bringDB(DB_KOSDAQ_DAY, '000250')

    # sqlite3 DB에서 table name 구하여 리스트에 저장
    def sqlTableList(self, db_name):
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_list = [v[0] for v in cur.fetchall()]

        return table_list

    def bringDB(self, sqlDB, table):
        con =sqlite3.connect(sqlDB)
        self.df_day = pd.read_sql(f"SELECT * FROM '{table}' WHERE ")

    # 당일 체크기준 매수조건
    def buy_condition(self, df):    #
        volume_condition = df.volume > df.avrg_volume * multi
        price_condition = df['close'] > df['preBandW'] * 1.5
        bandWidth_cond  = (max(df['avrg_bandW'] - min(df['avrg_bandW'])) / min(df['evrg_bandW'])  < 0.1
        cross_condition = df['close'] > df['upperB']

    def sell_condition(self):
        if self.position == True:
            sell
    '''


if __name__ == '__main__':
    bollinger_test = BollingerTesting()