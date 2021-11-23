import sys
import sqlite3
from PyQt5.QtWidgets import *
from mplfinance.original_flavor import candlestick2_ohlc
import matplotlib.pyplot as plt
import pandas as pd


class Graph:
    def __init__(self):
        DB_KOSDAQ_DAY = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(day).db"
        DB_KOSDAQ_MIN = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(1min).db"

        con = sqlite3.connect(DB_KOSDAQ_MIN)
        df_min = pd.read_sql(f"SELECT * FROM '069330' WHERE 체결시간 LIKE '20210518%' ORDER BY 체결시간",
                             con, index_col='체결시간', parse_dates='체결시간')
        con.close()

        print(df_min)

        df_min.index.name = 'date'
        df_min.columns = ['close', 'open', 'high', 'low', 'volume']
        df_min = df_min[['open', 'high', 'low', 'close', 'volume']]
        # -----------------------------------------------
        df_min['cum_volume'] = df_min['volume'].cumsum()
        # df_min['volume_ratio'] = \
            # df_min['cum_volume'].apply(lambda x: round(x / volume20, 1))  # todo 여기수정필요
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


        # df_min['day_mean20'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl19)[0])
        # df_min['day_upperB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl19)[1])
        # df_min['day_lowerB'] = df_min['종고저평균'].apply(lambda x: _mean20_cal(x, chl19)[2])
        # df_min['day_bandWidth'] = (df_min['day_upperB'] - df_min['day_lowerB']) / df_min['day_mean20']
        # df_min['bWidth_ratio'] = round(df_min['day_bandWidth'] / BWidth_1, 2)
        df_min['next_open'] = df_min['open'].shift(-1)
        # print('df_min', df_min)


        fig = plt.figure(figsize=(15, 9))
        ax = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)
        candlestick2_ohlc(ax, df_min['open'], df_min['high'], df_min['low'],
                          df_min['close'], width=0.8,
                          colorup='r', colordown='b')

        x_list = range(len(df_min.index))
        ax.set_xticks(range(0, len(df_min.index), 5))
        ax.set_xticks(x_list, minor=True)
        name_list = [v.strftime("%H%M") for i, v in enumerate(df_min.index)]
        name_list = [name_list[i] for i in range(0, len(df_min.index), 5)]
        ax.set_xticklabels(name_list, rotation=90)
        plt.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    graph = Graph()
    app.exec_()