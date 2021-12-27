import sqlite3
from multiprocessing import Process, Queue, Lock, current_process, active_children
from kiwoom_download import *
import datetime
import time
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.setting import *
from login.manuallogin22 import find_window, manual_login, auto_on
from utility.static import strf_time, now, get_python_process
DB_PATH = "C:/Users/USER/PycharmProjects/my_window/db"
DB_LIST = ['kospi(1min).db', 'kosdaq(1min).db']

class MultiDB:
    def __init__(self, num, queue, lock):
        self.num = num
        self.queryQ = queue
        self.lock = lock
        self.kiwoom = Kiwoom(self.num)
        self.source_code(f'{DB_PATH}/{DB_LIST[0]}', 'KOSPI')
        self.source_code(f'{DB_PATH}/{DB_LIST[1]}', 'KOSDAQ')

    def source_code(self, db_name, market):
        print('db_name', db_name)
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_list = [code[0] for code in cur.fetchall()]
        print('tablelist', table_list)

        d_num = int(self.num) - 1
        codes = [code for i, code in enumerate(table_list) if i % 4 == d_num]
        print(f'{self.num} codes {codes}')

        self.update(codes, db_name, market)

    def update(self, codes, db_name, market):
        # today = datetime.datetime.now().strftime('%Y%m%d')
        for i, code in enumerate(codes):
            time.sleep(3.6)
            self.lock.acquire()
            df = self.kiwoom.block_request('opt10080', 종목코드=code, 틱범위=1, 수정주가구분=1,
                                           output='주식분봉차트조회', next=0)
            self.lock.release()
            # column 숫자로 변환
            int_column = ['현재가', '시가', '고가', '저가', '거래량']
            df[int_column] = df[int_column].replace('', 0)
            df[int_column] = df[int_column].astype(int).abs()
            columns = ['체결시간', '현재가', '시가', '고가', '저가', '거래량']
            df = df[columns].copy()
            self.queryQ.put([df, code, db_name])
            print(f'[{now()}] {market} {code} {self.num} 데이터 다운로드 중 ... '
                  f'[{i}/{len(codes)}] --')

            # 업데이트할 때는 연속조회 불필요, 만약 업데이트가 많이 밀렸을 경우에는 그만큼 반복
            # dfs.append(df)
            count = 0
            while self.kiwoom.tr_remained == True:
                count += 1
                time.sleep(3.6)
                # sys.stdout.write(f'\r코드번호{code} 진행중: {self.start + i}/{self.end} ---> 연속조회 {count + 1}/82')
                self.lock.acquire()
                df = self.kiwoom.block_request('opt10080', 종목코드=code, 틱범위=1, 수정주가구분=1,
                                               output='주식분봉차트조회', next=2)
                self.lock.release()

                # column 숫자로 변환
                int_column = ['현재가', '시가', '고가', '저가', '거래량']
                df[int_column] = df[int_column].astype(int).abs()
                columns = ['체결시간', '현재가', '시가', '고가', '저가', '거래량']
                df = df[columns].copy()
                # df = df[::-1]
                self.queryQ.put([df, code, db_name])
                # 못 받은 데이터만큼만 반복
                if count == 1:
                    break

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
            if type(data[0]) == pd.DataFrame:
                self.save_sqlite3(data[0], data[1], data[2])

            elif data == '다운로드완료':
                print('한개 process 다운로드완료')

            elif data == '모든작업종료':
                print("queryQ 종료합니다.")
                break
            else:
                print('에러발생')

    def save_sqlite3(self, df, code, db_name):
        # lock 시간이 길면 안될 수도 있다 그러면 commit을 모아서 한다.
        self.lock.acquire()
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        out_name = f"'{code}'"
        '''
        query = "CREATE TABLE IF NOT EXISTS {} (체결시간 text PRIMARY KEY, \
                    현재가 integer, 시가 integer, 고가 integer, 저가 integer, 거래량 integer)".format(out_name)
        cur.execute(query)
        '''
        record_data_list = str(tuple(df.apply(lambda x: tuple(x.tolist()), axis=1)))[1:-1]
        if record_data_list[-1] == ',':
            record_data_list = record_data_list[:-1]
        sql_syntax = "INSERT OR IGNORE INTO %s VALUES %s" % (out_name, record_data_list)
        cur.execute(sql_syntax)
        con.commit()
        con.close()
        self.lock.release()


if __name__ == '__main__':
    queryQ = Queue()
    lock = Lock()

    # Query process start
    p_q = Process(name="Process_Query", target=Query, args=(queryQ, lock))
    p_q.start()

    num_list = ['01', '02', '03', '04']
    # num_list = ['01']
    for num in num_list:
        # 자동로그인 파일삭제
        login_info = f'{openapi_path}/system/Autologin.dat'
        # print('login_info', login_info)
        if os.path.isfile(login_info):
            os.remove(f'{openapi_path}/system/Autologin.dat')
        print('/n 자동 로그인 설정 파일 삭제 완료/n')
        proc_name = f'Process{num}'
        Process(name=proc_name, target=MultiDB, args=(num, queryQ, lock)).start()
        while find_window('Open API login') == 0:
            print(' 로그인창 열림 대기 중 .../n')
            time.sleep(1)
        print(' 아이디 및 패스워드 입력 대기 중 .../n')
        time.sleep(5)
        manual_login(int(num))
        print(' 아이디 및 패스워드 입력 완료/n')
        sleep_time = 50 if num == '01' else 30
        time.sleep(sleep_time)

    # 다 끝나고 나면 ...
    while True:
        time.sleep(1)
        if len(active_children()) == 1 and active_children()[0].name == "Process_Query":
            print("하나밖에 없음")
            break

    time.sleep(3)
    print("모든프로세스 다운로드 종료")
    queryQ.put("모든작업종료")

    p_q.join()
    # 프린트 해보면 안다.
    print('?????')
    p_q.close()
