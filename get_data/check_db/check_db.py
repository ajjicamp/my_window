# git test
import sqlite3
import datetime

con = sqlite3.connect("D:/db/Candle_day/b_day01.db")
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
table = cur.fetchall()
print('테이블', table)
table_list = [t[0] for t in table]
print('TABLE LIST', table_list)
print('총테이블', len(table))
count = 0
miss_list = []
for t in table_list:
    # cur.execute("SELECT 체결시간 FROM %s ORDER BY 체결시간 desc" % t)
    cur.execute("SELECT 일자 FROM %s ORDER BY 일자 desc" % t)
    last_record = cur.fetchone()
    # if last_record[0] != '20211013153000':
    if last_record[0] != '20211013':
        miss_list.append(last_record[0])
        count += 1
        print(t ,last_record[0])
# print('틀린레코드', count)
# print('miss list', miss_list)
# '''
#     cur.execute("SELECT 체결시간 FROM %s" % t)
    cur.execute("SELECT 일자 FROM %s" % t)
    chegyeol_time = [c[0] for c in cur.fetchall()]
    # print(chegyeol_time)

    count = {}
    for i in chegyeol_time:
        try:
            count[i] += 1
        except:
            count[i] = 1

    # print('count', count)
    duple_cnt = 0
    cnt_1 = 0
    for v in count.values():
        if v >1:
            duple_cnt += 1
        if v == 1:
            cnt_1 += 1
    print(t, '총길이', len(count), '중복수', duple_cnt, '1인수', cnt_1)

