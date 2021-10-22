'''
일봉차트데이트 업데이트 하는 모듈
코스피, 코스닥 구분하여 4개의 멀리프로세서로 다운로드
todo 새로 추가되는 종목이 있으면 확인하여 update 한다.
'''
from multiprocessing import Process, Queue, Lock, current_process, active_children
import logging
import sqlite3
import datetime
import time
import logging
from kiwoom_download import *
# from telegram_test import *
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
# from utility.setting import openapi_path, sn_brrq, sn_oper, db_day, db_Day
from utility.setting import openapi_path, sn_brrq, sn_oper
from login.manuallogin22 import find_window, manual_login, auto_on
from utility.static import strf_time, now
# logging.basicConfig(filename="../log.txt", level=logging.ERROR)
# logging.basicConfig(level=logging.INFO)
# app = QApplication(sys.argv)


class DayDataDownload:
    def __init__(self, num, queryQ, lock):
        self.num = num
        self.queryQ = queryQ
        self.lock = lock

        self.gubun = None
        self.codes = None
        self.start = None
        self.end = None
        self.codes = None

        self.kiwoom = Kiwoom(self.num)

        kospi = f'D:/db/a_day{self.num}.db'
        kosdaq = f'D:/db/b_day{self.num}.db'

        # multiprocessing으로 하므로 아래 함수를 두번 같이 실행하면 안된다.???
        self.Update(kospi)
        self.Update(kosdaq)

    def Update(self, db_name):
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        low_data = cur.fetchall()

        codes = [data[0] for data in low_data]
        print('크기', len(codes))
        con.close()

        # ----------------------------------------------------------------
        # start num ; 디폴트는 0, 중간에 멈췄을 경우는 멈춘 지점으로 직접 수정
        # ----------------------------------------------------------------

        if self.num == '01':
            self.start = 0
        if self.num == '02':
            self.start = 0
        if self.num == '03':
            self.start = 0
        if self.num == '04':
            self.start = 0

        # 여기서 self.end는 각 프로세서별 codes길이가 다르므로 자동 설정됨.
        self.end = len(codes)

        codes = codes[self.start: self.end]
        today = datetime.datetime.now().strftime('%Y%m%d')
        for i, code in enumerate(codes):
            time.sleep(3.6)
            count = 0

            self.lock.acquire()
            df = self.kiwoom.block_request('opt10081', 종목코드=code, 기준일자=today, 수정주가구분=1,
                                     output='주식일봉차트조회', next=0)
            self.lock.release()

            int_column = ['현재가', '시가', '고가', '저가', '거래량', '거래대금']
            df[int_column] = df[int_column].replace('', 0)
            df[int_column] = df[int_column].astype(int).abs()
            columns = ['일자', '현재가', '시가', '고가', '저가', '거래량', '거래대금']
            df = df[columns].copy()

            self.queryQ.put([df, code, db_name])
            print(f'[{now()}] {code} {self.num} 데이터 다운로드 중 ... '
                  f'[{self.start + i + 1}/{self.end}] --{count}')

            '''           
            while self.tr_remained == True:
                time.sleep(3.6)
                # sys.stdout.write(f'\r코드번호{code} 진행중: {self.start + i}/{self.end} ---> 연속조회 {count + 1}/82')
                count += 1

                self.lock.acquire()
                df = self.block_request('opt10081', 종목코드=code, 기준일자=today, 수정주가구분=1,
                                        output='주식일봉차트조회', next=2)
                self.lock.release()

                # column 숫자로 변환
                int_column = ['현재가', '시가', '고가', '저가', '거래량', '거래대금']
                df[int_column] = df[int_column].astype(int).abs()
                columns = ['일자', '현재가', '시가', '고가', '저가', '거래량', '거래대금']
                df = df[columns].copy()
                # df = df[::-1]
                self.queryQ.put([df, code, db_name])
                print(f'[{now()}] {code} {self.num} 데이터 다운로드 중 ... '
                      f'[{self.start + i + 1}/{self.end}] --{count}')

                # dfs.append(df)
                # if count == 10:
                #     break
            '''
        proc = current_process()
        print('다운로드 완료, current proces=================', proc.name)
        self.queryQ.put('다운로드완료')


