import sqlite3

con = sqlite3.connect("minute_chart'01'.db")
cur = con.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cur.fetchall()[-1])
# print(cur.fetchall())
# print(curtable)
