import pandas as pd
import mplfinance as mpf
import plotly.graph_objects as go
import plotly.express as px
import plotly.subplots as sub
import sqlite3
DB_PATH = "C:/Users/USER/PycharmProjects/my_window/db"
# db = f"{DB_PATH}/kospi(day).db"
kosdaq_day_db = f"{DB_PATH}/kosdaq(day).db"
kosdaq_min_db = f"{DB_PATH}/kosdaq(1min).db"

con = sqlite3.connect(kosdaq_min_db)
df = pd.read_sql("SELECT * FROM '000250' WHERE 체결시간 LIKE '20211022%' ORDER BY 체결시간",
                 con, index_col=None)
con.close()

df['체결시간'] = pd.to_datetime(df['체결시간'])
df = df.reset_index(drop=True).set_index('체결시간')
df.index.name = 'date'
df.columns = ['close', 'open', 'high', 'low', 'volume']
df = df[['open', 'high', 'low', 'close', 'volume']]
df['b_upper'] = [48100 for _ in range(len(df.index))]

adp = mpf.make_addplot(df['b_upper'])

colorset = mpf.make_marketcolors(up='tab:red', down='tab:blue', volume='tab:blue')
s = mpf.make_mpf_style(marketcolors=colorset)
# mpf.plot(df[:60], type='candle', volume=True, style=s)
mpf.plot(df, type='candle', volume=True, addplot=adp, style=s)

# candle = ptl.Candlestick(x=df.index)
candle = go.Candlestick(x=df.index,
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        increasing_line_color='red',
                        decreasing_line_color='blue',
                        )
upper_plot = go.Line(x=df.index, y=df['b_upper'])
# upper_plot = px.line(x=df.index, y=df['b_upper'])
volume_bar = go.Bar(x=df.index, y=df['volume'])
fig = sub.make_subplots(rows=2, cols=1, row_heights=[3, 1], shared_xaxes=True, vertical_spacing=0.02)

fig.add_trace(candle, row=1, col=1)
fig.add_trace(upper_plot, row=1, col=1)
fig.add_trace(volume_bar, row=2, col=1)

fig.update_layout(
                  title='Samsung stock price',
                  yaxis1_title='Stock Price',
                  yaxis2_title='Volume',
                  xaxis2_title='periods',
                  xaxis1_rangeslider_visible=False,
                  xaxis2_rangeslider_visible=True,
                  )
# fig = go.Figure(data=candle)
fig.show()