class Query:
    def __init__(self, queryQQ, lock):
        self.queryQ = queryQQ
        self.lock = lock
        self.Start()

    def Start(self):
        while True:
            data = self.queryQ.get()  # data = [df, code, db_name]
            if data != '다운로드완료':
                self.save_sqlite3(data[0], data[1], data[2])
            else:
                print('한개 process 다운로드완료')

    def save_sqlite3(self, df, code, db_name):
        # self.lock.acquire()
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        out_name = f"'{code}'"
        '''
        query = "CREATE TABLE IF NOT EXISTS {} (일자 text PRIMARY KEY, 현재가 integer, " \
                "시가 integer, 고가 integer, 저가 integer, 거래량 integer, 거래대금 integer)".format(out_name)
        cur.execute(query)
        '''
        record_data_list = str(tuple(df.apply(lambda x: tuple(x.tolist()), axis=1)))[1:-1]
        if record_data_list[-1] == ',':
            record_data_list = record_data_list[:-1]
        sql_syntax = "INSERT OR IGNORE INTO %s VALUES %s" % (out_name, record_data_list)
        cur.execute(sql_syntax)
        con.commit()
        con.close()
        # self.lock.release()
        # self.insert_bulk_record(con, db_name, out_name, df)

    def insert_bulk_record(self, con, db_name, table_name, record):
        # 위 save_sqlite3()함수로 합쳤다
        print('insert_bulk')
        record_data_list = str(tuple(record.apply(lambda x: tuple(x.tolist()), axis=1)))[1:-1]
        # record_data_list = str(tuple(record.apply(lambda x: tuple(x.tolist()), axis=1)))
        # print("record_data_list", record_data_list)
        if record_data_list[-1] == ',':
            record_data_list = record_data_list[:-1]
        # sql_syntax = "INSERT OR IGNORE INTO %s, %s VALUES %s" %(db_name, table_name, record_data_list)

        con = sqlite3.connect(db_name)
        cur = con.cursor()
        sql_syntax = "INSERT OR IGNORE INTO %s VALUES %s" % (table_name, record_data_list)
        cur.execute(sql_syntax)
        con.commit()
        con.close()


if __name__ == '__main__':
    queryQ = Queue()
    lock = Lock()

    # Query process start
    p_q = Process(name="Process_Query", target=Query, args=(queryQ, lock))
    p_q.start()

    num_list = ['01', '02', '03', '04']
    for num in num_list:
        # 자동로그인 파일삭제
        login_info = f'{openapi_path}/system/Autologin.dat'
        # print('login_info', login_info)
        if os.path.isfile(login_info):
            os.remove(f'{openapi_path}/system/Autologin.dat')
        print('/n 자동 로그인 설정 파일 삭제 완료/n')
        proc_name = f'Process{num}'
        Process(name=proc_name, target=DayDataDownload, args=(num, queryQ, lock)).start()
        while find_window('Open API login') == 0:
            print(' 로그인창 열림 대기 중 .../n')
            time.sleep(1)
        print(' 아이디 및 패스워드 입력 대기 중 .../n')
        time.sleep(5)
        manual_login(int(num))
        print(' 아이디 및 패스워드 입력 완료/n')
        time.sleep(30)

    # 다 끝나고 나면 ...
    while not len(active_children()) == 1:
        time.sleep(1)
        # live_process = active_children()
        # print('살아있는 자식 프로세스', live_process)
        if active_children()[0].name == "Process_Query":
            # print("하나밖에 없음")
            break
    time.sleep(3)
    print("모든프로세스 다운로드 종료")
    p_q.join()
    p_q.close()

