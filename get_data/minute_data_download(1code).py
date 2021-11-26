'''
분봉차트 1종목만 받는 모듈
'''

import os
from kiwoom_download import *
import sqlite3
import time

class MinuteDataDownload:
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect()
        codes = ['059270']
        db_name = 'C:/Users/USER/PycharmProjects/my_window/db/kosdaq(1min).db'
        self.minute_data_download(codes, db_name)

    def minute_data_download(self, codes, db_name):
        # print('minute_data_download start')

        for i, code in enumerate(codes):
            dfs = []
            time.sleep(3.6)
            count = 0

            df = self.kiwoom.block_request('opt10080', 종목코드=code, 틱범위=1,
                                           수정주가구분=1, output='주식분봉차트조회', next=0)

            # column 숫자로 변환
            int_column = ['현재가', '시가', '고가', '저가', '거래량']
            df[int_column] = df[int_column].replace('', 0)
            df[int_column] = df[int_column].astype(int).abs()
            columns = ['체결시간', '현재가', '시가', '고가', '저가', '거래량']
            df = df[columns].copy()
            dfs.append(df)
            # self.save_sqlite3(df, code, db_name)
            # print(f"{code}다운로드 중")

            while self.kiwoom.tr_remained == True:
                print(f"{code}다운로드 중 {count}")
                time.sleep(0.2)
                # time.sleep(3.6)
                # sys.stdout.write(f'/r코드번호{code} 진행중: {self.start + i}/{self.end} ---> 연속조회 {count + 1}/82')
                count += 1

                df = self.kiwoom.block_request('opt10080', 종목코드=code, 틱범위=1, 수정주가구분=1,
                                        output='주식분봉차트조회', next=2)

                # column 숫자로 변환
                int_column = ['현재가', '시가', '고가', '저가', '거래량']
                df[int_column] = df[int_column].astype(int).abs()
                columns = ['체결시간', '현재가', '시가', '고가', '저가', '거래량']
                df = df[columns].copy()
                dfs.append(df)
                # self.save_sqlite3(df, code, db_name)

            print('dfs', dfs)
            dfs = pd.concat(dfs, ignore_index=True)
            print('concat_dfs', dfs)
            con = sqlite3.connect(db_name)
            dfs.to_sql(code, con, if_exists='replace', index=False)
            con.commit()
            con.close()

    def update_sqlite3(self, df, code, db_name):
        # self.lock.acquire()
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        out_name = f"'{code}'"
        query = f"CREATE TABLE IF NOT EXISTS '{code}' (체결시간 text PRIMARY KEY, \
                    현재가 integer, 시가 integer, 고가 integer, 저가 integer, 거래량 integer)"
        cur.execute(query)

        record_data_list = str(tuple(df.apply(lambda x: tuple(x.tolist()), axis=1)))[1:-1]
        if record_data_list[-1] == ',':
            record_data_list = record_data_list[:-1]
        sql_syntax = "INSERT OR IGNORE INTO %s VALUES %s" % (out_name, record_data_list)
        cur.execute(sql_syntax)
        con.commit()
        con.close()
        # self.lock.release()
        # self.insert_bulk_record(con, db_name, out_name, df)


if __name__ == '__main__':
    m_data_download = MinuteDataDownload()