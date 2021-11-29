import sqlite3
import pandas as pd
import dateutil.parser
import numpy as np

db = "C:/Users/USER/PycharmProjects/my_window/backtest/bollinger05.db"
# table = "deal_1.1"
# table = "deal_1.5"
for i in np.arange(1.1, 4.1, 0.1):
    table = f"deal_{str(round(i, 1))}"

    con = sqlite3.connect(db)
    df = pd.read_sql(f"SELECT * FROM '{table}'", con)
    # 수익률이 양수인 경우만 필터링
    df = df[df['순이익률'] > 0]
    df['month'] = df['체결시간'].apply(lambda d: d[:6])
    df['time'] = df['체결시간'].apply(lambda t: t[8:10])
    df['밴드over'] = round((df['매수가'] / df['밴드상단'] - 1) * 100, 2)
    # df['매수후하락'] = round((df['매수가'] / df['저가'] - 1) * 100, 2)

    # df = df.reindex().set_index('체결시간')
    # df = df.sort_index()
    df['체결시간'] = df['체결시간'].apply(dateutil.parser.parse, dayfirst=True)

    # print(df.dtypes)
    # print(df)

    print(df.groupby('month').agg({'순이익': sum, '순이익률': 'mean'}))
    # print(df.groupby('time').agg({'종목번호': 'count', '순이익': sum, '순이익률': 'mean',
    #                               '돌파V배율': 'mean', '밴드상단': 'mean', '매수가': 'mean',
    #                               '밴드over': 'mean'}))
    print(table, '\n', df.groupby('time').agg({'종목번호': 'count', '순이익': sum, '순이익률': 'mean',
                                  '매수가': 'mean', '저가': 'mean', '촤저하락률': 'mean'}))
    input()

    # print(df['순이익률'].mean())
