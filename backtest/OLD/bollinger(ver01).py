import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from kiwoom import Kiwoom
# 한글폰트 깨짐방지
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False # 한글 폰트 사용시 마이너스 폰트 깨짐 해결
DB_PATH = "/db"
# db = f"{DB_PATH}/kospi(day).db"
db = f"{DB_PATH}/kosdaq(day).db"

class BollingerTrader:
    def __init__(self):
        self.df = None  # 일봉데이터
        # backtesting 거래 저장
        self.deal_df = pd.DataFrame(columns=['일자', '매수가', '매도가', '수익', '수익률',
                                             '거래량', '주가상승폭', '거래량상승률'])
        self.deal_df02 = pd.DataFrame(columns=['일자', '매수가', '매도가', '수익', '수익률',
                                             '거래량', '주가상승폭', '거래량상승률'])
        # sqlite db => dataframe
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_list = [x[0] for x in cur.fetchall()]
        # print(table_list)

        for i, table in enumerate(table_list):
            df = pd.read_sql(f"SELECT * FROM '{table}' WHERE 일자 > 20210101 ORDER BY 일자",
                             con, index_col=None)
            # df['일자'] = df['일자'].apply(lambda _: datetime.strptime(_, '%Y%m%d'))

            # df에 bollinger값 추가
            self.setBollingerIndicator(df)

            # 분석시작
            self.df = df[(df['일자'] >= '20210701') & (df['일자'] <= '20210831')]
            # self.df = df[(df['일자'] >= '20210401') & (df['일자'] <= '20210531')]
            # print('범위지정후', self.df)
            self.backTesting(self.df, table)
            # break
            print(f'{table} {i}/{len(table_list)} 분석중...')

        con.close()

        print('거래내용', self.deal_df)
        self.save_sqlite3(self.deal_df, "bollinger_deal")
        self.save_sqlite3(self.deal_df02, "bollinger_deal02")
        # df_sum = self.deal_df
        df_sum = self.deal_df02
        profit_sum = int(df_sum['수익'].sum())
        buy_sum = df_sum['매수가'].sum()
        sell_sum = df_sum['매도가'].sum()
        profit_rate = round((profit_sum / buy_sum) * 100, 2) if buy_sum != 0 else 0

        print(f'손익합계:{profit_sum} 매수합계:{buy_sum} 총수익률(%):{profit_rate}')

        self.getVolume(self.df)

        # todo 종근당바이오 210317 사례(단 하루만 튀었다가 이튿날 바로 폭락) 방지장치 필요(수동작업필요)
        # todo 위와 같은날 종근당홀딩스도 동일사례

    def setBollingerIndicator(self, df):
        # 볼린저밴드값 설정
        df['종고저평균'] = (df['현재가'] + df['고가'] + df['저가']) / 3
        df['밴드기준선'] = df['종고저평균'].rolling(window=20).mean()  # 밴드기준선
        df['밴드상단'] = df['밴드기준선'] + df['종고저평균'].rolling(window=20).std() * 2
        df['밴드하단'] = df['밴드기준선'] - df['종고저평균'].rolling(window=20).std() * 2
        # df['밴드폭'] = (df['밴드상단'] - df['밴드하단']) / df['밴드기준선']
        # df['밴드폭최대'] = df['밴드폭'].rolling(window=120, min_periods=20).max()

        # 거래량 이평 구하기
        df['거래20'] = df['거래량'].rolling(window=20).mean()  # 거래량 20이평
        df['거래량상승률'] = (df['거래량'] / df['거래20'])
        # 주가 상승률 구하기
        df['전일종가'] = df['현재가'].shift(1)
        df['주가상승률'] = (df['현재가'] - df['전일종가']) / df['전일종가'] * 100
        # 돌파여부 구하기
        df['돌파'] = df['현재가'] > df['밴드상단']
        df['전일돌파'] = df['돌파'].shift(1)
        # 익일시가(매도가)
        df['익일시가'] = df['시가'].shift(-1)

        df['전일밴드상단'] = df['밴드상단'].shift(1)
        df['전일상단돌파'] = df['현재가'] > df['전일밴드상단']


    def backTesting(self, df, table):
        count = 0
        buy_price, sell_price, profit = None, None, None
        for i in df.index:
            # 종가매수 익일시가 매도
            if not df.at[i, '전일돌파'] and df.at[i, '돌파'] and (df.at[i, '거래량상승률'] > 10) \
                    and (df.at[i, '주가상승률'] < 29) and (df.at[i, '주가상승률'] > 5.0):
                count += 1
                buy_price = df.at[i, '현재가']
                sell_price = df.at[i, '익일시가']
                profit = sell_price - buy_price
                profit_rate = round(profit / buy_price * 100, 2)
                volume = df.at[i, '거래량']
                price_rate = round(df.at[i, '주가상승률'], 2)
                volume_rate = round(df.at[i, '거래량상승률'], 2)
                # 거래를 df에 입력; 그리 많지 않으므로 전거래내용을 한개 df에 입력
                self.deal_df.loc[table] = [df.at[i, '일자'], buy_price, sell_price,
                                           profit, profit_rate, volume, price_rate, volume_rate]

            '''
            # 돌파시점 매수, 당일 trailing stop
            if not df.at[i, '전일돌파'] and df.at[i, '전일상단돌파'] \
                    and (df.at[i, '거래량상승률'] > 10) and (df.at[i, '주가상승률'] < 29):
                  # and (df.at[i, '주가상승률'] > 5.0
                buy_price = df.at[i, '전일밴드상단']
                sell_price = df.at[i, '익일시가']
                profit = sell_price - buy_price
                profit_rate = round(profit / buy_price * 100, 2)
                volume = df.at[i, '거래량']
                price_rate = round(df.at[i, '주가상승률'], 2)
                volume_rate = round(df.at[i, '거래량상승률'], 2)
                # 거래를 df에 입력; 그리 많지 않으므로 전거래내용을 한개 df에 입력
                self.deal_df02.loc[table] = [df.at[i, '일자'], buy_price, sell_price,
                                         profit, profit_rate, volume, price_rate, volume_rate]
            '''

    def save_sqlite3(self, deal_df, table_name):
        con = sqlite3.connect("../bollinger.db")
        deal_df.to_sql(f"{table_name}", con, index_label="종목코드", if_exists='replace')
        con.commit()
        con.close()

    def getVolume(self, dfd):
        con = sqlite3.connect("../bollinger.db")
        # order = '수익률(%)'
        deal_df = pd.read_sql(f"SELECT * FROM bollinger_deal ORDER BY 수익률", con, index_col=None)
        print('130\n', deal_df)
        con.close()
        # self.calculateVolume(df)
        self.pointVolume(deal_df, dfd)

    def calculateVolume(self, df):    # 여기의 df는 거래한 deal_df

        for i in df.index:
            code = df.at[i, '종목코드']
            date = df.at[i, '일자']
            print('수익률', code, date, df.at[i, '수익률'])

            # 분봉데이터에서 거래 해당일자의 코드종목 데이터를 읽어와서 dfm에 저장.
            con = sqlite3.connect(f"{DB_PATH}/kosdaq(1min).db")
            dfm = pd.read_sql(f"SELECT * FROM '{code}' WHERE 체결시간 >= {date}090000 and 체결시간 < {date}240000",
                              con, index_col=None)
            con.close()

            # 시간별 거래량 산출
            dfm['누적거래량'] = dfm['거래량'].cumsum()
            dfm['누적거래량비율'] = dfm['누적거래량'] / dfm['거래량'].sum()
            # print('dfm', dfm)
            for idx in dfm.index:
                if dfm.at[idx, '체결시간'][10:12] == '00':
                    time = dfm.at[idx, '체결시간'][8:10]
                    cum_rate = str(round(dfm.at[idx, '누적거래량비율'] * 100)) + '(%)'
                    price = dfm.at[idx, '현재가']
                    price_rate = round(price / dfm['현재가'][len(dfm)-1] * 100, 0)
                    print(time, cum_rate, price, price_rate)
            input('다음진행')

    # bollinger band 상단 돌파시점의 거래량 계산
    def pointVolume(self, deal_df, dfd):  # 거래내용을 저장한 df(deal_df)
        # print('164\n', deal_df)
        for i in deal_df.index:
            code = deal_df.at[i, '종목코드']
            date = deal_df.at[i, '일자']
            print('수익률', code, date, deal_df.at[i, '수익률'])

            # 해당 종목의 거래일자 데이터를 불러옴.
            con = sqlite3.connect(f"{DB_PATH}/kosdaq(1min).db")
            dfm = pd.read_sql(f"SELECT * FROM '{code}' WHERE 체결시간 >= {date}090000 and 체결시간 < {date}240000",
                              con, index_col=None)
            con.close()

            # con = sqlite3.connect(f"{DB_PATH}/kosdaq(day).db")
            # dfd = pd.read_sql(f"SELECT * FROM '{code}' WHERE 일자 == {date}", con, index_col=None)

            # 시간별 거래량 산출
            dfm['누적거래량'] = dfm['거래량'].cumsum()
            dfm['누적거래량비율'] = dfm['누적거래량'] / dfm['거래량'].sum()
            print('186\n', dfd)
            # print('dfm', dfm)
            # 이미 매수조건이 충족된 deal의 돌파시점 거래량을 분석하는 것임.
            for idx in dfm.index:
                # todo if dfm.at[idx, '누적거래량'] > dfd.at['전일밴드상단'][dfd['일자'] == date]:

                    time = dfm.at[idx, '체결시간'][8:10]
                    cum_rate = str(round(dfm.at[idx, '누적거래량비율'] * 100)) + '(%)'
                    price = dfm.at[idx, '현재가']
                    price_rate = round(price / dfm['현재가'][len(dfm)-1] * 100, 0)
                    print(time, cum_rate, price, price_rate)
            input('다음진행')


if __name__ == '__main__':
    bollinger = BollingerTrader()