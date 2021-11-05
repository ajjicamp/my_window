import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
import backtrader as bt
import sqlite3
import pandas as pd

# Create a subclass of Strategy to define the indicators and logic

class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30   # period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

    def next(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy()  # enter long

        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position


cerebro = bt.Cerebro() # create a "Cerebro" engine instance # 삼성전자의 '005930.KS' 코드를 적용하여 데이터 획득
con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/db/kosdaq(day).db")

for idx, code in enumerate(['000250', '000440']):
    day_df = pd.read_sql(f"SELECT * FROM '{code}' WHERE 일자 > 20210101", con, index_col=None)
    day_df['일자'] = pd.to_datetime(day_df['일자'])
    day_df = day_df.reset_index(drop=True).set_index('일자')
    day_df.index.name = 'date'
    # day_df.columns = ['Close', 'Open', 'High', 'Low', 'Volume', 'Amount']
    # day_df = day_df[['Open', 'High', 'Low', 'Close', 'Volume', 'Amount']]
    day_df.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
    day_df = day_df[['open', 'high', 'low', 'close', 'volume', 'amount']]
    data = bt.feeds.PandasData(dataname=day_df)
    cerebro.adddata(data, name=code)
cerebro.broker.setcash(10000000) # 초기 자본 설정
cerebro.broker.setcommission(commission=0.00015) # 매매 수수료는 0.015% 설정
cerebro.addstrategy(SmaCross) # 자신만의 매매 전략 추가
cerebro.run() # 백테스팅 시작
# Get final portfolio Value
portvalue = cerebro.broker.getvalue()
pnl = portvalue - 10000000
#Print out the final result
print('Final Portfolio Value: ${}'.format(portvalue))
print('P/L: ${}'.format(pnl))
print((portvalue-10000000)/10000000*100, '%')
#Visualize
# cerebro.plot(style='candlestick')
cerebro.plot()