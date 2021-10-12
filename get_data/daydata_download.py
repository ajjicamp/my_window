import os
import sys
import time
import sqlite3
import zipfile
import pythoncom
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QAxContainer import QAxWidget
from multiprocessing import Process, Queue, Lock
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from login.manuallogin import find_window, manual_login
from utility.static import strf_time, now
from utility.setting import openapi_path, sn_brrq, sn_oper, db_day, db_minute
app = QtWidgets.QApplication(sys.argv)


class DaydataDowwnload:
    def __init__(self, gubun, queryQQ, lockk):
        self.gubun = gubun
        self.queryQ = queryQQ
        self.lock = lockk
        self.str_trname = None
        self.str_tday = strf_time('%Y%m%d')
        self.df_tr = None
        self.list_trcd = []
        self.dict_tritems = None
        self.dict_cond = {}
        self.dict_bool = {
            '로그인': False,
            'TR수신': False,
            'TR다음': False,
            'CD수신': False,
            'CR수신': False
        }

        self.ocx = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')
        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.ocx.OnReceiveTrCondition.connect(self.OnReceiveTrCondition)
        self.ocx.OnReceiveConditionVer.connect(self.OnReceiveConditionVer)
        self.Start()

    def Start(self):
        self.CommConnect()
        # self.DownloadDay()
        self.DownloadMinute()

    def CommConnect(self):
        self.ocx.dynamicCall('CommConnect()')
        while not self.dict_bool['로그인']:
            pythoncom.PumpWaitingMessages()

        '''
        # 조건검색식 수신하여 codelist 설정 ---> 나는 코스피, 코스닥 전체코드로 작성
        self.dict_bool['CD수신'] = False
        self.ocx.dynamicCall('GetConditionLoad()')
        while not self.dict_bool['CD수신']:
            pythoncom.PumpWaitingMessages()

        data = self.ocx.dynamicCall('GetConditionNameList()')
        conditions = data.split(';')[:-1]
        for condition in conditions:
            cond_index, cond_name = condition.split('^')
            self.dict_cond[int(cond_index)] = cond_name
        '''

    # def DownloadDay(self):
    def DownloadMinute(self):

        self.lock.acquire()  # todo lock은 왜 필요한가?
        # 나는 여기서 전체코드 수신
        # codes = self.SendCondition(sn_oper, self.dict_cond[2], 2, 0)
        codes = self.GetCodeListByMarket('10')[:8]
        self.lock.release()

        print('codes:', codes)
        codes = [code for i, code in enumerate(codes) if i % 4 == self.gubun]  # 4로 나눈값이 process 번호이면 즉, 4번째 마다 저장
        count = len(codes)
        for i, code in enumerate(codes):
            time.sleep(3.6)
            df = []
            self.lock.acquire()  # todo lock이 왜 필요?
            # df2 = self.Block_Request('opt10081', 종목코드=code, 기준일자=self.str_tday, 수정주가구분=1,
            #                          output='주식일봉차트조회', next=0)
            df2 = self.Block_Request('opt10080', 종목코드=code, 틱범위= 1, 수정주가구분=1,
                                     output='주식분봉차트조회', next=0)
            self.lock.release()

            # df2 = df2.set_index('일자')
            df2 = df2.set_index('체결시간')
            df.append(df2)

            tr_next_count = 0
            while self.dict_bool['TR다음']:
                time.sleep(3.6)
                tr_next_count += 1
                self.lock.acquire()
                # df2 = self.Block_Request('opt10081', 종목코드=code, 기준일자=self.str_tday, 수정주가구분=1,
                #                          output='주식일봉차트조회', next=2)
                df2 = self.Block_Request('opt10080', 종목코드=code, 틱범위=1, 수정주가구분=1,
                                         output='주식분봉차트조회', next=2)
                self.lock.release()
                df2 = df2.set_index('체결시간')
                df.append(df2)
                print(f'[{now()}] {self.gubun} 데이터 다운로드 중 ... [{i + 1}/{count}] [tr_next_count: {tr_next_count}]')
                if tr_next_count == 5:
                    break

            df = pd.concat(df)
            # columns = ['현재가', '시가', '고가', '저가', '거래량', '거래대금']
            columns = ['현재가', '시가', '고가', '저가', '거래량']
            df[columns] = df[columns].astype(int).abs()
            df = df[columns].copy()
            df = df[::-1]
            self.queryQ.put([df, code])
            print(f'[{now()}] {self.gubun} 데이터 다운로드 중 ... [{i + 1}/{count}]')
        if self.gubun == 3: # 위의 for문을 마친 후에 self.gubun == 3: 다운로드 완료하고 하면, 0, 1, 2 ,3이 차례로 되는 건가?
            self.queryQ.put('다운로드완료')

    def OnEventConnect(self, err_code):
        if err_code == 0:
            self.dict_bool['로그인'] = True

    def OnReceiveConditionVer(self, ret, msg):
        if msg == '':
            return
        if ret == 1:
            self.dict_bool['CD수신'] = True

    def OnReceiveTrCondition(self, screen, code_list, cond_name, cond_index, nnext):
        if screen == "" and cond_name == "" and cond_index == "" and nnext == "":
            return
        codes = code_list.split(';')[:-1]
        self.list_trcd = codes
        self.dict_bool['CR수신'] = True

    def OnReceiveTrData(self, screen, rqname, trcode, record, nnext):
        if screen == '' and record == '':
            return
        items = None
        self.dict_bool['TR다음'] = True if nnext == '2' else False
        for output in self.dict_tritems['output']:
            record = list(output.keys())[0]
            items = list(output.values())[0]
            if record == self.str_trname:
                break
        rows = self.ocx.dynamicCall('GetRepeatCnt(QString, QString)', trcode, rqname)
        if rows == 0:
            rows = 1
        df2 = []
        for row in range(rows):
            row_data = []
            for item in items:
                data = self.ocx.dynamicCall('GetCommData(QString, QString, int, QString)', trcode, rqname, row, item)
                row_data.append(data.strip())
            df2.append(row_data)
        df = pd.DataFrame(data=df2, columns=items)
        self.df_tr = df
        self.dict_bool['TR수신'] = True

    def SendCondition(self, screen, cond_name, cond_index, search):
        self.dict_bool['CR수신'] = False
        self.ocx.dynamicCall('SendCondition(QString, QString, int, int)', screen, cond_name, cond_index, search)
        while not self.dict_bool['CR수신']:
            pythoncom.PumpWaitingMessages()
        return self.list_trcd

    def Block_Request(self, *args, **kwargs):
        trcode = args[0].lower()
        liness = self.ReadEnc(trcode)
        self.dict_tritems = self.ParseDat(trcode, liness)
        self.str_trname = kwargs['output']
        nnext = kwargs['next']
        for i in kwargs:
            if i.lower() != 'output' and i.lower() != 'next':
                self.ocx.dynamicCall('SetInputValue(QString, QString)', i, kwargs[i])
        self.dict_bool['TR수신'] = False
        self.dict_bool['TR다음'] = False
        self.ocx.dynamicCall('CommRqData(QString, QString, int, QString)', self.str_trname, trcode, nnext, sn_brrq)
        while not self.dict_bool['TR수신']:
            pythoncom.PumpWaitingMessages()
        return self.df_tr

    # noinspection PyMethodMayBeStatic
    def ReadEnc(self, trcode):
        enc = zipfile.ZipFile(f'{openapi_path}/data/{trcode}.enc')
        liness = enc.read(trcode.upper() + '.dat').decode('cp949')
        return liness

    # noinspection PyMethodMayBeStatic
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


