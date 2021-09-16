import os
import sys
import sqlite3
import pandas as pd
import zipfile
import matplotlib.pyplot as plt
from kiwoom import Kiwoom
# 한글폰트 깨짐방지
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False # 한글 폰트 사용시 마이너스 폰트 깨짐 해결

#  todo 코스피, 코스닥 종목을 불러와서 텍스트파일에 저장하는 모듈
def get_market_code():
    kiwoom = Kiwoom(login=True)
    kospi = kiwoom.GetCodeListByMarket('0')
    kosdaq = kiwoom.GetCodeListByMarket('10')

    with open('kospi_code.txt', 'w') as f:
        for data in kospi:
            f.write(f'{data}\n')

    with open('kosdaq_code.txt', 'w') as f:
        for data in kosdaq:
            f.write(f'{data}\n')
get_market_code()

# text file에 저장돼 있는 코스피코드 및 코스닥코드를 읽어와서 list에 저장.
kospi_list = []
with open('kospi_code.txt', 'r') as f:
    while True:
        data = f.readline().strip()
        if not data:
            break
        kospi_list.append(data)
kosdaq_list = []
with open('kosdaq_code.txt', 'r') as f:
    while True:
        data = f.readline().strip()
        if not data:
            break
        kosdaq_list.append(data)

# kospi, kosdaq 종목 전체에 대한 sql 일봉차트를 가져와서 dataframe에 저장(종목당 하나의 dataframe생성)
# sql data의 table 이름은  kospi ; 'a005930'로, kosdaq은 'b000020'형태로 저장되어 있음.
con = sqlite3.connect('d:/day_chart.db')
df = {}  # df[code] = pd.Dataframe
def create_daychart(codelist):      # args: kospi_list, kosdaq_list.
    for i, code in enumerate(codelist):
        sys.stdout.write(f'\rdb생성중: {i+1}/{len(codelist)}')
        try:
            table = f'a{code}' if codelist == kospi_list else f'b{code}'
            df[code] = pd.read_sql("SELECT * FROM" + " " + table, con, index_col=None)
        except Exception as e:
            print("에러발생", e)
        else:
            # 문자데이터를 숫자로 변경
            df[code][['현재가', '시가', '고가', '저가', '거래량']] \
               = df[code][['현재가', '시가', '고가', '저가', '거래량']].apply(pd.to_numeric)
            # '일자'를 기준으로 sort
            df[code].sort_values(by=['일자'], inplace=True, ignore_index=True)

            # df[code]['종가20'] = df[code]['현재가'].rolling(window=20).mean()    # 종가 20이평
            # 볼린저밴드값 구하기
            df[code]['종고저평균'] = (df[code]['현재가'] + df[code]['고가'] + df[code]['저가']) / 3
            df[code]['밴드기준선'] = df[code]['종고저평균'].rolling(window=20).mean()    # 밴드기준선
            df[code]['std20'] = df[code]['종고저평균'].rolling(window=20).std()    # 표준편차 20
            df[code]['밴드상단'] = df[code]['밴드기준선'] + df[code]['std20'] * 2
            df[code]['밴드하단'] = df[code]['밴드기준선'] - df[code]['std20'] * 2
            df[code]['밴드폭'] = (df[code]['밴드상단'] - df[code]['밴드하단']) / df[code]['밴드기준선']
            df[code]['밴드폭최대'] = df[code]['밴드폭'].rolling(window=120, min_periods=20).max()
            # df[code]['밴드폭평균'] = df[code]['밴드폭'].rolling(window=120, min_periods=20).mean()
            # df[code]['밴드zscore'] = df[code]['밴드폭'] - df

            # 거래량 이평 구하기
            df[code]['거래20'] = df[code]['거래량'].rolling(window=20).mean()   #거래량 20이평
            # print('밴드폭최대', df[code]['밴드폭최대'])
            # input('just')

# 코스피 종목 일봉차트값 구하기
create_daychart(kospi_list)
# 코스닥 종목 일봉차트 구하기
create_daychart(kosdaq_list)

