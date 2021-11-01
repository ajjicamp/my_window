# sqlite3 db 업데이트 후 row 숫자 및 각 테이블의 (일자,체결시간) 체크.
# 날짜/체결시간 순서대로 빠진것 없는지도 체크,
import sqlite3
import pandas as pd
import datetime

DB_PATH = "C:/Users/USER/PycharmProjects/my_window/db"
# DB_PATH = "D:/db"

# LAST_DATE = datetime.datetime.now().strftime("%Y%h%m")
LAST_DATE = '20211028'
LAST_TIME = f'{LAST_DATE}153000'


class CheckDB:
    def __init__(self):
        self.check_db(f'{DB_PATH}/kospi(day).db', '일자', LAST_DATE)
        self.check_db(f'{DB_PATH}/kosdaq(day).db', '일자', LAST_DATE)
        self.check_db(f'{DB_PATH}/kospi(1min).db', '체결시간', LAST_TIME)
        self.check_db(f'{DB_PATH}/kosdaq(1min).db', '체결시간', LAST_TIME)

    def check_db(self, db, key, last_value):
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_list = [val[0] for val in cur.fetchall()]
        # print(f'{db}의 table숫자 {len(table_list)}')

        miss_table = 0
        for table in table_list:
            cur.execute(f"SELECT {key} FROM '{table}' ORDER BY {key} desc")
            data = cur.fetchone()[0]
            if data != last_value:
                miss_table += 1
        print(f'오류table 숫자 {db}: {miss_table}/{len(table_list)}')


if __name__ == '__main__':
    checkdb = CheckDB()