'''
This file contains a simple animation demo using mplfinance "external axes mode".
Note that presently mplfinance does not support "blitting" (blitting makes animation
more efficient).  Nonetheless, the animation is efficient enough to update at least
once per second, and typically more frequently depending on the size of the plot.
'''

import sqlite3
import pandas as pd
import mplfinance as mpf
import matplotlib.animation as animation

# idf = pd.read_csv('data/SPY_20110701_20120630_Bollinger.csv',index_col=0,parse_dates=True)
# con = sqlite3.connect("bollinger.db")

con = sqlite3.connect(f"C:/Users/USER/PycharmProjects/my_window/db/kosdaq(day).db")
idf = pd.read_sql("SELECT * FROM '002680' WHERE 일자 > '20210501' ORDER BY 일자",
                  con, index_col=None)
idf['일자'] = pd.to_datetime(idf['일자'])
idf = idf.reset_index(drop=True).set_index('일자')
idf.index.name = 'date'
idf.columns = ['close', 'open', 'high', 'low', 'volume', 'amount']
idf = idf[['open', 'high', 'low', 'close', 'volume', 'amount']]

print('idf', idf)

print(idf.shape)
print(idf.head(3))
print(idf.tail(3))
df = idf.loc['2021-07-01':'2021-08-31',:]
# df = idf.loc['20210701':'20210831', :]

print('df', df)

fig = mpf.figure(style='charles', figsize=(7, 8))
ax1 = fig.add_subplot(2, 1, 1)
ax2 = fig.add_subplot(3, 1, 3)

def animate(ival):
    if (20+ival) > len(df):
        print('no more data to plot')
        ani.event_source.interval *= 3
        if ani.event_source.interval > 12000:
            exit()
        return
    data = df.iloc[0:(20+ival)]
    ax1.clear()
    ax2.clear()
    mpf.plot(data, ax=ax1, volume=ax2, type='candle')

ani = animation.FuncAnimation(fig, animate, interval=250)

mpf.show()