# print('df 삼성전자', df['005930'])
######################
def daychart_trade(code, gubun):  # dfc = df[code] ; 600일분 일봉차트 dataframe
    dfc = df[code]
    dolpa = False  # 밴드돌파상태인지 아닌지 파악(즉, false이면 첫돌파)
    count = 0      # 수익시현한 회수 count
    profit = 0     # 일별 수익금액
    profit_sum = 0  # 종목별 수익금 합계

    df_profit = pd.DataFrame(columns=['일자', '손익', '매입가', '매도가', '고가', '저가', '상한선', '기준선', '하한선'])
    for i in range(20, len(dfc)-1):   # 종목별로 생성한 일봉데이터(600일분), 마지막 row는 제외;익일이 없으므로 청산불가
        # 매수조건 설정
        upper_over = dfc['현재가'][i] > dfc['밴드상단'][i-1]  # 밴드 상단돌파여부
        volume_over = dfc['거래량'][i] > dfc['거래20'][i-1] * 10  # 거래량 돌파여부
        # volume_over = dfc['거래량'][i] > dfc['거래량'][i-1] * 5  # 거래량 돌파여부
        band_width = dfc['밴드폭'][i-1] < dfc['밴드폭최대'][i-1] / 1

        # 매수기준가
        buy_price = dfc['현재가'][i]
        # buy_price = max(dfc['밴드상단'][i-1], dfc['시가'][i])

        # 매도기준가
        sell_price = dfc['시가'][i+1]

        if not dolpa and upper_over and volume_over and band_width:  # 첫돌파인지 파악
        # if not dolpa and volume_over and band_width:  # 첫돌파인지 파악
            count += 1
            profit = sell_price - buy_price  # 한건 수익
            data = (dfc['일자'][i], profit, buy_price, sell_price, dfc['고가'][i + 1], dfc['저가'][i + 1],
                    round(dfc['밴드상단'][i], 0), round(dfc['밴드기준선'][i], 0), round(dfc['밴드하단'][i], 0))
            df_profit.at[count] = data
        dolpa = upper_over  # 현재 돌파된 상황 ---> 다음 [i]에서 조건검토에 사용
        # profit_sum += profit  # 종목총수익

    # 한 종목 분석 완료하고 데이터 분석
    if count == 0:
        return
    # return  # 매수조건 성립이 하나도 없는 경우 리턴

    # 건별 트레이딩을 기록한 dataframe을 엑셀에 저장
    filename = f'd:/b_width/code_/{gubun}{code}.xlsx' # gubun == 'a' or 'b'
    with pd.ExcelWriter(filename, mode='w', engine='openpyxl') as writer:
            df_profit.to_excel(writer, index=False)

    # 종목별 트레이딩 집계하여 호출프로시저에 return
    # count
    profit_sum = df_profit['손익'].sum()
    buy_sum = df_profit['매입가'].sum()
    profit_rate = round(profit_sum / buy_sum * 100, 2)
    year_rate = round(profit_rate * 365, 2)
    buy_avrg = round(buy_sum / count, 0)
    sell_avrg = round(df_profit['매도가'].sum() / count, 0)

    total = (count, profit_sum, buy_sum, profit_rate, year_rate, buy_avrg, sell_avrg)
    return total

def calc_allcode(codelist, gubun):
    df_total = pd.DataFrame(columns=['총건수', '총수익', '총매입금액', '수익률(%)', '투자수익률(연간,%)',
                                     '평균매입가', '평균매도가'])
    for i, code in enumerate(codelist):
        # print(f'{i+1}/{len(codelist)}')
        sys.stdout.write(f'\r종목분석중: {i+1}/{len(codelist)}')
        try:
            # dfc = df[code]
            # print('dfc', dfc)
            # if not code == '271940':
            result = daychart_trade(code, gubun)
        except Exception as e:
            print(f'122line {code} 에러발생 {e}')
            # print('dfs', code, '\n', df[code])
            # stop = input("잠시대기:")
        else:
            if not result == "":
                df_total.at[code] = result
    total_count = df_total['총건수'].sum()
    total_profit = df_total['총수익'].sum()
    total_buy = df_total['총매입금액'].sum()
    total_profit_rate = total_profit / total_buy * 100
    total_year_rate = df_total['투자수익률(연간,%)'].sum()
    total_buy_avrg = df_total['평균매입가'].sum() / total_count
    total_sell_avrg = df_total['평균매도가'].sum() / total_count

    # df_total[]

    print(f"{gubun}: 총건수: {format(total_count, ',')}, 수익총계: {format(round(total_profit, 0), ',')}, "
          f"매입총계: {format(round(total_buy, 0), ',')},총수익률: {round(total_profit_rate, 2)}")

    # 전종목 집계결과 엑셀에 저장
    filename = 'd:/b_width/kospi_width.xlsx' if gubun == 'a' else 'd:/b_width/kosdaq_width.xlsx'
    with pd.ExcelWriter(filename, mode='w', engine='openpyxl') as writer:
        df_total.to_excel(writer)

calc_allcode(kospi_list, 'a')
calc_allcode(kosdaq_list, 'b')

"""
plt.figure(figsize=(9, 5))
plt.plot(df.index, df['현재가'], label='Close')
plt.plot(df.index, df['upper'], linestyle='dashed', label='Upper band')
plt.plot(df.index, df['ma20'], linestyle='dashed', label='Moving Average 20')
plt.plot(df.index, df['lower'], linestyle='dashed', label='Lower band')
plt.title(f'볼린저 밴드(20일, 2 표준편차)')
plt.legend(loc='best')
plt.show()
"""


