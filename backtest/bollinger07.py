import os
import sqlite3
import pandas as pd
import datetime
import time
import numpy as np

PATH ="C:/Users/USER/PycharmProjects/my_window/backtest"
DB_KOSDAQ_DAY = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(day).db"
DB_KOSDAQ_MIN = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(1min).db"
DB_DEAL_DETAILS = f"{PATH}/bollinger07.db"
DB_DEAL_PROFIT = f"{PATH}/deal_profit07.db"

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
        multiple = 1.1
        # DB에서 종목별 일봉데어터를 가져와서 필요한 컬럼항목 추가하고 매수조건 필터링
        for i, table in enumerate(table_list[:20]):
            # print('table', i, table)
            start_time = time.time()
            con = sqlite3.connect(DB_KOSDAQ_DAY)
            df_day = pd.read_sql(f"SELECT * FROM '{table}' WHERE 일자 >= 20201001 and 일자 <= 20211005 ORDER BY 일자", con,
                                 index_col='일자', parse_dates='일자')
            con.close()
            df_day.index.name = 'date'
            df_day.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
            df_day = df_day[['open', 'high', 'low', 'close', 'volume']]

            # 밴드폭계산시 20일째날은 고가기준으로 밴드폭을 계산하여 종가기준시 빠지는 사례가 없도록 하자.
            # 종가밴드 설정
            df_day['volume_mean20'] = round(df_day['volume'].rolling(window=20).mean())
            df_day['volume_ratio'] = round(df_day['volume'] / df_day['volume_mean20'], 1)  # 거래량 증가율(직전평균대비)
            df_day['종고저평균'] = round((df_day['close'] + df_day['high'] + df_day['low']) / 3)
            df_day['밴드기준선'] = round(df_day['종고저평균'].rolling(window=20).mean())  # 밴드기준선
            df_day['밴드상단'] = round(df_day['밴드기준선'] + df_day['종고저평균'].rolling(window=20).std(ddof=0) * 2)
            df_day['밴드하단'] = round(df_day['밴드기준선'] - df_day['종고저평균'].rolling(window=20).std(ddof=0) * 2)
            df_day['밴드폭'] = round((df_day['밴드상단'] - df_day['밴드하단']) / df_day['밴드기준선'], 3)
            df_day['전일밴드폭'] = df_day['밴드폭'].shift(1)
            df_day['전일밴드상단'] = df_day['밴드상단'].shift(1)
            df_day['밴드돌파'] = df_day['high'] > df_day['밴드상단']
            df_day['익일시가'] = df_day['open'].shift(-1)
            df_day['전일종가'] = df_day['close'].shift(1)
            df_day['밴드확장률OK'] = df_day['밴드폭'] > df_day['전일밴드폭'] * multiple
            df_day['밴드120폭최고'] = df_day['밴드폭'].rolling(window=120).max()
            df_day['밴드120폭최저'] = df_day['밴드폭'].rolling(window=120).min()

            # 시초가밴드 설정
            # print(f"시물레이션 중 {table}... {i + 1} / {len(self.table_list)}")
            self.codeTrading(table, df_day)  # 종목별로 날짜를 달리하여 여러개의 deal이 있을 수 있다.
            print('소요시간', time.time() - start_time)

    def codeTrading(self, table, df_day):
        # buy_cond = df_day['밴드돌파'] & df_day['밴드확장률OK'] & (df_day['전일밴드폭'] != 0) \
        #            & (df_day.index >= '2021-03-01')
        # df_day = df_day[buy_cond]  # 한종목의 일봉차트

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
        self.count = 0
        for i, idx in enumerate(df_day.index):  # 고가돌파 및 밴드폭확장조건을 충족한 필터링된 데이터
            # 고가돌파한 당일의 분봉데이터 가져와서 조건검색 ===> # 이조건에 해당하는 날짜가 여러개일 수 있다.
            start = time.time()

            self.count += 1
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

            df_min['종가돌파'] = df_min['close'] > df_min['day_upperB']
            df_min['종가밴드확장'] = df_min['day_bandWidth'] > df_day.at[idx, '전일밴드폭'] * 1.1
            df_min['종가밴드폭120하위'] = df_min['day_bandWidth'] < \
                                   ((df_day.at[idx, '밴드120폭최고'] - df_day.at[idx, '밴드120폭최저']) * 0.2)

            # 시초가 기준 볼린저밴드를 계산(시초가는 이기준으로 접근)
            df_min['day_mean20_open'] = df_min['open'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[0])
            df_min['day_upperB_open'] = df_min['open'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[1])
            df_min['day_lowerB_open'] = df_min['open'].apply(lambda x: _mean20_cal(x, chl_avrg_list)[2])
            df_min['day_bandWidth_open'] = (df_min['day_upperB_open'] - df_min['day_lowerB_open']) / \
                                           df_min['day_mean20_open']
            df_min['시가돌파'] = df_min['open'] > df_min['day_upperB_open']
            df_min['시가밴드확장'] = df_min['day_bandWidth_open'] > df_day.at[idx, '전일밴드폭'] * 1.1
            df_min['시가밴드폭120하위'] = df_min['day_bandWidth_open'] < \
                   ((df_day.at[idx, '밴드120폭최고'] - df_day.at[idx, '밴드120폭최저']) * 0.2)

            # df = df_min[df_min['시가돌파'] & df_min['시가밴드확장'] & df_min['시가밴드폭120하위']]
            df = df_min[df_min['시가돌파']]
            if len(df) != 0:
                print('시가기준', table, idx, len(df))
            else:
                # df = df_min[df_min['종가돌파'] & df_min['종가밴드확장'] & df_min['종가밴드폭120하위']]
                df = df_min[df_min['종가돌파']]
                print('종가기준', table, idx, len(df))


if __name__ == '__main__':
    bTrader = BollingerTrader()






