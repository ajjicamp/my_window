# 다운로드 받은 db의 날짜가 누락된 것이 있는지 확인하는 코드. 완전하게 일치함 별 쓸 일이 없을 것임.
import sqlite3
import pandas as pd

con = sqlite3.connect("d:/db/market_jisu.db")
df = pd.read_sql("SELECT * FROM kospi", con, index_col=None)
con.close()

# day_list는 코스피 업종차트데이트의 일자 리스트로써 누락없는 완전한 데이터.
day_list = [v for v in df['일자']]
# print('day_list\n', day_list)

con = sqlite3.connect("d:/db/candle_day/b_day04.db")
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
table_list = [val[0] for val in cur.fetchall()]
# print('table', table_list)
# con.close()

for table in table_list:
    df_day = pd.read_sql("SELECT 일자 FROM %s" % table, con, index_col=None)
    code_day = [day for day in df_day['일자']]
    code_day.sort()
    code_day.reverse()
    last_day = code_day[-1]
    print(last_day)
    # print('일자column값', code_day)
    index = day_list.index(last_day)
    day_list02 = day_list[:index+1]

    print(len(code_day), len(day_list02))
    if day_list02 == code_day:
        print("OK")
    else:
        print("맞지 않음")
        print("차이점: ", table, (set(day_list02) - set(code_day)))
        input("잠시대기")