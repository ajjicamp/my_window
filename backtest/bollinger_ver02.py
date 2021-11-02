# bollinger band 상단 돌파 + 거래량 폭등 시 장중 매수  익일시가 매도
import datetime
import sqlite3
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import gridspec, collections
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import uic
import mplfinance as mpf
import plotly.graph_objects as go
import plotly.subplots as ms
import numpy as np

# from datetime import datetime
# from kiwoom import Kiwoom

# 한글폰트 깨짐방지
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False # 한글 폰트 사용시 마이너스 폰트 깨짐 해결

form_class = uic.loadUiType("C:/Users/USER/PycharmProjects/my_window/backtest/point_window.ui")[0]

DB_PATH = "C:/Users/USER/PycharmProjects/my_window/db"
# db = f"{DB_PATH}/kospi(day).db"
kosdaq_day_db = f"{DB_PATH}/kosdaq(day).db"
kosdaq_min_db = f"{DB_PATH}/kosdaq(1min).db"


class BollingerTrader:
    def __init__(self):
        self.df = None  # 일봉데이터
        # backtesting 거래 저장
        self.jonggameme_df = pd.DataFrame(columns=[
            '일자', '매수가', '매도가', '전일종가', '수익', '수익률', '거래량', '거래20',
            '주가상승폭', '거래량상승률', '밴드상단', '전일밴드상단', '돌파시간', '돌파거래량', '돌파거래량배율', '돌파가격'])
        self.summary_deal_df = pd.DataFrame(columns=['총수익', '총매수금', '총수익률'])

        # kosdaq(day).db table_name 추출(우선 코스닥종목만으로 테스트)
        con = sqlite3.connect(kosdaq_day_db)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_list = [x[0] for x in cur.fetchall()]
        # print(table_list)
        con.close()

        # 전략 #1 볼린저밴드 상단돌파시(거래량 10배) 종가매수하여 익일시가 매도
        self.jonggameme(table_list)

    def jonggameme(self, table_list):
        day_df = None
        for idx, table in enumerate(table_list):
            # table기준 금년도 1월1일 이후 데이터 추출
            con = sqlite3.connect(kosdaq_day_db)
            day_df = pd.read_sql(f"SELECT * FROM '{table}' WHERE 일자 > 20210101 ORDER BY 일자",
                                 con, index_col=None)
            con.close()

            # df에 bollinger값 및 기타지표 값 추가(여러방식을 감안 다양한 지표 미리생성))
            self.setBollingerIndicator(day_df)

            # 분석 대상기간(2개월분)으로 필터링하여 백테스팅
            day_df = day_df[(day_df['일자'] >= '20210701') & (day_df['일자'] <= '20210831')]

            # break
            print(f'{table} {idx}/{len(table_list)} 분석중...')

            count = 0
            for i in day_df.index:
                if not day_df.at[i, '전일돌파'] and day_df.at[i, '돌파'] \
                        and (day_df.at[i, '주가상승률'] < 29):
                    # and (day_df.at[i, '거래량상승률'] > 10) \
                    count += 1
                    # buy_price = day_df.at[i, '현재가']
                    buy_price = max(day_df.at[i, '밴드상단'], day_df.at[i, '시가'])
                    sell_price = day_df.at[i, '익일시가']
                    profit = sell_price - buy_price
                    profit_rate = round(profit / buy_price * 100, 2)
                    volume = day_df.at[i, '거래량']
                    price_rate = round(day_df.at[i, '주가상승률'], 2)
                    volume_rate = round(day_df.at[i, '거래량상승률'], 2)

                    # 여기서 거래내용을 바탕으로 deal_point를 찾는다.
                    dolpa_data = self.dealPoint(table, day_df.at[i, '일자'],
                                                day_df.at[i, '밴드상단'], day_df.at[i, '거래20'])
                                                # day_df.at[i, '전일밴드상단'], day_df.at[i, '거래20'])
                    # print('dolpa_data', dolpa_data, day_df.at[i, '일자'], day_df.at[i, '밴드상단'], day_df.at[i, '거래20'])

                    # 거래를 df에 입력; 그리 많지 않으므로 전거래내용을 한개 df에 입력
                    self.jonggameme_df.loc[table] = [
                       day_df.at[i, '일자'], buy_price, sell_price, day_df.at[i, '전일종가'],
                       profit, profit_rate, volume, day_df.at[i, '거래20'], price_rate,
                       volume_rate, day_df.at[i, '밴드상단'], day_df.at[i, '전일밴드상단'],
                       dolpa_data['돌파시간'], dolpa_data['돌파거래량'], dolpa_data['돌파거래량배율'],
                       dolpa_data['돌파가격'],
                       ]
            # print('거래내용', self.jonggameme_df)

        # print('최종거래df', self.jonggameme_df)
        # 거래내용 db에 저장(전체 종목 거래분)
        self.save_sqlite3(self.jonggameme_df, "bollinger.db", "jonggameme")

        # 전체 거래내용 집계 출력
        self.summary_deal(self.jonggameme_df, 'jonggameme')
        # self.summary_deal(self.jonggameme_df, 'kosdaq')

    def dealPoint(self, code, date, upper, volume20):
        # 거래발생일자의 하루치 분봉을 가져옴
        con = sqlite3.connect(f"{DB_PATH}/kosdaq(1min).db")
        min_df = pd.read_sql(f"SELECT * FROM '{code}' WHERE 체결시간 LIKE '{date}%' ORDER BY 체결시간",
                             con, index_col=None)
        con.close()

        # 하루치 분봉데이터에 누적거래량 컬럼을 추가
        min_df['누적거래량'] = min_df['거래량'].cumsum()

        # 당일 분봉데이터를 기준으로 밴드상단 돌파시점의 거래량증가율(배율) 및 누적거래량 등을 확인하여 저장
        dolpa_data = {}
        for mi in min_df.index:
            if min_df.at[mi, '현재가'] >= upper:
            # if min_df.at[mi, '현재가'] >= before_upper:
                increase_rate = round(min_df.at[mi, '누적거래량'] / volume20, 2)
                dolpa_data['돌파시간'] = min_df.at[mi, '체결시간'][8:12]
                dolpa_data['돌파거래량'] = min_df.at[mi, '누적거래량']
                dolpa_data['돌파거래량배율'] = increase_rate
                dolpa_data['돌파가격'] = min_df.at[mi, '현재가']
                break   # todo 이 break는 반드시 필요하다.

        return dolpa_data

    def summary_deal(self, df, index):

        profit_sum = int(df['수익'].sum())
        buy_sum = df['매수가'].sum()
        # sell_sum = df['매도가'].sum()
        profit_rate = round((profit_sum / buy_sum) * 100, 2) if buy_sum != 0 else 0
        print(f'손익합계:{profit_sum} 매수합계:{buy_sum} 총수익률(%):{profit_rate}')

        self.summary_deal_df.loc[index] = [profit_sum, buy_sum, profit_rate]
        self.save_sqlite3(self.summary_deal_df, 'summary_deal.db', 'jonggameme', 'append')

        # todo 종근당바이오 210317 사례(단 하루만 튀었다가 이튿날 바로 폭락) 방지장치 필요(수동작업필요)
        # todo 위와 같은날 종근당홀딩스도 동일사례

    def save_sqlite3(self, df, db_name, table_name, option='replace'):
        con = sqlite3.connect(db_name)
        df.to_sql(f"{table_name}", con, if_exists=option)
        con.commit()
        con.close()

    def setBollingerIndicator(self, df):
        # 볼린저밴드값 설정
        df['종고저평균'] = round((df['현재가'] + df['고가'] + df['저가']) / 3, 0)
        df['밴드기준선'] = round(df['종고저평균'].rolling(window=20).mean(), 0)  # 밴드기준선
        df['밴드상단'] = round(df['밴드기준선'] + df['종고저평균'].rolling(window=20).std() * 2, 0)
        df['밴드하단'] = round(df['밴드기준선'] - df['종고저평균'].rolling(window=20).std() * 2, 0)
        df['밴드폭'] = round((df['밴드상단'] - df['밴드하단']) / df['밴드기준선'], 0)
        df['밴드폭최대'] = round(df['밴드폭'].rolling(window=120, min_periods=20).max(), 0)

        # 거래량 이평 구하기
        df['거래20'] = round(df['거래량'].rolling(window=20).mean(), 0)  # 거래량 20이평
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


class PointWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        con = sqlite3.connect("bollinger.db")
        df = pd.read_sql("SELECT * FROM jonggameme", con, index_col=None)
        df = df.rename(columns={'index': '종목코드'})
        # print('234df', df)
        con.close()

        df = df[['종목코드', '일자', '매수가', '주가상승폭', '거래량상승률', '수익률', '밴드상단', '돌파시간', '돌파거래량배율', '돌파가격']]
        rows = len(df.index)
        self.tableWidget.setRowCount(rows)
        # print('컬럼이름리스트', df.columns)
        # print('type', type(df.at[0, '주가상승폭']) == np.float64)
        for idx in df.index:
            for col, name in enumerate(df.columns):
                data = df.at[idx, name]
                # print('data', data, type(data), idx, col)
                if type(data) == np.float64:
                    data = data.item()  # numpy를 float으로 변환

                if type(data) == bytes:
                    data = int.from_bytes(data, byteorder='little')  # bytes를 int로 변환

                if type(data) == str:
                    item = QTableWidgetItem(data)
                    item.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))

                elif type(data) == int or type(data) == float:
                    # data = format(data, ',')    # 이걸 사용하면 숫자가 문자로 바뀌어 정령이 제대로 안됨.
                    item = QTableWidgetItem()
                    item.setData(Qt.DisplayRole, data)
                    item.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))

                self.tableWidget.setItem(idx, col, item)

        # 이벤트 설정
        self.tableWidget.cellClicked.connect(self.cell_clicked)

    def cell_clicked(self, row, col):
        print('cellciliked', row)
        code = self.tableWidget.item(row, 0).text()
        sdate = self.tableWidget.item(row, 1).text()
        # before_upper = self.tableWidget.item(row, 6).text()
        # before_upper = float(before_upper)
        upper = self.tableWidget.item(row, 6).text()
        upper = float(upper)

        if col > 5:
            con = sqlite3.connect(f"{DB_PATH}/kosdaq(1min).db")
            min_df = pd.read_sql(f"SELECT * FROM '{code}' WHERE 체결시간 LIKE '{sdate}%' ORDER BY 체결시간",
                                 con, index_col=None)
            con.close()

            min_df['체결시간'] = pd.to_datetime(min_df['체결시간'])
            min_df = min_df.reset_index(drop=True).set_index('체결시간')
            min_df.index.name = 'date'
            min_df.columns = ['close', 'open', 'high', 'low', 'volume']
            min_df = min_df[['open', 'high', 'low', 'close', 'volume']]
            min_df['upper'] = [upper for _ in range(len(min_df.index))]

            # 하루치 분봉데이터에 누적거래량 컬럼을 추가

            min_df['cum_volume_ratio'] = round(min_df['volume'].cumsum() / min_df['volume'].sum(), 2)
            # print('261', min_df)

            # plotly를 이용한 candle chart
            candlestick = go.Candlestick(
                x=min_df.index,
                open=min_df['open'],
                high=min_df['high'],
                low=min_df['low'],
                close=min_df['close'],
                name='분봉차트',
                increasing_line_color='red',  # 상승봉 스타일링
                decreasing_line_color='blue',  # 하락봉 스타일링
            )
            upper_plot = go.Scatter(x=min_df.index, y=min_df['upper'],
                                    line=dict(color='red', width=1.5), name='밴드상단')

            volume_bar = go.Bar(x=min_df.index, y=min_df['volume'], name='volume_bar', yaxis='y1')
            cum_volume_ratio = go.Scatter(x=min_df.index, y=min_df['cum_volume_ratio'],
                                          line=dict(color='black', width=1.5), name='누적거래량비율',
                                          yaxis='y2')

            fig = ms.make_subplots(rows=2, cols=1,
                                   shared_xaxes=True,
                                   row_heights=[2, 1],
                                   vertical_spacing=0.02,
                                   specs=[[{"secondary_y": False}],
                                          [{"secondary_y": True}]]
                                   )

            fig.add_trace(candlestick, row=1, col=1)
            fig.add_trace(upper_plot, row=1, col=1)
            fig.add_trace(volume_bar, row=2, col=1, secondary_y=False)
            fig.add_trace(cum_volume_ratio, row=2, col=1, secondary_y=True)

            fig_title = f"{code} 분봉차트 {sdate}"
            fig.update_layout(
                title=fig_title,
                yaxis1_title='Stock Price',
                yaxis2_title='Volume',
                xaxis2_title='periods',
                xaxis1_rangeslider_visible=False,
                xaxis2_rangeslider_visible=True,
            )
            # fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
            # fig.update_yaxes(title_text="<b>secondary</b> yaxis title", secondary_y=True)

            fig.show()

            '''
            colorset = mpf.make_marketcolors(up='tab:red', down='tab:blue', volume='tab:blue')
            s = mpf.make_mpf_style(marketcolors=colorset)
            adp = mpf.make_addplot(min_df['b_upper'])
            mpf.plot(min_df, type='candle', volume=True, addplot=adp, style=s)
            '''
        elif col <= 5:
            tdate = pd.to_datetime(sdate)
            # print(sdate)
            start = tdate - datetime.timedelta(days=180)
            end = tdate + datetime.timedelta(days=20)
            start = str(start.strftime("%Y%m%d"))
            end = str(end.strftime("%Y%m%d"))
            # print('start', start, type(start))
            con = sqlite3.connect(f"{DB_PATH}/kosdaq(day).db")
            day_df = pd.read_sql(f"SELECT * FROM '{code}' WHERE 일자 > {start} and 일자 < {end} ORDER BY 일자",
                                 con, index_col=None)
            # print('day_df.index', day_df['일자'])
            day_df['일자'] = pd.to_datetime(day_df['일자'])  # plotly는 datetime 형식으로 바꾸지 않아도 된다.
            day_df = day_df.reset_index(drop=True).set_index('일자')
            day_df.index.name = 'date'
            day_df.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
            day_df = day_df[['open', 'high', 'low', 'close', 'volume', 'amount']]

            # bollinger band 추가
            day_df['종고저평균'] = round((day_df['close'] + day_df['high'] + day_df['low']) / 3, 0)
            day_df['밴드기준선'] = round(day_df['종고저평균'].rolling(window=20).mean(), 0)  # 밴드기준선
            day_df['밴드상단'] = round(day_df['밴드기준선'] + day_df['종고저평균'].rolling(window=20).std() * 2, 0)
            day_df['밴드하단'] = round(day_df['밴드기준선'] - day_df['종고저평균'].rolling(window=20).std() * 2, 0)

            print('day_df', day_df)

            # sdate = pd.to_datetime(sdate.strftime("%Y%m%d"))
            if sdate in day_df.index:
                print('안에 있다')

            print('sdate', sdate)
            # plotly를 이용한 candle chart
            candlestick = go.Candlestick(
                          x=day_df.index,
                          open=day_df['open'],
                          high=day_df['high'],
                          low=day_df['low'],
                          close=day_df['close'],
                          name='일봉차트',
                          increasing_line_color='red',  # 상승봉 스타일링
                          decreasing_line_color='blue',   # 하락봉 스타일링
                          )

            volume_bar = go.Bar(x=day_df.index, y=day_df['volume'], name='거래량차트')

            upperline = go.Scatter(x=day_df.index, y=day_df['밴드상단'], line=dict(color='red', width=1.5), name='밴드상단')
            midline = go.Scatter(x=day_df.index, y=day_df['밴드기준선'], line=dict(color='black', width=1.5), name='밴드기준선')
            lowerline = go.Scatter(x=day_df.index, y=day_df['밴드하단'], line=dict(color='blue', width=1.5), name='밴드하단')

            fig = ms.make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[3, 1], vertical_spacing=0.02)
            ms.make_subplots()
            fig.add_trace(candlestick, row=1, col=1)
            fig.add_trace(upperline, row=1, col=1)
            fig.add_trace(midline, row=1, col=1)
            fig.add_trace(lowerline, row=1, col=1)
            fig.add_trace(volume_bar, row=2, col=1)

            # fig_title = f"{code} 일봉차트 {sdate.strftime('%Y:%m:%d')}"
            fig_title = f"{code} 일봉차트 {sdate}"
            fig.update_layout(
                title=fig_title,
                yaxis1_title='Stock Price',
                yaxis2_title='Volume',
                xaxis2_title='periods',
                xaxis1_rangeslider_visible=False,
                xaxis2_rangeslider_visible=True,
                annotations=[
                    {"x": tdate, "y": upper, "ay": -40,
                     "text": f"<b>{sdate}<br>돌파{upper} </b>",
                     "arrowhead": 3, "showarrow": True,
                     "font": {"size": 15}}],
            )
            fig.show()


            '''
            # 아래방법은 좀 더 연구가 필요하다
            # add your own style by passing in kwargs
            s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 6})
            fig = mpf.figure(figsize=(10, 7), style=s)  # pass in the self defined style to the whole canvas
            ax = fig.add_subplot(2, 1, 1)  # main candle stick chart subplot, you can also pass in the self defined style here only for this subplot
            av = fig.add_subplot(2, 1, 2, sharex=ax)  # volume chart subplot
            adp_data = day_df['밴드상단']
            adp = mpf.make_addplot(adp_data)

            mpf.plot(day_df, type='candle', ax=ax, volume=av)
            ax.plot(day_df.index, day_df['밴드상단'])
            fig.show()
            '''
            '''
            # 아래부분은 정상작동
            colorset = mpf.make_marketcolors(up='tab:red', down='tab:blue', volume='tab:blue')
            s = mpf.make_mpf_style(marketcolors=colorset)
            # adp_data = [day_df['밴드상단'], day_df['밴드기준선'], day_df['밴드하단']]
            adp_data = day_df['밴드상단']
            adp_data2 = day_df['밴드기준선']
            adp_data3 = day_df['밴드하단']
            adp = mpf.make_addplot(adp_data)
            adp2 = mpf.make_addplot(adp_data2)
            adp3 = mpf.make_addplot(adp_data3)
            # adp = mpf.make_addplot(day_df['b_upper'])
            mpf.plot(day_df, type='candle', volume=True, addplot=[adp, adp2, adp3],
                     style=s, title=f'DAY_CHART[{date.strftime("%Y:%m:%d")} bollinger upper over]')
            '''


if __name__ == '__main__':
    # bollinger = BollingerTrader()
    app = QApplication(sys.argv)
    point_window = PointWindow()
    point_window.show()
    app.exec_()