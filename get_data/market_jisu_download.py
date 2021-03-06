import os
import sys
from multiprocessing import Process, Queue, Lock
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
import logging
import pandas as pd
import pythoncom
import zipfile
import sqlite3
import datetime
import time
import logging

# from telegram_test import *
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.setting import openapi_path, sn_brrq, sn_oper, db_day, db_minute
from login.manuallogin22 import find_window, manual_login, auto_on
from utility.static import strf_time, now

# logging.basicConfig(filename="../log.txt", level=logging.ERROR)
# logging.basicConfig(level=logging.INFO)

app = QApplication(sys.argv)

class MarketJisuDownload:
    def __init__(self, queryQ, lock):
        # self.db_name = 'D:/kospi_jisu.db'
        self.queryQ = queryQ
        self.lock = lock
        self.connected = False  # for login event
        self.received = False  # for tr event
        self.tr_items = None  # tr input/output items
        self.tr_data = None  # tr output data
        self.tr_record = None

        self.gubun = None
        self.codes = None
        self.start = None
        self.end = None
        self.codes = None
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")  # PyQt5.QAxContainer 모듈

        # slot 설정
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_tr)
        self.ocx.OnReceiveMsg.connect(self._handler_msg)
        self.CommConnect()

        # 기존 sqlite3 db를 읽어서 table의 처음부터 끝까지 데이터를 조회하면서 업데이트
        db_name = "D:/db/market_jisu(1min).db"
        self.marketjisu_download(db_name, "kospi")
        self.marketjisu_download(db_name, "kosdaq")

    def marketjisu_download(self, db_name, gubun):
        today = datetime.datetime.now().strftime("%Y%m%d")
        time.sleep(3.6)
        count = 0
        b_code = None
        if gubun == 'kospi':
            b_code = '001'
        elif gubun == 'kosdaq':
            b_code = '101'

        self.lock.acquire()
        # 일봉다운로드
        # df = self.block_request('opt20006', 업종코드=b_code, 기준일자=today,
        #                         output='업종일봉조회', next=0)
        # 분봉다운로드
        df = self.block_request('opt20005', 업종코드=b_code, 틱범위=1,
                                output='업종분봉조회', next=0)
        self.lock.release()

        # column 숫자로 변환
        int_column = ['현재가', '시가', '고가', '저가', '거래량']
        df[int_column] = df[int_column].replace('', 0)
        df[int_column] = df[int_column].astype(int).abs()

        columns = ['체결시간', '현재가', '시가', '고가', '저가', '거래량']
        df = df[columns].copy()
        # df = df[::-1]
        # print('df', df)
        self.queryQ.put([df, db_name, gubun])

        while self.tr_remained == True:
            time.sleep(3.6)
            # time.sleep(0.2)
            count += 1
            self.lock.acquire()
            # df = self.block_request('opt20006', 업종코드=b_code, 기준일자=today,
            #                         output='업종일봉조회', next=2)
            df = self.block_request('opt20005', 업종코드=b_code, 틱범위=1,
                                    output='업종뷴봉조회', next=2)
            self.lock.release()

            # column 숫자로 변환
            int_column = ['현재가', '시가', '고가', '저가', '거래량']
            df[int_column] = df[int_column].replace('', 0)
            df[int_column] = df[int_column].astype(int).abs()

            columns = ['체결시간', '현재가', '시가', '고가', '저가', '거래량']
            df = df[columns].copy()
            self.queryQ.put([df, db_name, gubun])
            print(f"다운로드 중...{count}")

        self.queryQ.put('다운로드완료')

    # ------------------------
    # Kiwoom _handler [SLOT]
    # ------------------------
    def _handler_login(self, err_code):
        # print('handler_login')
        logging.info(f"hander login {err_code}")
        if err_code == 0:
            self.connected = True
        '''
        # 본서버 접속할때 계좌비밀번호 입력처리하는 코드.
        if self.num == '02' or self.num == '04':
            self.gubun = 1 if self.num == '02' else 2
            # print("여기 189까지 왔음.")
            QTimer.singleShot(5000, lambda: auto_on(self.gubun))  # 인자는 첫번째 계정 or 두번째계정 송부
            self.ocx.dynamicCall('KOA_Functions(QString, QString)', 'ShowAccountWindow', '')
            print(' 자동 로그인 설정 완료\n')
            print(' 자동 로그인 설정용 프로세스 종료 중 ...')
        '''
    def _handler_condition_load(self, ret, msg):
        if ret == 1:
            self.condition_loaded = True

    def _handler_tr(self, screen, rqname, trcode, record, next):
        logging.info(f"OnReceiveTrData {screen} {rqname} {trcode} {record} {next}")
        try:
            record = None
            items = None

            # remained data
            if next == '2':
                self.tr_remained = True
            else:
                self.tr_remained = False

            for output in self.tr_items['output']:
                record = list(output.keys())[0]
                items = list(output.values())[0]
                if record == self.tr_record:
                    break

            rows = self.GetRepeatCnt(trcode, rqname)
            if rows == 0:
                rows = 1

            data_list = []
            for row in range(rows):
                row_data = []
                for item in items:
                    data = self.GetCommData(trcode, rqname, row, item)
                    row_data.append(data)
                data_list.append(row_data)

            # data to DataFrame
            df = pd.DataFrame(data=data_list, columns=items)
            self.tr_data = df
            self.received = True
        except:
            pass

    def _handler_msg(self, screen, rqname, trcode, msg):
        logging.info(f"OnReceiveMsg {screen} {rqname} {trcode} {msg}")

    # end---------------------------------------------------------------

    def CommConnect(self, block=True):
        """
        로그인 윈도우를 실행합니다.
        :param block: True: 로그인완료까지 블록킹 됨, False: 블록킹 하지 않음
        :return: None
        """
        print('commconnect')
        self.ocx.dynamicCall("CommConnect()")
        if block:
            while not self.connected:
                pythoncom.PumpWaitingMessages()

    def CommRqData(self, rqname, trcode, next, screen):
        """
        TR을 서버로 송신합니다.
        :param rqname: 사용자가 임의로 지정할 수 있는 요청 이름
        :param trcode: 요청하는 TR의 코드
        :param next: 0: 처음 조회, 2: 연속 조회
        :param screen: 화면번호 ('0000' 또는 '0' 제외한 숫자값으로 200개로 한정된 값
        :return: None
        """
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen)

    def GetLoginInfo(self, tag):
        """
        로그인한 사용자 정보를 반환하는 메서드
        :param tag: ("ACCOUNT_CNT, "ACCNO", "USER_ID", "USER_NAME", "KEY_BSECGB", "FIREW_SECGB")
        :return: tag에 대한 데이터 값
        """
        data = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)

        if tag == "ACCNO":
            return data.split(';')[:-1]
        else:
            return data

    def SetInputValue(self, id, value):
        """
        TR 입력값을 설정하는 메서드
        :param id: TR INPUT의 아이템명
        :param value: 입력 값
        :return: None
        """
        self.ocx.dynamicCall("SetInputValue(QString, QString)", id, value)

    def GetRepeatCnt(self, trcode, rqname):
        """
        멀티데이터의 행(row)의 개수를 얻는 메서드
        :param trcode: TR코드
        :param rqname: 사용자가 설정한 요청이름
        :return: 멀티데이터의 행의 개수
        """
        count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return count

    def CommKwRqData(self, arr_code, next, code_count, type, rqname, screen):
        """
        여러 종목 (한 번에 100종목)에 대한 TR을 서버로 송신하는 메서드
        :param arr_code: 여러 종목코드 예: '000020:000040'
        :param next: 0: 처음조회
        :param code_count: 종목코드의 개수
        :param type: 0: 주식종목 3: 선물종목
        :param rqname: 사용자가 설정하는 요청이름
        :param screen: 화면번호
        :return:
        """
        ret = self.ocx.dynamicCall("CommKwRqData(QString, bool, int, int, QString, QString)", arr_code, next,
                                   code_count,
                                   type, rqname, screen);
        return ret

    def GetCodeListByMarket(self, market):
        """
        시장별 상장된 종목코드를 반환하는 메서드
        :param market: 0: 코스피, 3: ELW, 4: 뮤추얼펀드 5: 신주인수권 6: 리츠
                       8: ETF, 9: 하이일드펀드, 10: 코스닥, 30: K-OTC, 50: 코넥스(KONEX)
        :return: 종목코드 리스트 예: ["000020", "000040", ...]
        """
        data = self.ocx.dynamicCall("GetCodeListByMarket(QString)", market)
        tokens = data.split(';')[:-1]
        return tokens

    def GetMasterCodeName(self, code):
        """
        종목코드에 대한 종목명을 얻는 메서드
        :param code: 종목코드
        :return: 종목명
        """
        data = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return data

    def GetCommData(self, trcode, rqname, index, item):
        """
        수순 데이터를 가져가는 메서드
        :param trcode: TR 코드
        :param rqname: 요청 이름
        :param index: 멀티데이터의 경우 row index
        :param item: 얻어오려는 항목 이름
        :return:
        """
        data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, index, item)
        return data.strip()

    def block_request(self, *trcode, **kwargs):
        '''
        tr조회함수
        :param args: ex) 'opt10001'
        :param kwargs: 종목코드="005930", output="주식기본정보", next=0
        :return:
        '''
        trcode = trcode[0].lower()
        # lines = parser.read_enc(trcode)
        lines = self.ReadEnc(trcode)

        self.tr_items = self.ParseDat(trcode, lines)
        self.tr_record = kwargs["output"]
        next = kwargs["next"]

        # set input
        for id in kwargs:
            if id.lower() != "output" and id.lower() != "next":
                self.SetInputValue(id, kwargs[id])

        # initialize
        self.received = False
        self.tr_remained = False

        # request
        self.CommRqData(trcode, trcode, next, "0101")
        while not self.received:
            pythoncom.PumpWaitingMessages()

        return self.tr_data  # df output항목을 columns로 하는 데이터프레임을 반환(_handler_tr과 상호작용

    def ReadEnc(self, trcode):
        openapi_path = "C:/OpenAPI"
        enc = zipfile.ZipFile(f'{openapi_path}/data/{trcode}.enc')

        liness = enc.read(trcode.upper() + '.dat').decode('cp949')
        return liness

    def ParseDat(self, trcode, liness):
        liness = liness.split('\n')
        start = [i for i, x in enumerate(liness) if x.startswith('@START')]
        end = [i for i, x in enumerate(liness) if x.startswith('@END')]
        block = zip(start, end)
        enc_data = {'trcode': trcode, 'input': [], 'output': []}
        for start, end in block:
            block_data = liness[start - 1:end + 1]
            block_info = block_data[0]
            block_type = 'input' if 'INPUT' in block_info else 'output'
            record_line = block_data[1]
            tokens = record_line.split('_')[1].strip()
            record = tokens.split('=')[0]
            fields = block_data[2:-1]
            field_name = []
            for line in fields:
                field = line.split('=')[0].strip()
                field_name.append(field)
            fields = {record: field_name}
            enc_data['input'].append(fields) if block_type == 'input' else enc_data['output'].append(fields)
        return enc_data


