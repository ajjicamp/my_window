import sqlite3

con = sqlite3.connect("D:\minute_chart'01'.db")
cur = con.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(str(cur.fetchall()[-1][0]))
# print(cur.fetchall())
# print(curtable)
