import sqlite3
import pandas as pd
import numpy as np

DB_KOSPI_MIN = "C:/Users/USER/PycharmProjects/my_window/db/kospi(1min).db"
DB_KOSDAQ_MIN = "C:/Users/USER/PycharmProjects/my_window/db/kosdaq(1min).db"

class GoldenCrossDeal:
    def __init__(self):
        con = sqlite3.connect(DB_KOSPI_MIN)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        self.kospi_table_list = [v[0] for v in cur.fetchall()]
        con.close()

        for table in self.kospi_table_list:
            con = sqlite3.connect(DB_KOSPI_MIN)
            df_kospi = pd.read_sql(f"SELECT * FROM '{table}' WHERE 체결시간 >= 20210701 and 체결시간 <= 20210930 ORDER BY 체결시간", con,
                                 index_col='체결시간', parse_dates='체결시간')
            con.close()

            print(df_kospi)
            input()

            df_kospi

if __name__ == '__main__':
    deal = GoldenCrossDeal()
