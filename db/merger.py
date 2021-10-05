import sqlite3

import pandas as pd

con = sqlite3.connect("copy_day.db")
cur = con.cursor()
cur.execute("DELETE FROM a000020 WHERE 일자 < '20180705'")
con.commit()
con.close()

con = sqlite3.connect("basic.db")
cur = con.cursor()
con.execute("ATTACH 'copy_day.db' as 'dba'")

# con.execute("BEGIN")
'''
for row in con.execute("SELECT * FROM dba.sqlite_master WHERE type='table'"):
    # print('row', row[1])
    query = "SELECT * FROM " + row[1]
    cur.execute(query)
    result = str(cur.fetchall())[1:-1]
    if result[-1] == ',':
        result = result[:-1]
    # print('result', result)
    # combine = "INSERT OR IGNORE INTO" + row[1] + " VALUES " + result
    combine = "INSERT OR IGNORE INTO %s VALUES %s" % (row[1], result)
    print('combine\n ===================', combine, 'end')
    cur.execute(combine)
    con.commit()
    con.execute("DETACH database dba")
'''