class Query:
    def __init__(self, queryQQ, lock):
        self.queryQ = queryQQ
        self.lock = lock
        self.Start()

    def Start(self):
        while True:
            data = self.queryQ.get()  # data = [df, db_name, gubun]
            print('data', data)
            if data != '다운로드완료':
                self.save_sqlite3(data[0], data[1], data[2])
            else:
                print(f'한개 process 다운로드완료')

    def save_sqlite3(self, df, db_name, table_name):
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        # 일봉
        # query = "CREATE TABLE IF NOT EXISTS {} (일자 text PRIMARY KEY, \
        #             현재가 integer, 시가 integer, 고가 integer, 저가 integer, 거래량 integer, \
        #             거래대금 integer)".format(table_name)

        # 분봉
        query = "CREATE TABLE IF NOT EXISTS {} (체결시간 text PRIMARY KEY, \
                    현재가 integer, 시가 integer, 고가 integer, 저가 integer, 거래량 integer \
                    )".format(table_name)
        cur.execute(query)
        record_data_list = str(tuple(df.apply(lambda x: tuple(x.tolist()), axis=1)))[1:-1]
        if record_data_list[-1] == ',':
            record_data_list = record_data_list[:-1]
        sql_syntax = "INSERT OR IGNORE INTO %s VALUES %s" % (table_name, record_data_list)
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
    Process(target=Query, args=(queryQ, lock)).start()

    # DayDataDownload process-1 start
    # 자동로그인 파일삭제
    login_info = f'{openapi_path}/system/Autologin.dat'
    print('login_info', login_info)
    if os.path.isfile(login_info):
        os.remove(f'{openapi_path}/system/Autologin.dat')
    print('\n 자동 로그인 설정 파일 삭제 완료\n')

    Process(target=MarketJisuDownload, args=(queryQ, lock)).start()

    while find_window('Open API login') == 0:
        print(' 로그인창 열림 대기 중 ...\n')
        time.sleep(1)

    print(' 아이디 및 패스워드 입력 대기 중 ...\n')
    time.sleep(5)

    manual_login(1)
    print(' 아이디 및 패스워드 입력 완료\n')



