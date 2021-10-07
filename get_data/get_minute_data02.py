import os
import sys
from multiprocessing import Process, Lock
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
import logging
import pandas as pd
import pythoncom
import zipfile
import sqlite3
import datetime
import time

class GetMinuteData:
    def __init__(self, num, category, lock):
        super().__init__()
        app = QApplication(sys.argv)
        self.num = num
        self.category = category

        self.connected = False  # for login event
        self.received = False  # for tr event
        self.tr_items = None  # tr input/output items
        self.tr_data = None  # tr output data
        self.tr_record = None

        self.gubun = None
        self.codes = None
        # self.category = None
        self.start = None
        self.end = None
        self.codes = None

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")  # PyQt5.QAxContainer 모듈

        # slot 설정
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_tr)
        self.ocx.OnReceiveMsg.connect(self._handler_msg)

        self.CommConnect()

        # 일봉, 분봉, 틱 차트 데이터 수신
        self.kospi = self.GetCodeListByMarket('0')
        self.kosdaq = self.GetCodeListByMarket('10')

        if self.category == 'kosdaq':
            self.codes = self.kosdaq
        elif self.category == 'kospi':
            self.codes = self.kospi

        #  맨 처음이면 self.start = 0 아니면 직전 받은 code다음부터 수행
        db_name = f"E:\minute_chart{self.num}.db"
        if not os.path.isfile(db_name):
            self.start = 0
        else:
            con = sqlite3.connect(db_name)
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            last_table = str(cur.fetchall()[-1][0][1:])
            con.close()
            self.start = self.codes.index(last_table) + 1   # last_table 다음 code부터 수행

        # end_num 설정
        if self.num == '01':
            self.end = 400
        elif self.num == '02':
            self.end = 800
        elif self.num == '03':
            self.end = 1200
        elif self.num == '04':
            self.end = len(self.codes)

        print(f"시작번호: {self.start}, 끝번호: {self.end}")

        self.get_minute_data(self.codes[self.start: self.end], self.category)
        app.exec_()

    def get_minute_data(self, codes, category):
        # 전 종목의 분봉 데이터
        now = datetime.datetime.now()
        today = now.strftime("%Y%m%d")

        # sqlite3 db생성 및 준비
        tr_code = 'opt10080'
        rq_name = "주식분봉차트조회"

        # last_code = None
        for i, code in enumerate(codes):
            dfs = []
            count = 0
            df = self.block_request(tr_code,
                                    종목코드=code,
                                    # 기준일자=today,
                                    틱범위=1,
                                    수정주가구분=1,
                                    output=rq_name,
                                    next=0)
            dfs.append(df)
            while self.tr_remained == True:
                # sys.stdout.write(f'\r코드번호{code} 진행중: {i + 1}/{len(codes)} ---> 연속조회 {count + 1}/82')
                sys.stdout.write(f'\r코드번호{code} 진행중: {self.start + i}/{self.end} ---> 연속조회 {count + 1}/82')
                # time.sleep(0.2)
                time.sleep(3.6)
                count += 1
                df = self.block_request(tr_code,
                                        종목코드=code,
                                        # 기준일자=today,
                                        틱범위=1,
                                        수정주가구분=1,
                                        output=rq_name,
                                        next=2)
                dfs.append(df)
                if count == 20:
                    break
            df = pd.concat(dfs)
            print('df크기', len(df))
            df = df[['체결시간', '현재가', '시가', '고가', '저가', '거래량']]

            # sqlite3 db에 저장
            # sqlite table column '체결시간'을 primary key로 생성
            # fath = "D:/"
            fath = "E:/"
            filename = f'minute_chart{self.num}.db'
            db = fath + filename
            con = sqlite3.connect(db)
            cur = con.cursor()
            out_name = f"a{code}" if category == 'kospi' else f"b{code}"  # 여기서 b는 구분표시 즉, kospi ; a, kosdaq ; b, 숫자만으로 구성된 name을 피하기위한 수단이기도함.
            query = "CREATE TABLE IF NOT EXISTS {} (체결시간 text PRIMARY KEY, \
                        현재가 text, 시가 text, 고가 text, 저가 text, 거래량 text)".format(out_name)
            cur.execute(query)
            self.insert_bulk_record(con, db, out_name, df)
            con.close()

    def insert_bulk_record(self, con, db_name, table_name, record):
        record_data_list = str(tuple(record.apply(lambda x: tuple(x.tolist()), axis=1)))[1:-1]
        # record_data_list = str(tuple(record.apply(lambda x: tuple(x.tolist()), axis=1)))
        # print("record_data_list", record_data_list)
        if record_data_list[-1] == ',':
            record_data_list = record_data_list[:-1]
        # sql_syntax = "INSERT OR IGNORE INTO %s, %s VALUES %s" %(db_name, table_name, record_data_list)
        sql_syntax = "INSERT OR IGNORE INTO %s VALUES %s" %(table_name, record_data_list)
        cur = con.cursor()
        cur.execute(sql_syntax)
        con.commit()

    # ------------------------
    # Kiwoom _handler [SLOT]
    # ------------------------
    def _handler_login(self, err_code):
        # print('handler_login')
        logging.info(f"hander login {err_code}")
        if err_code == 0:
            self.connected = True

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
        ret = self.ocx.dynamicCall("CommKwRqData(QString, bool, int, int, QString, QString)", arr_code, next, code_count,
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

if __name__ == '__main__':
    # num = sys.argv[1]
    num = '02'
    # category = sys.argv[2]
    category = 'kosdaq'
    lock = Lock()
    # app = QApplication(sys.argv)
    # p = Process(target=GetMinuteData, args=(num, category, lock), daemon=True)
    # p.start()
    # p.join()
    getdata = GetMinuteData(num, category, lock)
    # app.exec_()
