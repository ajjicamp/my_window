import sqlite3

DB_PATH = '/my_window/db'
DB_FILE = f'{DB_PATH}/b_minute04.db'

con = sqlite3.connect(DB_FILE)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
table_list = [v[0] for v in cur.fetchall()]
# print(table_list)

for i, table in enumerate(table_list):
    new_table = table[1:]
    cur.execute(f"ALTER TABLE '{table}' RENAME TO '{new_table}'")
    print(f"{i}번 table name 변경중....")

print('변경완료')
con.commit()
con.close()