class Query:
    def __init__(self, queryQQ):
        self.queryQ = queryQQ
        # self.con = sqlite3.connect(db_day)
        self.con = sqlite3.connect(db_minute)
        self.Start()

    def __del__(self):
        self.con.close()

    def Start(self):
        while True:
            data = self.queryQ.get()    # data = [df, code]
            if data != '다운로드완료':
                data[0].to_sql(data[1], self.con, if_exists='replace', chunksize=1000)
            else:
                print('download 완료')
                break


if __name__ == '__main__':
    queryQ = Queue()
    lock = Lock()

    # 자동로그인 준비; dat 삭제
    login_info = f'{openapi_path}/system/Autologin.dat'
    if os.path.isfile(login_info):
        os.remove(f'{openapi_path}/system/Autologin.dat')

    # Query process start
    Process(target=Query, args=(queryQ,)).start()

    # DayDataDownload process start
    Process(target=DaydataDowwnload, args=(0, queryQ, lock)).start()

    while find_window('Open API login') == 0:
        print("open api login 발견")
        time.sleep(1)
    time.sleep(5)
    manual_login(1)
    # 아래 로직 작동안함.
    while find_window('Open API login') != 0:
        print("open api login 미발견")
        time.sleep(1)
    '''
    Process(target=DaydataDowwnload, args=(1, queryQ, lock)).start()
    while find_window('Open API login') == 0:
        time.sleep(1)
    time.sleep(5)
    manual_login(2)
    while find_window('Open API login') != 0:
        time.sleep(1)
    '''
    Process(target=DaydataDowwnload, args=(2, queryQ, lock)).start()
    while find_window('Open API login') == 0:
        time.sleep(1)
    time.sleep(5)
    manual_login(3)
    while find_window('Open API login') != 0:
        time.sleep(1)
    '''
    Process(target=DaydataDowwnload, args=(3, queryQ, lock)).start()
    while find_window('Open API login') == 0:
        time.sleep(1)
    time.sleep(5)
    manual_login(4)
    while find_window('Open API login') != 0:
        time.sleep(1)
    '''