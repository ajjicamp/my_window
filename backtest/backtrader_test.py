import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
import backtrader as bt
import sqlite3
import pandas as pd

# Create a subclass of Strategy to define the indicators and logic

class maCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = (
    ('sma1', 20),
    ('sma2', 30),
    ('oneplot', True)
    )

    def __init__(self):
        self.inds = dict()
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['sma1'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma1)
            self.inds[d]['sma2'] = bt.indicators.SimpleMovingAverage(
                d.close, period=self.params.sma2)
            self.inds[d]['cross'] = bt.indicators.CrossOver(self.inds[d]['sma1'],self.inds[d]['sma2'])
            if i > 0:
                if self.p.oneplot == True:
                    d.plotinfo.plotmaster = self.datas[0]

    def next(self):
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.date(), d._name
            pos = self.getposition(d).size
            if not pos:
                if self.inds[d]['cross'][0] == 1:
                    self.buy(data=d, size=10)
                elif self.inds[d]['cross'][0] == -1:
                    self.sell(data=d, size=10)
            else:
                if self.inds[d]['cross'][0] == 1:
                    self.close(data=d)
                    self.buy(data=d, size=10)
                elif self.inds[d]['cross'][0] == -1:
                    self.close(data=d)
                    self.sell(data=d, size=10)

    def notify_trade(self, trade):
        dt = self.data.datetime.date()
        if trade.isclosed:
            print('{} {} Closed: PnL Gross {}, Net {}'.format(
                dt, trade.data._name, round(trade.pnl, 2), round(trade.pnlcomm, 2)))

startcash = 1000000
cerebro = bt.Cerebro() # create a "Cerebro" engine instance # 삼성전자의 '005930.KS' 코드를 적용하여 데이터 획득
# cerebro.addstrategy(maCross, oneplot=False)
cerebro.addstrategy(maCross, oneplot=False)

con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/db/kosdaq(day).db")
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
table_list = [v[0] for v in cur.fetchall()]

df_list = []
for idx, code in enumerate(table_list[0:10]):
    day_df = pd.read_sql(f"SELECT * FROM '{code}' WHERE 일자 > 20210101", con, index_col=None)
    day_df['일자'] = pd.to_datetime(day_df['일자'])
    day_df = day_df.reset_index(drop=True).set_index('일자')
    day_df.index.name = 'date'
    # day_df.columns = ['Close', 'Open', 'High', 'Low', 'Volume', 'Amount']
    # day_df = day_df[['Open', 'High', 'Low', 'Close', 'Volume', 'Amount']]
    day_df.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
    day_df = day_df[['open', 'high', 'low', 'close', 'volume', 'amount']]

    df_list.append(day_df)
    data = bt.feeds.PandasData(dataname=df_list[idx])
    cerebro.adddata(data, name=code)

cerebro.broker.setcash(startcash) # 초기 자본 설정
# cerebro.broker.setcommission(commission=0.00015) # 매매 수수료는 0.015% 설정
cerebro.run() # 백테스팅 시작
# Get final portfolio Value
portvalue = cerebro.broker.getvalue()
pnl = portvalue - startcash
#Print out the final result
print('Final Portfolio Value: ${}'.format(portvalue))
print('P/L: ${}'.format(pnl))
print((portvalue-startcash)/startcash*100, '%')
#Visualize
# cerebro.plot(style='candlestick')
cerebro.plot()