# sqlite3 db 업데이트 후 row 숫자 및 각 테이블의 (일자,체결시간) 체크.
# 날짜/체결시간 순서대로 빠진것 없는지도 체크,
import sqlite3
import pandas as pd


DB_PATH = "C:/Users/USER/PycharmProjects/my_window/db"

DAY_KOSPI_DB_LIST = [f'{DB_PATH}/candle_day/a_day01.db',
                     f'{DB_PATH}/candle_day/a_day02.db',
                     f'{DB_PATH}/candle_day/a_day03.db',
                     f'{DB_PATH}/candle_day/a_day04.db',
                     ]

DAY_KOSDAQ_DB_LIST = [f'{DB_PATH}/candle_day/b_day01.db',
                      f'{DB_PATH}/candle_day/b_day02.db',
                      f'{DB_PATH}/candle_day/b_day03.db',
                      f'{DB_PATH}/candle_day/b_day04.db',
                      ]

MINUTE_KOSPI_DB_LIST = [f'{DB_PATH}/candle_minute/a_minute01.db',
                        f'{DB_PATH}/candle_minute/a_minute02.db',
                        f'{DB_PATH}/candle_minute/a_minute03.db',
                        f'{DB_PATH}/candle_minute/a_minute04.db',
                        ]

MINUTE_KOSDAQ_DB_LIST = [f'{DB_PATH}/candle_minute/b_minute01.db',
                         f'{DB_PATH}/candle_minute/b_minute02.db',
                         f'{DB_PATH}/candle_minute/b_minute03.db',
                         f'{DB_PATH}/candle_minute/b_minute04.db',
                         ]

ALL_CODE = DAY_KOSPI_DB_LIST + DAY_KOSDAQ_DB_LIST + MINUTE_KOSPI_DB_LIST + MINUTE_KOSDAQ_DB_LIST
LAST_DATE ="20211019"
LAST_TIME ="20211019153000"


class CheckDB:
    def __init__(self):
        self.check_db(DAY_KOSPI_DB_LIST, '일자', LAST_DATE)
        self.check_db(DAY_KOSDAQ_DB_LIST, '일자', LAST_DATE)
        self.check_db(MINUTE_KOSPI_DB_LIST, '체결시간', LAST_TIME)
        self.check_db(MINUTE_KOSDAQ_DB_LIST, '체결시간', LAST_TIME)

    def check_db(self, db_list, key, last_value):
        for db in db_list:
            con = sqlite3.connect(db)
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_list = [val[0] for val in cur.fetchall()]
            # print(f'{db}의 table숫자 {len(table_list)}')

            miss_table = 0
            for table in table_list:
                cur.execute(f"SELECT {key} FROM {table} ORDER BY {key} desc")
                data = cur.fetchone()[0]
                if data != last_value:
                    miss_table += 1
                    if db == 'C:/Users/USER/PycharmProjects/my_window/db/candle_minute/a_minute04.db':
                        print(table, data)
                        input()
            print(f'오류table 숫자 {db}: {miss_table}/{len(table_list)}')


if __name__ == '__main__':
    checkdb = CheckDB()