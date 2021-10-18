import sqlite3
import pandas as pd
import datetime

con = sqlite3.connect('D:/DB/Candle_minute/minute01.db')
df = pd.read_sql('SELECT * FROM B000250', con, index_col=None)
df = df.sort_values('체결시간')
# print('df', df.iloc[0]['체결시간'], df.iloc[-1]['체결시간'])
# print(len(df))

# for i in range(len(df)):
#     df.at[i, '체결일자'] = df.at[i, '체결시간'][:8]

df['체결일자'] = df['체결시간'].apply(lambda x: x[:8])
df['순수시간'] = df['체결시간'].apply(lambda x: x[8:])

# print('df일자\n', df[['체결일자', '체결시간', '순수시간']])
# day_list = df['체결시간'].apply(lambda x: x[:8])
# print('day_list\n', day_list)

# print(df)

# 아래 코딩은 가능하다.
# ctime = df['체결시간'][(df['체결시간'] > '20211005000000') & (df['체결시간'] < '20211006000000')]
# print('ctime길이', len(ctime))

# 정상적인 분봉시간 만들기
time_list = []
start = '090000'
start_date = datetime.datetime.strptime(start, '%H%M%S')
for i in range(391):
    change_date = start_date + datetime.timedelta(minutes=i)
    str_date = datetime.datetime.strftime(change_date, '%H%M%S')
    if i < 380 or i == 390:
        time_list.append(str_date)
# print(time_list)

group_day = df.groupby('체결일자', as_index=False)
miss_time = []
for key, group in group_day:
    # print('key', key)
    # print('group', group)
    # print('type', type(group))
    # ctime = group['체결시간']

    # group['순수시간']
    net_time = [time for time in group['순수시간']]
    # print('net_time', net_time)

    for i, time in enumerate(time_list):
        # print(i, time)
        miss = f'{key}{time}'
        # print('miss', miss)
        if not (time in net_time):
            miss_time.append(miss)
print('miss_time', len(miss_time), miss_time)

