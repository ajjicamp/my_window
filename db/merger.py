import sqlite3

con = sqlite3.connect("day_chart.db")
cur = con.cursor()
cur.execute("dum")