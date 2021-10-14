import sqlite3
import datetime
import time

con = sqlite3.connect("D:/minute01.db")
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
namelist = cur.fetchall()
name = namelist[100]
print('table name', name)

name = 'b900270'
cur.execute("SELECT 체결시간 FROM %s" % name)
chegyeol_time = cur.fetchall()
ch_time_lists = [t[0] for t in chegyeol_time]

count={}
for i in ch_time_lists:
    try: count[i] += 1
    except: count[i]=1
cnt = 0
for v in count.values():
    if v > 1:
        cnt += 1
print('중복개수', cnt)

# print('중복개수', count)


# print('체결시간', chegyeol_time)
print('체결시간리스트', len(ch_time_lists),'개')

start = ch_time_lists[0][:12]
end = ch_time_lists[-1][:12]

start = datetime.datetime.strptime(start, '%Y%m%d%H%M')
end = datetime.datetime.strptime(end, '%Y%m%d%H%M')
print(start, end)
print('총시간(분)', end - start)
# print('총시간차', period)
# print('봉개수', period/3)


