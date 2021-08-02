import sys
import logging
import sqlite3
import telegram
import requests
import pythoncom
import pandas as pd
# from Utility import *
from threading import Timer
from bs4 import BeautifulSoup
from PyQt5.QAxContainer import QAxWidget
# app = QtWidgets.QApplication(sys.argv)


class Worker:
    def __init__(self, windowQ, workerQ, chartQ, hogaQ, queryQ, soundQ, downQ):
        self.log = logging
        self.log.basicConfig(filename=f"{system_path}/Log/{strymdtime()}_.txt", level=logging.INFO)

        self.windowQ = windowQ
        self.workerQ = workerQ
        self.chartQ = chartQ
        self.hogaQ = hogaQ
        self.queryQ = queryQ
        self.soundQ = soundQ
        self.downQ = downQ

        self.db_day = f"{system_path}/DB/day.db"
        self.db_etc = f"{system_path}/DB/etc.db"
        self.db_bac = f"{system_path}/Backup/"

        self.df_hm = pd.DataFrame(columns=['HML', 'SELL', 'BUY1', 'BUY2', 'BUY3', 'BUY4', 'BUY5', 'BUY6', 'BUY7'])
        self.df_od = pd.DataFrame(columns=['전략구분', '매수횟수'])
        self.df_gs = pd.DataFrame(
            columns=['종목명', 'HMP', '현재가', '등락율', '거래대금', '증감비율', '체결강도',
                     '종목코드', '시가', '고가', '저가', '전일종가', 'HML'])
        self.df_tj = pd.DataFrame(
            columns=['추정예탁자산', '추정예수금', '수익률평균', '총수익률', '총평가손익', '총매입금액', '총평가금액'])
        self.df_jg = pd.DataFrame(
            columns=['종목명', '매입가', '현재가', '수익률', '평가손익', '매입금액', '평가금액',
                     '종목코드', '시가', '고가', '저가', '전일종가', '보유수량', '최고수익률', '최저수익률'])
        self.df_cj = pd.DataFrame(
            columns=['종목명', '주문구분', '주문수량', '미체결수량', '주문가격', '체결가', '체결시간',
                     '종목코드'])
        self.df_tt = pd.DataFrame(
            columns=['거래횟수', '총매수금액', '총매도금액', '총수익금액', '총손실금액', '수익률', '수익금합계'])
        self.df_td = pd.DataFrame(
            columns=['종목명', '매수가', '매도가', '주문수량', '수익률', '수익금', '체결시간',
                     '종목코드', '매수금액', '매도금액', '전략구분'])

        self.chart_code = ['', '', '', '', '', '']
        self.hoga_code = ['', '']

        self.df_hj_left = None
        self.df_hj_right = None

        self.df_cdb = None
        self.df_bdb = None
        self.df_cbc = None
        self.df_dbc = None
        self.df_bbc = None

        self.list_kosd = None
        self.list_bb05 = None
        self.list_bb00 = None
        self.list_cad = None
        self.list_buy = []
        self.list_sell = []

        self.int_cbat = None
        self.int_dbat = None
        self.int_bbat = None

        self.int_bcbp = None
        self.int_mcbp = None
        self.int_cdsp = None
        self.int_hmlp = None
        self.int_hper = None
        self.int_sbgm = None
        self.int_sper = None
        self.int_cslp = None
        self.int_cpsp = None
        self.int_dper = None

        self.int_bdbp = None
        self.int_cbsp = None

        self.int_bbbp = None
        self.int_bdsp = None

        self.int_gjut = None
        self.int_rcut = None
        self.int_siut = None
        self.int_trot = None
        self.int_trct = None
        self.int_medt = None
        self.int_sedt = None
        self.int_elst = None
        self.int_hjof = 600
        self.int_shut = 60

        self.str_bot = None
        self.int_id = None

        self.int_btax = None
        self.int_stax = None
        self.int_fees = None

        self.bool_test = False
        self.bool_jstd = False
        self.bool_cas = False
        self.bool_cad = False
        self.bool_bnf = False
        self.bool_down = False
        self.bool_sound = False
        self.bool_chup = False
        self.bool_hgup = False
        self.bool_atbj = False
        self.bool_info = False
        self.bool_kpcs = False
        self.bool_kdcs = False

        now = datetime.datetime.now()
        self.time_exit = now + datetime.timedelta(seconds=+self.int_hjof)
        self.time_updf = now
        self.time_info = now
        self.time_tran = now
        self.time_tmjj = now

        self.start_tr = now
        self.count_tr = 0

        self.ThemaJudoju = []
        self.str_tday = strymdtime()
        self.str_acct = None
        self.float_cpuper = 0.00
        self.float_memory = 0.00
        self.int_threads = 0
        self.int_oper = 1
        self.int_ysgm = 0
        self.int_cttr = 0
        self.int_ctcr = 0
        self.int_ctjc = 0
        self.int_ctcj = 0
        self.int_cthj = 0
        self.int_ctsc = 0
        self.int_ctrjc = 0
        self.int_ctrhj = 0

        self.int_screen_gs = 0
        self.screen_gsjc = 1100

        self.bool_conn = False
        self.bool_trcdload = False
        self.bool_cdload = False
        self.bool_received = False
        self.bool_trremained = False
        self.df_trdata = None
        self.list_trcddata = None
        self.list_tritems = None
        self.list_trrecord = None

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._h_login)
        self.ocx.OnReceiveTrData.connect(self._h_tran_data)
        self.ocx.OnReceiveRealData.connect(self._h_real_data)
        self.ocx.OnReceiveChejanData.connect(self._h_cjan_data)
        self.ocx.OnReceiveTrCondition.connect(self._h_cond_data)
        self.ocx.OnReceiveConditionVer.connect(self._h_cond_load)
        self.ocx.OnReceiveRealCondition.connect(self._h_real_cond)
        self.Start()

    def Start(self):
        self.CreateDatabase()
        self.LoadSettings()
        self.LoadDatabase()
        self.CommConnect()
        self.GetCondition()
        self.EventLoop()

    def CreateDatabase(self):
        con = sqlite3.connect(self.db_etc)
        df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        con.close()
        if "casbuycount" not in df['name'].values:  # df[column].values는 array이다. values가 없으면 series라서 조건이 불성립.
            self.queryQ.put("CREATE TABLE casbuycount ('종목코드' TEXT, '종목명' TEXT, '매수횟수' INTEGER,"
                            "'체결시간' TEXT, 'SELL' INTEGER, 'BUY1' INTEGER, 'BUY2' INTEGER, 'BUY3' INTEGER,"
                            "'BUY4' INTEGER, 'BUY5' INTEGER, 'BUY6' INTEGER, 'BUY7' INTEGER)")
            self.queryQ.put("CREATE INDEX 'ix_casbuycount_종목코드' ON 'casbuycount' ('종목코드')")
        if "cadbuycount" not in df['name'].values:
            self.queryQ.put("CREATE TABLE cadbuycount ('종목코드' TEXT, '종목명' TEXT, '매수횟수' INTEGER,"
                            "'체결시간' TEXT)")
            self.queryQ.put("CREATE INDEX 'ix_cadbuycount_종목코드' ON 'cadbuycount' ('종목코드')")
        if "bnfbuycount" not in df['name'].values:
            self.queryQ.put("CREATE TABLE bnfbuycount ('종목코드' TEXT, '종목명' TEXT, '매수횟수' INTEGER,"
                            "'체결시간' TEXT)")
            self.queryQ.put("CREATE INDEX 'ix_bnfbuycount_종목코드' ON 'bnfbuycount' ('종목코드')")
        if "chegeollist" not in df['name'].values:
            self.queryQ.put("CREATE TABLE chegeollist ('주문번호' TEXT, '종목명' TEXT, '주문구분' TEXT,"
                            "'주문수량' INTEGER, '미체결수량' INTEGER, '주문가격' INTEGER, '체결가' INTEGER,"
                            "'체결시간' INTEGER, '종목코드' TEXT)")
            self.queryQ.put("CREATE INDEX 'ix_chegeollist_주문번호' ON 'chegeollist' ('주문번호')")
        if "tradelist" not in df['name'].values:
            self.queryQ.put("CREATE TABLE tradelist ('주문번호' TEXT, '종목명' TEXT, '매수가' INTEGER,"
                            "'매도가' INTEGER, '주문수량' INTEGER, '수익률' REAL, '수익금' INTEGER, '체결시간' INTEGER,"
                            "'종목코드' TEXT, '매수금액' INTEGER, '매도금액' INTEGER, '전략구분' TEXT)")
            self.queryQ.put("CREATE INDEX 'ix_tradelist_주문번호' ON 'tradelist' ('주문번호')")
        if "totaltradelist" not in df['name'].values:
            self.queryQ.put("CREATE TABLE 'totaltradelist' ('일자' TEXT, '총매수금액' INTEGER, '총매도금액' INTEGER,"
                            "'총수익금액' INTEGER, '총손실금액' INTEGER, '수익률' REAL, '수익금합계' INTEGER)")
            self.queryQ.put("CREATE INDEX 'ix_totaltradelist_일자' ON 'totaltradelist' ('일자')")
        if "bnfbacktest" not in df['name'].values:
            self.queryQ.put("CREATE TABLE 'bnfbacktest' ('종목코드' TEXT, '거래횟수' INTEGER, '익절' INTEGER,"
                            "'손절' INTEGER, '승률' REAL, '보유기간' INTEGER, '수익률' REAL, '수익금' INTEGER)")
            self.queryQ.put("CREATE INDEX 'ix_bnfbacktest_종목코드' ON 'bnfbacktest' ('종목코드')")
        if "setting" not in df['name'].values:
            df2 = pd.DataFrame({
                '구분': ['bool_test', 'bool_jstd', 'bool_cas', 'bool_cad', 'bool_bnf', 'bool_atbj',
                       'bool_chup', 'bool_hgup', 'bool_sound', 'bool_info', 'bool_down',
                       'int_btax', 'int_stax', 'int_fees',
                       'int_bcbp', 'int_mcbp', 'int_cdsp', 'int_hmlp', 'int_hper',
                       'int_sbgm', 'int_sper', 'int_cslp', 'int_cpsp', 'int_dper',
                       'int_bdbp', 'int_cbsp', 'int_bbbp', 'int_bdsp',
                       'int_gjut', 'int_rcut', 'int_siut', 'int_trot', 'int_trct',
                       'int_medt', 'int_sedt', 'int_elst', 'int_hjof', 'int_shut'],
                '설정': [0, 1, 1, 1, 1, 1,
                       1, 1, 1, 1, 1,
                       15, 15, 25,
                       15, 10, 4, 50, 10,
                       100, -1.0, -2.5, -2.0, 2.5,
                       4, -2.0, 100, 2,
                       1, 1, 1, 3.6, 50,
                       0.25, 0.25, 0.000001, 600, 60]})
            df2 = df2.set_index('구분')
            self.queryQ.put([df2, "setting", "replace"])
        if "telegram" not in df['name'].values:
            df2 = pd.DataFrame({'str_bot': [" "], 'int_id': [0]}, index=[0])
            self.queryQ.put([df2, "telegram", "replace"])

    def LoadSettings(self):
        time.sleep(1)
        con = sqlite3.connect(self.db_etc)
        df = pd.read_sql("SELECT * FROM telegram", con)
        self.str_bot = df['str_bot'][0]
        self.windowQ.put([4, f"텔레그램봇넘버 {self.str_bot}"])
        self.int_id = int(df['int_id'][0])
        self.windowQ.put([4, f"사용자아이디 {self.int_id}"])
        df = pd.read_sql("SELECT * FROM setting", con)
        df = df.set_index('구분')
        con.close()
        self.bool_test = int(df['설정']['bool_test'])
        self.windowQ.put([4, f"테스트모드 {self.bool_test}"])
        self.bool_jstd = int(df['설정']['bool_jstd'])
        self.windowQ.put([4, f"지수트렌드 {self.bool_jstd}"])
        self.bool_cas = int(df['설정']['bool_cas'])
        self.windowQ.put([4, f"전략CAS {self.bool_cas}"])
        self.bool_bnf = int(df['설정']['bool_bnf'])
        self.windowQ.put([4, f"전략BNF {self.bool_bnf}"])
        self.bool_cad = int(df['설정']['bool_cad'])
        self.windowQ.put([4, f"전략CAD {self.bool_cad}"])
        self.bool_atbj = int(df['설정']['bool_atbj'])
        self.windowQ.put([4, f"자동비중조절 {self.bool_atbj}"])
        self.bool_chup = int(df['설정']['bool_chup'])
        self.chartQ.put(f"차트ONOFF {self.bool_chup}")
        self.windowQ.put([4, f"차트 {self.bool_chup}"])
        self.bool_hgup = int(df['설정']['bool_hgup'])
        self.hogaQ.put(f"호가ONOFF {self.bool_hgup}")
        self.windowQ.put([4, f"호가창 {self.bool_hgup}"])
        self.bool_sound = int(df['설정']['bool_sound'])
        self.windowQ.put([4, f"알림소리 {self.bool_sound}"])
        self.bool_info = int(df['설정']['bool_info'])
        self.chartQ.put(f"부가정보ONOFF {self.bool_info}")
        self.hogaQ.put(f"부가정보ONOFF {self.bool_info}")
        self.windowQ.put([4, f"부가정보 {self.bool_info}"])
        self.bool_down = int(df['설정']['bool_down'])
        self.windowQ.put([4, f"다운로드 {self.bool_down}"])
        self.int_btax = int(df['설정']['int_btax'])
        self.windowQ.put([4, f"매수수수료 {self.int_btax}"])
        self.int_stax = int(df['설정']['int_stax'])
        self.windowQ.put([4, f"매도수수료 {self.int_stax}"])
        self.int_fees = int(df['설정']['int_fees'])
        self.windowQ.put([4, f"제세공과금 {self.int_fees}"])
        self.int_bcbp = int(df['설정']['int_bcbp'])
        self.windowQ.put([4, f"전략CAS 기본매수비율 {self.int_bcbp}"])
        self.int_mcbp = int(df['설정']['int_mcbp'])
        self.windowQ.put([4, f"전략CAS 최대매수비율 {self.int_mcbp}"])
        self.int_cdsp = int(df['설정']['int_cdsp'])
        self.windowQ.put([4, f"전략CAS 분할매도비율 {self.int_cdsp}"])
        self.int_hmlp = int(df['설정']['int_hmlp'])
        self.windowQ.put([4, f"전략CAS 최고거래대금비율 {self.int_hmlp}"])
        self.int_hper = int(df['설정']['int_hper'])
        self.windowQ.put([4, f"전략CAS 매수제한등락율 {self.int_hper}"])
        self.int_sbgm = int(df['설정']['int_sbgm'])
        self.windowQ.put([4, f"전략CAS 전량청산보유금액 {self.int_sbgm}"])
        self.int_sper = float(df['설정']['int_sper'])
        self.chartQ.put(f"전략CAS 청산라인등락율 {self.int_sper}")
        self.windowQ.put([4, f"전략CAS 청산라인등락율 {self.int_sper}"])
        self.int_cslp = float(df['설정']['int_cslp'])
        self.windowQ.put([4, f"전략CAS 본전청산최저수익률 {self.int_cslp}"])
        self.int_cpsp = float(df['설정']['int_cpsp'])
        self.windowQ.put([4, f"전략CAS 추가매수등락율 {self.int_cpsp}"])
        self.int_dper = float(df['설정']['int_dper'])
        self.windowQ.put([4, f"전략CAS 분할매도최소등락율 {self.int_dper}"])
        self.int_bdbp = int(df['설정']['int_bdbp'])
        self.windowQ.put([4, f"전략CAD 기본매수비율 {self.int_bdbp}"])
        self.int_cbsp = float(df['설정']['int_cbsp'])
        self.windowQ.put([4, f"전략CAD 청산라인등락율 {self.int_cbsp}"])
        self.int_bbbp = int(df['설정']['int_bbbp'])
        self.windowQ.put([4, f"전략BNF 기본매수비율 {self.int_bbbp}"])
        self.int_bdsp = int(df['설정']['int_bdsp'])
        self.windowQ.put([4, f"전략BNF 분할매도비율 {self.int_bdsp}"])
        self.int_gjut = int(df['설정']['int_gjut'])
        self.windowQ.put([4, f"관심종목잔고 갱신시간 {self.int_gjut}"])
        self.int_rcut = int(df['설정']['int_rcut'])
        self.chartQ.put(f"실시간차트 갱신시간 {self.int_rcut}")
        self.windowQ.put([4, f"실시간차트 갱신시간 {self.int_rcut}"])
        self.int_siut = int(df['설정']['int_siut'])
        self.hogaQ.put(f"부가정보 갱신시간 {self.int_siut}")
        self.chartQ.put(f"부가정보 갱신시간 {self.int_siut}")
        self.windowQ.put([4, f"부가정보 갱신시간 {self.int_siut}"])
        self.int_trot = float(df['설정']['int_trot'])
        self.windowQ.put([4, f"TR조회제한 1회당시간 {self.int_trot}"])
        self.int_trct = int(df['설정']['int_trct'])
        self.windowQ.put([4, f"TR조회제한 계산시점 {self.int_trct}"])
        self.int_medt = float(df['설정']['int_medt'])
        self.windowQ.put([4, f"메인이벤트루프 대기시간 {self.int_medt}"])
        self.int_sedt = float(df['설정']['int_sedt'])
        self.windowQ.put([4, f"조회이벤트루프 대기시간 {self.int_sedt}"])
        self.int_elst = float(df['설정']['int_elst'])
        self.windowQ.put(f"이벤트루프 슬립시간 {self.int_elst}")
        self.soundQ.put(f"이벤트루프 슬립시간 {self.int_elst}")
        self.queryQ.put(f"이벤트루프 슬립시간 {self.int_elst}")
        self.hogaQ.put(f"이벤트루프 슬립시간 {self.int_elst}")
        self.chartQ.put(f"이벤트루프 슬립시간 {self.int_elst}")
        self.windowQ.put([4, f"이벤트루프 슬립시간 {self.int_elst}"])
        self.int_hjof = int(df['설정']['int_hjof'])
        self.windowQ.put([4, f"휴장유무 확인시간 {self.int_hjof}"])
        self.int_shut = int(df['설정']['int_shut'])
        self.windowQ.put([4, f"컴퓨터종료 대기시간 {self.int_shut}"])
        self.windowQ.put([1, "모든 설정값 불러오기 완료"])

    def LoadDatabase(self):
        con = sqlite3.connect(self.db_etc)
        df = pd.read_sql(f"SELECT 체결시간 FROM chegeollist ORDER BY 체결시간 DESC LIMIT 1", con)
        if len(df) > 0:
            dblastday = str(df['체결시간'][0])[:8]
        else:
            dblastday = strymdtime()
        self.df_cbc = pd.read_sql("SELECT * FROM casbuycount", con)
        self.df_cbc = self.df_cbc.set_index('종목코드')
        self.df_dbc = pd.read_sql("SELECT * FROM cadbuycount", con)
        self.df_dbc = self.df_dbc.set_index('종목코드')
        self.df_bbc = pd.read_sql("SELECT * FROM bnfbuycount", con)
        self.df_bbc = self.df_bbc.set_index('종목코드')
        self.df_bdb = pd.read_sql("SELECT 종목코드, 수익률 FROM bnfbacktest", con)
        self.df_bdb = self.df_bdb.set_index('종목코드')
        self.df_cj = pd.read_sql(f"SELECT * FROM chegeollist WHERE 체결시간 LIKE '{dblastday}%'", con)
        self.df_cj = self.df_cj.set_index('주문번호')
        self.df_cj.sort_values(by=['체결시간'], ascending=False, inplace=True)
        self.df_td = pd.read_sql(f"SELECT * FROM tradelist WHERE 체결시간 LIKE '{dblastday}%'", con)
        self.df_td = self.df_td.set_index('주문번호')
        self.df_td.sort_values(by=['체결시간'], ascending=False, inplace=True)
        con.close()
        self.windowQ.put(self.df_cj)
        self.windowQ.put(self.df_td)
        if len(self.df_cj) > 0:
            for name in self.df_cj['종목명']:
                if name not in self.list_buy:
                    self.list_buy.append(name)
        if len(self.df_td) > 0:
            for name in self.df_td['종목명']:
                if name not in self.list_sell:
                    self.list_sell.append(name)
            self.UpdateTotaltradelist()
        self.windowQ.put([1, "데이터베이스 정보 불러오기 완료"])

    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")
        while not self.bool_conn:
            pythoncom.PumpWaitingMessages()
            time.sleep(self.int_elst)
        self.windowQ.put([1, "OpenAPI 로그인 완료"])
        self.str_acct = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO").split(';')[0]
        self.windowQ.put([1, "계좌번호 불러오기 완료"])
        self.list_kosd = self.GetCodeListByMarket("10")
        if self.bool_sound:
            self.soundQ.put("키움증권 오픈에이피아이에 로그인하였습니다.")

    def GetCondition(self):
        self.bool_cdload = False
        self.ocx.dynamicCall("GetConditionLoad()")
        while not self.bool_cdload:
            pythoncom.PumpWaitingMessages()
            time.sleep(self.int_elst)
        data = self.ocx.dynamicCall("GetConditionNameList()")
        conditions = data.split(";")[:-1]
        df = []
        for condition in conditions:
            cond_index, cond_name = condition.split('^')
            df.append(pd.DataFrame({'조건명': [cond_name]}, index=[cond_index]))
        self.df_cdb = pd.concat(df)
        self.windowQ.put([1, "조건검색식 불러오기 완료"])
        self.windowQ.put([4, "시스템 준비 완료"])

    def EventLoop(self):
        jjo, cdr, rds, cad, bnf = False, False, False, False, False
        while True:
            if not self.workerQ.empty():
                work = self.workerQ.get()
                if type(work) == list:
                    if len(work) == 11:
                        self.SendOrder(work)
                    else:
                        self.UpdateRealreg(work)
                elif type(work) == str:
                    self.RunWork(work)
            if self.int_oper == 1 and not jjo and self.TrtimeCondition:
                self.GetAccountjanGo()
                self.GetKpcKdcChart()
                self.OperationRealreg()
                jjo = True
                if self.int_oper == 1 and 90030 < inttime():
                    self.int_oper = 3
            if self.int_oper == 3 and not cdr and self.TrtimeCondition:
                self.ConditionRealreg()
                cdr = True
            if self.int_oper == 3 and self.TrtimeCondition:
                self.UpdateHML(Check=False)
            if self.int_oper == 3 and datetime.datetime.now() > self.time_tmjj and self.bool_jstd:
                self.GetThemaJudoju()
                self.time_tmjj = datetime.datetime.now() + datetime.timedelta(seconds=+10)
            if self.int_oper == 2 and not rds and self.TrtimeCondition:
                self.RemoveALlRealreg()
                self.DeleteBuycount()
                self.SaveTotaltradelist()
                rds = True
            if self.int_oper == 2 and 152500 < inttime() and not cad and self.TrtimeCondition and self.bool_cad:
                self.GetCadbuycodes()
                self.BuyCad()
                cad = True
            if self.int_oper == 2 and 152500 < inttime() and not bnf and self.TrtimeCondition and self.bool_bnf:
                self.GetBnfbuycodes()
                self.BuyBnf()
                bnf = True
            if self.int_oper == 8 and downloadday() and self.bool_down:
                self.DownloadData()
                os.system(f"shutdown /s /t {self.int_shut}")
                self.SysExit()
            if self.int_oper == 8:
                os.system(f"shutdown /s /t {self.int_shut}")
                self.SysExit()
            if self.int_oper == 1 and datetime.datetime.now() > self.time_exit:
                os.system(f"shutdown /s /t {self.int_shut}")
                self.SysExit()
            if datetime.datetime.now() > self.time_info and self.bool_info:
                self.UpdateInfo()
                self.time_info = datetime.datetime.now() + datetime.timedelta(seconds=+self.int_siut)
            time_loop = datetime.datetime.now() + datetime.timedelta(seconds=+self.int_medt)
            while datetime.datetime.now() < time_loop:
                pythoncom.PumpWaitingMessages()
                time.sleep(self.int_elst)

    def SendOrder(self, order):
        gubun = order[-1]
        del order[-1]
        name = order[-1]
        del order[-1]
        code = order[4]
        if gubun == "CAS" and order[0] == "매수" and code not in self.df_gs.index and code not in self.df_jg.index:
            self.windowQ.put([2, f"CAS 매수 조건 확인 FALSE [조건이탈] {name}"])
            if code in self.df_od.index:
                self.df_od.drop(index=code, inplace=True)
            return
        elif gubun == "수동" and order[2] == "":
            order[2] = self.str_acct
            if code not in self.df_od.index:
                if code in self.df_cbc.index:
                    bc = self.df_cbc['매수횟수'][code]
                    df = pd.DataFrame({'전략구분': ["수동"], '매수횟수': [bc]}, index=[code])
                else:
                    df = pd.DataFrame({'전략구분': ["수동"], '매수횟수': [0]}, index=[code])
                self.df_od = self.df_od.append(df)
            else:
                self.windowQ.put([2, "주문실패 : 현재 주문중인 종목입니다."])
                return
        ret = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", order)
        if ret == 0:
            self.windowQ.put([2, f"{name} {order[5]}주 {order[0]} 주문 전송"])
        else:
            self.windowQ.put([2, f"{name} {order[5]}주 {order[0]} 주문 실패"])

    def UpdateRealreg(self, rreg):
        if len(rreg) == 4:
            if rreg[2] == "10;12;14;30;228":
                codes = rreg[1].split(";")
                for i, code in enumerate(codes):
                    if code not in self.df_gs.index and code not in self.df_jg.index:
                        del codes[i]
                rreg[1] = ";".join(codes)
            if rreg[1] == "":
                return
            ret = self.ocx.dynamicCall(
                "SetRealReg(QString, QString, QString, QString)", rreg[0], rreg[1], rreg[2], rreg[3])
            if rreg[2] == "215;20;214":
                self.windowQ.put([1, f"실시간 알림 등록 {ret} 장시작시간"])
            elif rreg[2] == "20;10":
                self.windowQ.put([1, f"실시간 알림 등록 {ret} 업종지수"])
            elif rreg[2] == "10;12;14;30;228":
                count = len(rreg[1].split(";"))
                if count == 1:
                    name = self.GetMasterCodeName(rreg[1])
                    self.windowQ.put([1, f"실시간 알림 등록 {ret} 주식체결 {name}"])
                else:
                    self.windowQ.put([1, f"실시간 알림 등록 {ret} 주식체결 {count}"])
        elif len(rreg) == 5:
            if not self.bool_hgup:
                return
            gubun = rreg[4]
            del rreg[4]
            if gubun == 'left':
                self.hoga_code[0] = rreg[1]
            elif gubun == 'right':
                self.hoga_code[1] = rreg[1]
            name = self.GetMasterCodeName(rreg[1])
            ret = self.ocx.dynamicCall(
                "SetRealReg(QString, QString, QString, QString)", rreg[0], rreg[1], rreg[2], rreg[3])
            self.windowQ.put([1, f"실시간 알림 등록 {ret} 주식호가잔량 {name}"])
        else:
            ret = self.ocx.dynamicCall("SetRealRemove(QString, QString)", rreg[0], rreg[1])
            name = self.GetMasterCodeName(rreg[1])
            self.windowQ.put([1, f"실시간 알림 중단 {ret} {name}"])

    def RunWork(self, work):    # 약 600줄  'work' 변수를 어떻게 사용하느냐가 중요
        if "left분봉일봉" in work:
            code = work.split(" ")[1]
            name = self.GetMasterCodeName(code)
            if code == self.chart_code[0] or code == self.chart_code[2]:
                return
            if not self.TrtimeCondition:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
                return
            self.hogaQ.put('left초기화')
            self.GetMinDayChart('left', code, name)
        elif "left주봉월봉" in work:
            code = work.split(" ")[1]
            name = self.GetMasterCodeName(code)
            if code == self.chart_code[1] or code == self.chart_code[3]:
                return
            if not self.TrtimeCondition:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
                return
            self.hogaQ.put('left초기화')
            self.GetWeekMonthChart('left', code, name)
        elif "right분봉일봉" in work:
            code = work.split(" ")[1]
            name = self.GetMasterCodeName(code)
            if code == self.chart_code[0] or code == self.chart_code[2]:
                return
            if not self.TrtimeCondition:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
                return
            self.hogaQ.put('right초기화')
            self.GetMinDayChart('right', code, name)
        elif "right주봉월봉" in work:
            code = work.split(" ")[1]
            name = self.GetMasterCodeName(code)
            if code == self.chart_code[1] or code == self.chart_code[3]:
                return
            if not self.TrtimeCondition:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
                return
            self.hogaQ.put('right초기화')
            self.GetWeekMonthChart('right', code, name)
        elif "center분봉일봉" in work:
            code = work.split(" ")[1]
            name = self.GetMasterCodeName(code)
            if code == self.chart_code[4]:
                return
            if not self.TrtimeCondition:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
                return
            self.GetMinDayChart('center', code, name)
        elif "chegeol분봉일봉" in work:
            code = work.split(" ")[1]
            name = self.GetMasterCodeName(code)
            if code == self.chart_code[5]:
                return
            if not self.TrtimeCondition:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
                return
            self.GetMinDayChart('chegeol', code, name)
        elif "테마그룹" in work:
            if not self.TrtimeCondition:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
                return
            self.GetThemaGroup()
        elif "테마구성종목" in work:
            code = work.split(" ")[1]
            if not self.TrtimeCondition:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
                return
            self.GetThemaJongmok(code)
        elif "매수취소" in work:
            code = work.split(" ")[1]
            name = self.GetMasterCodeName(code)
            for on in self.df_cj.index:
                if self.df_cj['종목명'][on] == name and self.df_cj['주문구분'][on] == "매수" and \
                        self.df_cj['미체결수량'][on] > 0:
                    omc = self.df_cj['미체결수량'][on]
                    op = self.df_cj['주문가격'][on]
                    work = ["매수취소", "4989", self.str_acct, 3, code, omc, op, "00", on, name, "수동"]
                    self.workerQ.put(work)
        elif "매도취소" in work:
            code = work.split(" ")[1]
            name = self.GetMasterCodeName(code)
            for on in self.df_cj.index:
                if self.df_cj['종목명'][on] == name and self.df_cj['주문구분'][on] == "매도" and \
                        self.df_cj['미체결수량'][on] > 0:
                    omc = self.df_cj['미체결수량'][on]
                    op = self.df_cj['주문가격'][on]
                    work = ["매도취소", "4989", self.str_acct, 4, code, omc, op, "00", on, name, "수동"]
                    self.workerQ.put(work)
        elif work == "보유종목 일괄청산":
            for code in self.df_jg.index:
                name = self.df_jg['종목명'][code]
                jc = self.df_jg['보유수량'][code]
                bc = 1
                if code in self.df_cbc.index:
                    bc = self.df_cbc['매수횟수'][code]
                df = pd.DataFrame({'전략구분': ["CAS"], '매수횟수': [bc]}, index=[code])
                self.df_od = self.df_od.append(df)
                work = ["매도", "4989", self.str_acct, 2, code, jc, 0, "03", "", name, "수동"]
                self.workerQ.put(work)
        elif work == "계좌평가 및 잔고":
            if self.TrtimeCondition:
                self.windowQ.put([4, "계좌평가 및 잔고"])
                self.GetAccountjanGo()
            else:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
        elif work == "장운영상태":
            self.windowQ.put([4, "장운영상태"])
            self.int_oper = 3
        elif work == "관심종목 정보":
            if self.TrtimeCondition:
                self.df_gs = pd.DataFrame(
                    columns=['종목명', 'HMP', '현재가', '등락율', '거래대금', '증감비율', '체결강도',
                             '종목코드', '시가', '고가', '저가', '전일종가', 'HML'])
                codes = self.SendCondition(str(screen_csrc + 3), self.df_cdb['조건명'][3], 3, 0)
                for code in codes:
                    name = self.GetMasterCodeName(code)
                    self.df_gs = self.df_gs.append(pd.DataFrame({
                        '종목명': [name], 'HMP': [0], '현재가': [0], '등락율': [0.00], '거래대금': [0], '증감비율': [0],
                        '체결강도': [0], '종목코드': [code], '시가': [0], '고가': [0], '저가': [0], '전일종가': [0],
                        'HML': [0]}, index=[code]))
                self.UpdateHML(Check=True)
                self.windowQ.put(self.df_gs)
            else:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
        elif work == "매수횟수 정리":
            self.DeleteBuycount()
        elif work == "CAD 매수 검색":
            if self.TrtimeCondition:
                self.GetCadbuycodes()
            else:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
        elif work == "CAD 매수 실행":
            if self.TrtimeCondition:
                if self.list_cad is None:
                    self.windowQ([1, "CAD매수검색을 먼저 실행하십시오."])
                else:
                    self.BuyCad()
            else:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
        elif work == "BNF 매수 검색":
            if self.TrtimeCondition:
                self.GetBnfbuycodes()
            else:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
        elif work == "BNF 매수 실행":
            if self.TrtimeCondition:
                if self.list_bb05 is None or self.list_bb00 is None:
                    self.windowQ([1, "BNF매수검색을 먼저 실행하십시오."])
                else:
                    self.BuyBnf()
            else:
                self.windowQ.put([1, f"해당 명령은 {self.RemainedTrtime}초 후에 실행됩니다."])
                Timer(self.RemainedTrtime, self.workerQ.put, args=[work]).start()
        elif work == "일별목록 저장":
            self.SaveTotaltradelist()
        elif work == "데이터 다운로드":
            self.windowQ.put([4, "데이터 다운로드"])
            self.DownloadData()
            os.system(f"shutdown /s /t {self.int_shut}")
            self.SysExit()
        elif work == "테스트모드 ON/OFF":
            if self.bool_test:
                self.bool_test = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_test'")
                self.windowQ.put([4, "테스트모드 OFF"])
                if self.bool_sound:
                    self.soundQ.put("테스트모드 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_test = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_test'")
                self.windowQ.put([4, "테스트모드 ON"])
                if self.bool_sound:
                    self.soundQ.put("테스트모드 설정이 ON으로 변경되었습니다.")
        elif work == "지수트렌드 ON/OFF":
            if self.bool_jstd:
                self.bool_jstd = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_jstd'")
                self.windowQ.put([4, "지수트렌드 OFF"])
                if self.bool_sound:
                    self.soundQ.put("지수트렌드 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_jstd = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_jstd'")
                self.windowQ.put([4, "지수트렌드 ON"])
                if self.bool_sound:
                    self.soundQ.put("지수트렌드 설정이 ON으로 변경되었습니다.")
        elif work == "전략CAS ON/OFF":
            if self.bool_cas:
                self.bool_cas = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_cas'")
                self.windowQ.put([4, "전략CAS OFF"])
                if self.bool_sound:
                    self.soundQ.put("전략카스 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_cas = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_cas'")
                self.windowQ.put([4, "전략CAS ON"])
                if self.bool_sound:
                    self.soundQ.put("전략카스 설정이 ON으로 변경되었습니다.")
        elif work == "전략CAD ON/OFF":
            if self.bool_cad:
                self.bool_cad = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_cad'")
                self.windowQ.put([4, "전략CAD OFF"])
                if self.bool_sound:
                    self.soundQ.put("전략카드 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_cad = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_cad'")
                self.windowQ.put([4, "전략CAD ON"])
                if self.bool_sound:
                    self.soundQ.put("전략카드 설정이 ON으로 변경되었습니다.")
        elif work == "전략BNF ON/OFF":
            if self.bool_bnf:
                self.bool_bnf = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_bnf'")
                self.windowQ.put([4, "전략BNF OFF"])
                if self.bool_sound:
                    self.soundQ.put("전략BNF 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_bnf = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_bnf'")
                self.windowQ.put([4, "전략BNF ON"])
                if self.bool_sound:
                    self.soundQ.put("전략BNF 설정이 ON으로 변경되었습니다.")
        elif work == "자동비중조절 ON/OFF":
            if self.bool_atbj:
                self.bool_atbj = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_atbj'")
                self.windowQ.put([4, "자동비중조절 OFF"])
                if self.bool_sound:
                    self.soundQ.put("자동비중조절 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_atbj = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_atbj'")
                self.windowQ.put([4, "자동비중조절 ON"])
                if self.bool_sound:
                    self.soundQ.put("자동비중조절 설정이 ON으로 변경되었습니다.")
        elif work == "차트 ON/OFF":
            if self.bool_chup:
                self.bool_chup = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_chup'")
                self.windowQ.put([4, "차트 OFF"])
                self.chartQ.put(f"차트ONOFF {self.bool_chup}")
                if self.bool_sound:
                    self.soundQ.put("차트 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_chup = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_chup'")
                self.windowQ.put([4, "차트 ON"])
                self.chartQ.put(f"차트ONOFF {self.bool_chup}")
                if self.bool_sound:
                    self.soundQ.put("차트 설정이 ON으로 변경되었습니다.")
        elif work == "호가창 ON/OFF":
            if self.bool_hgup:
                self.bool_hgup = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_hgup'")
                self.windowQ.put([4, "호가창 OFF"])
                self.hogaQ.put(f"호가ONOFF {self.bool_hgup}")
                if self.bool_sound:
                    self.soundQ.put("호가창 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_hgup = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_hgup'")
                self.windowQ.put([4, "호가창 ON"])
                self.hogaQ.put(f"호가ONOFF {self.bool_hgup}")
                if self.bool_sound:
                    self.soundQ.put("호가창 설정이 ON으로 변경되었습니다.")
        elif work == "알림소리 ON/OFF":
            if self.bool_sound:
                if self.bool_sound:
                    self.soundQ.put("알림소리 설정이 OFF로 변경되었습니다.")
                self.bool_sound = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_sound'")
                self.windowQ.put([4, "알림소리 OFF"])
            else:
                self.bool_sound = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_sound'")
                self.windowQ.put([4, "알림소리 ON"])
                if self.bool_sound:
                    self.soundQ.put("알림소리 설정이 ON으로 변경되었습니다.")
        elif work == "부가정보 ON/OFF":
            if self.bool_info:
                self.bool_info = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_info'")
                self.windowQ.put([4, "부가정보 OFF"])
                self.chartQ.put(f"부가정보ONOFF {self.bool_info}")
                self.hogaQ.put(f"부가정보ONOFF {self.bool_info}")
                if self.bool_sound:
                    self.soundQ.put("부가정보 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_info = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_info'")
                self.windowQ.put([4, "부가정보 ON"])
                self.chartQ.put(f"부가정보ONOFF {self.bool_info}")
                self.hogaQ.put(f"부가정보ONOFF {self.bool_info}")
                if self.bool_sound:
                    self.soundQ.put("부가정보 설정이 ON으로 변경되었습니다.")
        elif work == "다운로드 ON/OFF":
            if self.bool_down:
                self.bool_down = 0
                self.queryQ.put("UPDATE setting SET 설정 = 0 WHERE 구분 = 'bool_down'")
                self.windowQ.put([4, "다운로드 OFF"])
                if self.bool_sound:
                    self.soundQ.put("다운로드 설정이 OFF로 변경되었습니다.")
            else:
                self.bool_down = 1
                self.queryQ.put("UPDATE setting SET 설정 = 1 WHERE 구분 = 'bool_down'")
                self.windowQ.put([4, "다운로드 ON"])
                if self.bool_sound:
                    self.soundQ.put("다운로드 설정이 ON으로 변경되었습니다.")
        elif "전략CAS 기본매수비율" in work:
            text = work.split(" ")[-1]
            self.int_bcbp = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_bcbp'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 기본매수비율을 증권자산 {text}분의 1로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 기본매수비율을 증권자산 1/{text}로 변경 완료"])
        elif "전략CAS 최대매수비율" in work:
            text = work.split(" ")[-1]
            self.int_mcbp = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_mcbp'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 최대매수비율을 증권자산 {text}분의 1로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 최대매수비율을 증권자산 1/{text}로 변경 완료"])
        elif "전략CAS 분할매도비율" in work:
            text = work.split(" ")[-1]
            self.int_cdsp = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_cdsp'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 분할매도비율을 보유수량 {text}분의 1로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 분할매도비율을 보유수량 1/{text}로 변경 완료"])
        elif "전략CAS 최고거래대금비율" in work:
            text = work.split(" ")[-1]
            self.int_hmlp = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_hmlp'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 최고거래대금비율을 {text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 최고거래대금비율을 {text}%로 변경 완료"])
        elif "전략CAS 매수제한등락율" in work:
            text = work.split(" ")[-1]
            self.int_hper = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_hper'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 매수제한등락율를 {text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 매수제한등락율를 {text}%로 변경 완료"])
        elif "전략CAS 전량청산보유금액" in work:
            text = work.split(" ")[-1]
            self.int_sbgm = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_sbgm'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 전량청산보유금액을 {text}000원으로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 전량청산보유금액을 {text}000원로 변경 완료"])
        elif "전략CAS 청산라인등락율" in work:
            text = work.split(" ")[-1]
            self.int_sper = float(text)
            self.chartQ.put(f"전략CAS 청산라인등락율 {text}")
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text)}' WHERE 구분 = 'int_sper'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 청산라인등락율을 {text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 청산라인등락율을 {text}%로 변경 완료"])
            for code in self.df_cbc.index:
                SELL = int(round(self.df_cbc['BUY1'][code] * (1 + self.int_sper / 100)))
                self.df_cbc.at[code, 'SELL'] = SELL
                self.queryQ.put(f"UPDATE casbuycount SET SELL = {SELL} WHERE 종목코드 = '{code}'")
        elif "전략CAS 본전청산최저수익률" in work:
            text = work.split(" ")[-1]
            self.int_cslp = float(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text)}' WHERE 구분 = 'int_cslp'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 본전청산최저수익률을 {text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 본전청산최저수익률을 {text}%로 변경 완료"])
        elif "전략CAS 추가매수등락율" in work:
            text = work.split(" ")[-1]
            self.int_cpsp = float(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text)}' WHERE 구분 = 'int_cpsp'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 추가매수등락율을 {text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 추가매수등락율을 {text}%로 변경 완료"])
        elif "전략CAS 분할매도최소등락율" in work:
            text = work.split(" ")[-1]
            self.int_dper = float(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text)}' WHERE 구분 = 'int_dper'")
            if self.bool_sound:
                self.soundQ.put(f"전략카스 분할매도최소등락율을 {text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAS 분할매도최소등락율을 {text}%로 변경 완료"])
        elif "전략CAD 기본매수비율" in work:
            text = work.split(" ")[-1]
            self.int_bdbp = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_bdbp'")
            if self.bool_sound:
                self.soundQ.put(f"전략카드 기본매수비율을 증권자산 {text}분의 1로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAD 기본매수비율을 증권자산 1/{text}로 변경 완료"])
        elif "전략CAD 청산라인등락율" in work:
            text = work.split(" ")[-1]
            self.int_cbsp = float(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text)}' WHERE 구분 = 'int_cbsp'")
            if self.bool_sound:
                self.soundQ.put(f"전략카드 청산라인등락율을 {text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략CAD 청산라인등락율을 {text}%로 변경 완료"])
        elif "전략BNF 기본매수비율" in work:
            text = work.split(" ")[-1]
            self.int_bbbp = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_bbbp'")
            if self.bool_sound:
                self.soundQ.put(f"전략BNF 기본매수비율을 증권자산 {text}분의 1로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략BNF 기본매수비율을 증권자산 1/{text}로 변경 완료"])
        elif "전략BNF 분할매도비율" in work:
            text = work.split(" ")[-1]
            self.int_bdsp = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_bdsp'")
            if self.bool_sound:
                self.soundQ.put(f"전략BNF 분할매도비율을 보유수량 {text}분의 1로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"전략BNF 분할매도비율을 보유수량 1/{text}로 변경 완료"])
        elif "전략설정전체목록일괄설정" in work:
            text = work.split(" ")
            self.int_bcbp = int(text[1])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text[1])}' WHERE 구분 = 'int_bcbp'")
            self.int_mcbp = int(text[2])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text[2])}' WHERE 구분 = 'int_mcbp'")
            self.int_cdsp = int(text[3])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text[3])}' WHERE 구분 = 'int_cdsp'")
            self.int_hmlp = int(text[4])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text[4])}' WHERE 구분 = 'int_hmlp'")
            self.int_hper = int(text[5])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text[5])}' WHERE 구분 = 'int_hper'")
            self.int_sbgm = int(text[6])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text[6])}' WHERE 구분 = 'int_sbgm'")
            self.int_sper = float(text[7])
            self.chartQ.put(f"전략CAS 청산라인등락율 {text[7]}")
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text[7])}' WHERE 구분 = 'int_sper'")
            for code in self.df_cbc.index:
                SELL = int(round(self.df_cbc['BUY1'][code] * (1 + self.int_sper / 100)))
                self.df_cbc.at[code, 'SELL'] = SELL
                self.queryQ.put(f"UPDATE casbuycount SET SELL = {SELL} WHERE 종목코드 = '{code}'")
            self.int_cslp = float(text[8])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text[8])}' WHERE 구분 = 'int_cslp'")
            self.int_cpsp = float(text[9])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text[9])}' WHERE 구분 = 'int_cpsp'")
            self.int_dper = float(text[10])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text[10])}' WHERE 구분 = 'int_dper'")
            self.int_bdbp = int(text[11])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text[11])}' WHERE 구분 = 'int_bdbp'")
            self.int_cbsp = float(text[12])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text[12])}' WHERE 구분 = 'int_cbsp'")
            self.int_bbbp = int(text[13])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text[13])}' WHERE 구분 = 'int_bbbp'")
            self.int_bdsp = int(text[14])
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text[14])}' WHERE 구분 = 'int_bdsp'")
            if self.bool_sound:
                self.soundQ.put("전략설정 전체목록이 변경되었습니다.")
            else:
                self.windowQ.put([1, "전략설정 전체목록 변경 완료"])
        elif "관심종목잔고 갱신시간" in work:
            text = work.split(" ")[-1]
            self.int_gjut = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_gjut'")
            if self.bool_sound:
                self.soundQ.put(f"관심종목 및 잔고 갱신시간을 {text}초로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"관심종목 및 잔고 갱신시간을 {text}초로 변경 완료"])
        elif "실시간차트 갱신시간" in work:
            text = work.split(" ")[-1]
            self.int_rcut = int(text)
            self.chartQ.put(f"실시간차트 갱신시간 {text}")
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_rcut'")
            if self.bool_sound:
                self.soundQ.put(f"실시간차트 갱신시간을 {text}초로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"실시간차트 갱신시간을 {text}초로 변경 완료"])
        elif "부가정보 갱신시간" in work:
            text = work.split(" ")[-1]
            self.int_siut = int(text)
            self.hogaQ.put(f"부가정보 갱신시간 {text}")
            self.chartQ.put(f"부가정보 갱신시간 {text}")
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_siut'")
            if self.bool_sound:
                self.soundQ.put(f"부가정보 갱신시간을 {text}초로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"부가정보 갱신시간을 {text}초로 변경 완료"])
        elif "TR조회제한 1회당시간" in work:
            text = work.split(" ")[-1]
            self.int_trot = float(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text)}' WHERE 구분 = 'int_trot'")
            if self.bool_sound:
                self.soundQ.put(f"TR조회제한 1회당시간을 {text}초로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"TR조회제한 1회당시간을 {text}초로 변경 완료"])
        elif "TR조회제한 계산시점" in work:
            text = work.split(" ")[-1]
            self.int_trct = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_trct'")
            if text[-1:] in ["0", "3", "6"]:
                text = text + "으"
            if self.bool_sound:
                self.soundQ.put(f"TR조회제한 계산시점을 조회횟수 {text}회 이상으로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"TR조회제한 계산시점을 조회횟수 {text}회 이상으로 변경 완료"])
        elif "메인이벤트루프 대기시간" in work:
            text = work.split(" ")[-1]
            self.int_medt = float(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text)}' WHERE 구분 = 'int_medt'")
            if self.bool_sound:
                self.soundQ.put(f"메인이벤트루프 대기시간을 {text}초로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"메인이벤트루프 대기시간을 {text}초로 변경 완료"])
        elif "조회이벤트루프 대기시간" in work:
            text = work.split(" ")[-1]
            self.int_sedt = float(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text)}' WHERE 구분 = 'int_sedt'")
            if self.bool_sound:
                self.soundQ.put(f"조회이벤트루프 대기시간을 {text}초로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"조회이벤트루프 대기시간을 {text}초로 변경 완료"])
        elif "이벤트루프 슬립시간" in work:
            text = work.split(" ")[-1]
            self.int_elst = float(text)
            self.hogaQ.put(f"이벤트루프 슬립시간 {text}")
            self.chartQ.put(f"이벤트루프 슬립시간 {text}")
            self.queryQ.put(f"이벤트루프 슬립시간 {text}")
            self.soundQ.put(f"이벤트루프 슬립시간 {text}")
            self.queryQ.put(f"UPDATE setting SET 설정 = '{float(text)}' WHERE 구분 = 'int_elst'")
            if self.bool_sound:
                self.soundQ.put(f"이벤트루프 슬립시간을 {text}초로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"이벤트루프 슬립시간을 {text}초로 변경 완료"])
        elif "휴장유무 확인시간" in work:
            text = work.split(" ")[-1]
            self.int_hjof = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_hjof'")
            if self.bool_sound:
                self.soundQ.put(f"휴장유무 확인시간을 {text}초로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"휴장유무 확인시간을 {text}초로 변경 완료"])
        elif "컴퓨터종료 대기시간" in work:
            text = work.split(" ")[-1]
            self.int_shut = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_shut'")
            if self.bool_sound:
                self.soundQ.put(f"컴퓨터종료 대기시간을 {text}초로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"컴퓨터종료 대기시간을 {text}초로 변경 완료"])
        elif "매수수수료" in work:
            text = work.split(" ")[-1]
            self.int_stax = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_stax'")
            if self.bool_sound:
                self.soundQ.put(f"매수수수료를 0.0{text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"매수수수료를 0.0{text}%로 변경 완료"])
        elif "매도수수료" in work:
            text = work.split(" ")[-1]
            self.int_btax = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_btax'")
            if self.bool_sound:
                self.soundQ.put(f"매도수수료를 0.0{text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"매도수수료를 0.0{text}%로 변경 완료"])
        elif "제세공과금" in work:
            text = work.split(" ")[-1]
            self.int_fees = int(text)
            self.queryQ.put(f"UPDATE setting SET 설정 = '{int(text)}' WHERE 구분 = 'int_fees'")
            if self.bool_sound:
                self.soundQ.put(f"제세공과금을 0.{text}%로 변경하였습니다.")
            else:
                self.windowQ.put([1, f"제세공과금을 0.{text}%로 변경 완료"])
        elif "텔레그램" in work:
            bot_number = work.split(" ")[1]
            chat_id = work.split(" ")[2]
            self.str_bot = bot_number
            self.int_id = int(chat_id)
            self.queryQ.put(f"UPDATE telegram SET str_bot = '{bot_number}'")
            self.queryQ.put(f"UPDATE telegram SET int_id = '{int(chat_id)}'")
            if self.bool_sound:
                self.soundQ.put("텔레그램 봇넘버 및 아이디가 변경되었습니다.")
            else:
                self.windowQ.put([1, "텔레그램 봇넘버 및 아이디 설정 완료"])
        elif "코스피추세" in work:
            if work.split(" ")[-1] == "상승":
                self.bool_kpcs = True
            else:
                self.bool_kpcs = False
        elif "코스닥추세" in work:
            if work.split(" ")[-1] == "상승":
                self.bool_kdcs = True
            else:
                self.bool_kdcs = False
        elif work == "시스템 종료":
            self.windowQ.put([4, "시스템 종료"])
            self.SysExit()    #    #

    def GetMinDayChart(self, gubun, code, name):
        df = self.Block_Request("opt10081", 종목코드=code, 기준일자=self.str_tday, 수정주가구분=0,
                                output="주식일봉차트조회", next=0)
        df2 = self.Block_Request("opt10080", 종목코드=code, 틱범위=5, 수정주가구분=0,
                                 output="주식분봉차트조회", next=0)
        pc = self.GetMasterLastPrice(code)
        if gubun == 'left':
            self.chart_code[0] = code
            self.chartQ.put(["left일봉분봉", name, pc, df, df2])
            self.GetJongmokTujaja(gubun, code)
        elif gubun == 'right':
            self.chart_code[2] = code
            self.chartQ.put(["right일봉분봉", name, pc, df, df2])
            self.GetJongmokTujaja(gubun, code)
        elif gubun == 'center':
            self.chart_code[4] = code
            self.chart_code[5] = ''
            self.chartQ.put(["center일봉분봉", name, pc, df, df2])
        elif gubun == 'chegeol':
            self.chart_code[5] = code
            self.chart_code[4] = ''
            self.chartQ.put(["chegeol일봉분봉", name, pc, df, df2])
        self.UpdateTrtime()

    def GetJongmokTujaja(self, gubun, code):
        df = self.Block_Request("opt10059", 일자=self.str_tday, 종목코드=code, 금액수량구분=2, 매매구분=0,
                                단위구분=1, output="종목별투자자기관별", next=0)
        try:
            df.rename(columns={'일자': f'{gubun}일자', '개인투자자': '개인', '외국인투자자': '외국인',
                               '기관계': '기관', '현재가': '종가'}, inplace=True)
            df = df[[f'{gubun}일자', '개인', '외국인', '기관', '종가', '전일대비', '등락율']].copy()
        except Exception as e:
            self.log.info(f"[{strtime()}] GetTujajaInfo 종목별투자자기관별 {e}")
        else:
            self.windowQ.put(df)

    def GetWeekMonthChart(self, gubun, code, name):
        lday = (datetime.datetime.now() + datetime.timedelta(days=-600)).strftime("%Y%m%d")
        df = self.Block_Request("opt10082", 종목코드=code, 기준일자=self.str_tday, 끝일자=lday, 수정주가구분=0,
                                output="주식주봉차트조회", next=0)
        df2 = self.Block_Request("opt10083", 종목코드=code, 기준일자=self.str_tday, 끝일자=lday, 수정주가구분=0,
                                 output="주식월봉차트조회", next=0)
        if gubun == 'left':
            self.chart_code[1] = code
            self.chartQ.put(["left주봉월봉", name, "", df, df2])
            self.GetJongmokTujaja(gubun, code)
        elif gubun == 'right':
            self.chart_code[3] = code
            self.chartQ.put(["right주봉월봉", name, "", df, df2])
            self.GetJongmokTujaja(gubun, code)
        self.UpdateTrtime()

    def GetThemaGroup(self):
        df = []
        df2 = self.Block_Request("opt90001", 검색구분="0", 날짜구분="99", 등락수익구분="3", output="테마그룹별", next=0)
        df2['인덱스'] = df2['종목코드']
        df2 = df2.set_index('인덱스')
        df.append(df2)
        while self.bool_trremained:
            df2 = self.Block_Request("opt90001", 검색구분="0", 날짜구분="99", 등락수익구분="3", output="테마그룹별", next=2)
            df2['인덱스'] = df2['종목코드']
            df2 = df2.set_index('인덱스')
            df.append(df2)
        df = pd.concat(df)
        df['등락율'] = df['등락율'].apply(lambda x: float(x))
        df = df[['종목코드', '테마명', '등락율', '종목수', '상승종목수', '하락종목수', '기간수익률']].copy()
        df.sort_values(by=['등락율'], ascending=False, inplace=True)
        df.rename(columns={'테마명': 't1테마명'}, inplace=True)
        self.windowQ.put(df[0:58])
        df.rename(columns={'t1테마명': 't2테마명'}, inplace=True)
        self.windowQ.put(df[58:116])
        df.rename(columns={'t2테마명': 't3테마명'}, inplace=True)
        self.windowQ.put(df[116:len(df)])
        df = []
        df2 = self.Block_Request("opt20003", 업종코드="001", output="전업종지수", next=0)
        df2['인덱스'] = df2['종목코드']
        df2 = df2.set_index('인덱스')
        df.append(df2)
        df2 = self.Block_Request("opt20003", 업종코드="101", output="전업종지수", next=0)
        df2['인덱스'] = df2['종목코드']
        df2 = df2.set_index('인덱스')
        df.append(df2)
        df = pd.concat(df)
        df['등락율'] = df['등락률'].apply(lambda x: float(x))
        df = df[['종목코드', '종목명', '현재가', '전일대비', '등락율', '거래량', '상장종목수']].copy()
        df.drop(index=['001', '002', '003', '004', '603', '604', '605', '101', '103', '104', '138', '139', '140',
                       '142', '143', '144', '145', '150', '160', '165'], inplace=True)
        df.sort_values(by=['등락율'], ascending=False, inplace=True)
        self.windowQ.put(df)
        self.UpdateTrtime()

    def GetThemaJongmok(self, code):
        df = self.Block_Request("opt90002", 날짜구분="99", 종목코드=code, output="테마구성종목", next=0)
        df['등락율'] = df['등락율'].apply(lambda x: float(x))
        df['인덱스'] = df['종목코드']
        df = df.set_index('인덱스')
        df = df[['종목코드', '종목명', '현재가', '전일대비', '등락율', '누적거래량', '기간수익률n']].copy()
        self.windowQ.put(df)
        self.UpdateTrtime()

    def GetAccountjanGo(self):
        error = True
        while error:
            df = self.Block_Request("opw00004", 계좌번호=self.str_acct, 비밀번호="", 비밀번호입력매체구분="00", 조회구분=1,
                                    output="계좌평가현황", next=0)
            try:
                self.int_ysgm = int(df['D+2추정예수금'][0])
            except ValueError:
                self.windowQ.put([1, "오류가 발생하여 계좌평가현황을 재조회합니다."])
                time.sleep(self.int_trot - self.int_sedt)
            else:
                error = False
        error = True
        while error:
            df = self.Block_Request("opw00018", 계좌번호=self.str_acct, 비밀번호="", 비밀번호입력매체구분="00", 조회구분=2,
                                    output="계좌평가결과", next=0)
            try:
                totaljasan = int(df['추정예탁자산'][0])
                self.int_cbat = int(round(totaljasan / self.int_bcbp))
                self.int_bbat = int(round(totaljasan / self.int_bbbp))
                self.int_dbat = int(round(totaljasan / self.int_bdbp))
                self.df_tj = pd.DataFrame({
                    '추정예탁자산': [totaljasan], '추정예수금': [self.int_ysgm], '수익률평균': [0],
                    '총수익률': [float(df['총수익률(%)'][0])], '총평가손익': [int(df['총평가손익금액'][0])],
                    '총매입금액': [int(df['총매입금액'][0])], '총평가금액': [int(df['총평가금액'][0])]}, index=[0])
            except ValueError:
                self.windowQ.put([1, "오류가 발생하여 계좌평가결과를 재조회합니다."])
                time.sleep(self.int_trot - self.int_sedt)
            else:
                error = False
                self.windowQ.put(self.df_tj)
        df = []
        error = True
        while error:
            df2 = self.Block_Request("opw00018", 계좌번호=self.str_acct, 비밀번호="", 비밀번호입력매체구분="00", 조회구분=2,
                                     output="계좌평가잔고개별합산", next=0)
            try:
                for i, code in enumerate(df2['종목번호']):
                    df2['종목번호'][i] = code.strip('A')
            except ValueError:
                if len(df2) != 0:
                    error = False
                else:
                    self.windowQ.put([1, "오류가 발생하여 계좌평가잔고개별합산을 재조회합니다."])
                    time.sleep(self.int_trot - self.int_sedt)
            else:
                error = False
                df.append(df2)
        while self.bool_trremained:
            df2 = self.Block_Request("opw00018", 계좌번호=self.str_acct, 비밀번호="", 비밀번호입력매체구분="00", 조회구분=2,
                                     output="계좌평가잔고개별합산", next=2)
            try:
                for i, code in enumerate(df2['종목번호']):
                    df2['종목번호'][i] = code.strip('A')
            except Exception as e:
                self.log.info(f"[{strtime()}] GetAccountJanGo 계좌평가잔고개별합산 2 {e}")
            else:
                df.append(df2)
        if len(df) > 0:
            try:
                df = pd.concat(df)
                df = df.set_index('종목번호')
                rregcodelist = []
                df['매입가'] = df['매입가'].apply(lambda x: int(x))
                df['현재가'] = df['현재가'].apply(lambda x: abs(int(x)))
                df['수익률(%)'] = df['수익률(%)'].apply(lambda x: float(x))
                df['평가손익'] = df['평가손익'].apply(lambda x: int(x))
                df['매입금액'] = df['매입금액'].apply(lambda x: int(x))
                df['평가금액'] = df['평가금액'].apply(lambda x: int(x))
                df['보유수량'] = df['보유수량'].apply(lambda x: int(x))
                self.df_jg = pd.DataFrame(
                    columns=['종목명', '매입가', '현재가', '수익률', '평가손익', '매입금액', '평가금액',
                             '종목코드', '시가', '고가', '저가', '전일종가', '보유수량', '최고수익률', '최저수익률'])
                for code in df.index:
                    self.df_jg = self.df_jg.append(pd.DataFrame({
                        '종목명': [df['종목명'][code]], '매입가': [df['매입가'][code]], '현재가': [df['현재가'][code]],
                        '수익률': [df['수익률(%)'][code]], '평가손익': [df['평가손익'][code]],
                        '매입금액': [df['매입금액'][code]], '평가금액': [df['평가금액'][code]], '종목코드': [code],
                        '시가': [0], '고가': [0], '저가': [0], '전일종가': [0], '보유수량': [df['보유수량'][code]],
                        '최고수익률': [0], '최저수익률': [0]}, index=[code]))
                    rregcodelist.append(code)
            except Exception as e:
                self.log.info(f"[{strtime()}] GetAccountJanGo 계좌평가잔고개별합산 {e}")
            else:
                for i in range(0, len(rregcodelist), 100):
                    j = i + 100
                    screen_no = str(screen_jgjc + 1 + i / 100)
                    self.workerQ.put([screen_no, ";".join(rregcodelist[i:j]), "10;12;14;30;228", 1])
                self.df_jg.sort_values(by=['매입금액'], ascending=False, inplace=True)
                self.windowQ.put(self.df_jg)
        self.windowQ.put([4, "계좌평가 및 잔고"])
        self.windowQ.put([1, "계좌평가 및 잔고 데이터 불러오기 완료"])
        self.UpdateTrtime()

    def GetKpcKdcChart(self):
        error = True
        while error:
            df = self.Block_Request("opt20005", 업종코드="001", 틱범위=5, output="업종분봉조회", next=0)
            if len(df) > 80:
                self.chartQ.put(['코스피현재가', df])
                error = False
            else:
                self.windowQ.put([1, "오류가 발생하여 코스피종합차트를 재조회합니다."])
                time.sleep(self.int_trot - self.int_sedt)
        error = True
        while error:
            df = self.Block_Request("opt20005", 업종코드="101", 틱범위=5, output="업종분봉조회", next=0)
            if len(df) > 80:
                self.chartQ.put(['코스닥현재가', df])
                error = False
            else:
                self.windowQ.put([1, "오류가 발생하여 코스닥종합차트를 재조회합니다."])
                time.sleep(self.int_trot - self.int_sedt)
        self.windowQ.put([1, "코스피 코스닥 차트 조회 완료"])
        self.UpdateTrtime()

    def OperationRealreg(self):
        self.windowQ.put([4, "장운영시간"])
        self.workerQ.put([str(screen_jsjc), " ", "215;20;214", 0])
        if self.bool_sound:
            self.soundQ.put("시스템이 정상적으로 시작되었습니다.")
        else:
            self.windowQ.put([1, "시스템이 정상적으로 시작되었습니다."])

    def ConditionRealreg(self):
        self.workerQ.put([str(screen_oper), "001;101", "20;10", 1])
        self.windowQ.put([4, "장운영상태"])
        for cindex in [1, 2, 7, 8]:
            if self.bool_cas and cindex == 1:
                codes = self.SendCondition(str(screen_csrc + cindex), self.df_cdb['조건명'][cindex], cindex, 1)
                self.windowQ.put([1, f"조건검색식 {cindex} {self.df_cdb['조건명'][cindex]} 실시간 알림 등록 완료"])
                for code in codes:
                    if code in self.df_gs.index:
                        continue
                    name = self.GetMasterCodeName(code)
                    self.df_gs = self.df_gs.append(pd.DataFrame({
                        '종목명': [name], 'HMP': [0], '현재가': [0], '등락율': [0.00], '거래대금': [0], '증감비율': [0],
                        '체결강도': [0], '종목코드': [code], '시가': [0], '고가': [0], '저가': [0], '전일종가': [0],
                        'HML': [0]}, index=[code]))
            elif self.bool_cas and cindex == 2:
                self.SendCondition(str(screen_csrc + cindex), self.df_cdb['조건명'][cindex], cindex, 1)
                self.windowQ.put([1, f"조건검색식 {cindex} {self.df_cdb['조건명'][cindex]} 실시간 알림 등록 완료"])
            elif self.bool_bnf and cindex in [7, 8]:
                codes = self.SendCondition(str(screen_csrc + cindex), self.df_cdb['조건명'][cindex], cindex, 1)
                self.windowQ.put([1, f"조건검색식 {cindex} {self.df_cdb['조건명'][cindex]} 실시간 알림 등록 완료"])
                for code in codes:
                    A = code not in self.df_od.index
                    B = cindex == 7 and code in self.df_jg.index and code in self.df_bbc.index
                    C = cindex == 8 and code in self.df_jg.index and code in self.df_bbc.index
                    if A and (B or C):
                        jc = self.df_jg['보유수량'][code]
                        bc = self.df_bbc['매수횟수'][code]
                        name, oc = self.GetMasterCodeName(code), int(round(jc * (1 / bc)))
                        if oc == 0:
                            oc = 1
                        if not self.bool_test:
                            self.Sell(code, "BNF", bc, oc, name)
        self.windowQ.put([4, "실시간 조건검색 등록"])
        self.UpdateTrtime()

    def UpdateHML(self, Check=False):
        codes = [code for code in self.df_gs.index if self.df_gs['HML'][code] == 0]
        if len(codes) > 0:
            rregcodelist = []
            for code in codes:
                if code in self.df_hm.index and not Check:
                    HML = self.df_hm['HML'][code]
                    if code in self.df_gs.index:
                        self.df_gs.at[code, 'HML'] = HML
                        if code not in self.df_jg.index:
                            rregcodelist.append(code)
                else:
                    df = self.Block_Request("opt10081", 종목코드=code, 기준일자=self.str_tday, 수정주가구분=1,
                                            output="주식일봉차트조회", next=0)
                    try:
                        df['현재가'] = df['현재가'].apply(lambda x: abs(int(x)))
                        df['고가'] = df['고가'].apply(lambda x: abs(int(x)))
                        df['거래대금'] = df['거래대금'].apply(lambda x: abs(int(x)))
                        HML = df['거래대금'][1:241].max()
                        lines = [df['고가'][1], df['현재가'][1:6].max(), df['현재가'][1:11].max(),
                                 df['현재가'][1:21].max(), df['고가'][1:6].max(), df['고가'][1:11].max(),
                                 df['고가'][1:21].max()]
                        lines.sort()
                        SELL = int(round(lines[0] * (1 + self.int_sper / 100)))
                    except Exception as e:
                        self.log.info(f"[{strtime()}] UpdateHML 주식일봉차트조회 {e}")
                    else:
                        if not Check:
                            self.df_hm = self.df_hm.append(pd.DataFrame({
                                'HML': [HML], 'SELL': [SELL], 'BUY1': [lines[0]], 'BUY2': [lines[1]],
                                'BUY3': [lines[2]], 'BUY4': [lines[3]], 'BUY5': [lines[4]],
                                'BUY6': [lines[5]], 'BUY7': [lines[6]]}, index=[code]))
                            if code in self.df_gs.index:
                                self.df_gs.at[code, 'HML'] = HML
                                if code not in self.df_jg.index:
                                    rregcodelist.append(code)
                        else:
                            if code not in self.df_hm.index:
                                self.df_hm = self.df_hm.append(pd.DataFrame({
                                    'HML': [HML], 'SELL': [SELL], 'BUY1': [lines[0]], 'BUY2': [lines[1]],
                                    'BUY3': [lines[2]], 'BUY4': [lines[3]], 'BUY5': [lines[4]],
                                    'BUY6': [lines[5]], 'BUY7': [lines[6]]}, index=[code]))
                            name = self.GetMasterCodeName(code)
                            HMP = int(round(df['거래대금'][0] / (HML * self.int_hmlp / 100) * 100))
                            c = df['현재가'][0]
                            per = round((df['현재가'][0] / df['현재가'][1] - 1) * 100, 2)
                            m = df['거래대금'][0]
                            vp = int(round(df['거래대금'][0] / df['거래대금'][1] * 100))
                            o = df['시가'][0]
                            h = df['고가'][0]
                            low = df['저가'][0]
                            prec = df['현재가'][1]
                            self.df_gs.at[code, :] = name, HMP, c, per, m, vp, 0, code, o, h, low, prec, HML
                            self.df_gs.sort_values(by=['등락율'], ascending=False, inplace=True)
            if not Check:
                screen_no = self.GetScreenNumber(len(rregcodelist))
                self.workerQ.put([screen_no, ";".join(rregcodelist), "10;12;14;30;228", 1])
            self.windowQ.put([4, "관심종목 정보"])
            self.UpdateTrtime()

    def GetScreenNumber(self, count):
        pre_int_screen = self.int_screen_gs
        self.int_screen_gs += count
        if int(self.int_screen_gs / 100) > int(pre_int_screen / 100):
            self.screen_gsjc = self.screen_gsjc + 1
            if self.screen_gsjc >= 1200:
                self.screen_gsjc = 1100
        return str(self.screen_gsjc)

    @Thread_Decorator
    def GetThemaJudoju(self):
        name_list = []
        bs = BeautifulSoup(requests.get(info_url_03).text, "lxml")
        names = bs.select('.col_type5')
        for name in names:
            name = name.get_text().strip("\n").strip("..")
            if name not in name_list:
                name_list.append(name)
        self.ThemaJudoju = name_list

    def RemoveALlRealreg(self):
        self.windowQ.put([4, "실시간 수신 중단"])
        for cindex in [1, 2, 7, 8]:
            self.ocx.dynamicCall("SendConditionStop(QString, QString, int)",
                                 str(screen_csrc + cindex), self.df_cdb['조건명'][cindex], cindex)
            sleeptime = datetime.datetime.now() + datetime.timedelta(seconds=+self.int_sedt)
            while datetime.datetime.now() < sleeptime:
                pythoncom.PumpWaitingMessages()
                time.sleep(self.int_elst)
        self.workerQ.put(["ALL", "ALL"])
        self.workerQ.put([str(screen_oper), " ", "215;20;214", 0])
        if self.bool_sound:
            self.soundQ.put("실시간알림의 수신을 중단하였습니다.")
        else:
            self.windowQ.put([1, "실시간 알림 수신 중단 요청 완료"])
        self.UpdateTrtime()

    @Thread_Decorator
    def DeleteBuycount(self):
        self.windowQ.put([4, "매수횟수 정리"])
        if len(self.df_jg) > 0:
            codes = [code for code in self.df_cbc.index if code not in self.df_jg.index]
            if len(codes) > 0:
                for code in codes:
                    self.df_cbc.drop(index=code, inplace=True)
                codes = "', '".join(codes)
                codes = "'" + codes + "'"
                self.queryQ.put(f"DELETE FROM casbuycount WHERE 종목코드 in ({codes})")
            codes = [code for code in self.df_dbc.index if code not in self.df_jg.index]
            if len(codes) > 0:
                for code in codes:
                    self.df_dbc.drop(index=code, inplace=True)
                codes = "', '".join(codes)
                codes = "'" + codes + "'"
                self.queryQ.put(f"DELETE FROM cadbuycount WHERE 종목코드 in ({codes})")
        else:
            for code in self.df_cbc.index:
                self.df_cbc.drop(index=code, inplace=True)
            for code in self.df_dbc.index:
                self.df_dbc.drop(index=code, inplace=True)
            self.queryQ.put("DELETE FROM casbuycount")
            self.queryQ.put("DELETE FROM cadbuycount")
        if self.bool_sound:
            self.soundQ.put("매수횟수 DB를 갱신하였습니다.")
        else:
            self.windowQ.put([1, "buycount DB 업데이트 완료"])

    @Thread_Decorator
    def SaveTotaltradelist(self):
        self.windowQ.put([4, "일별목록 저장"])
        df = self.df_tt[['총매수금액', '총매도금액', '총수익금액', '총손실금액', '수익률', '수익금합계']].copy()
        df['일자'] = self.str_tday
        df = df.set_index('일자')
        self.queryQ.put([df, "totaltradelist", "append"])
        if self.bool_sound:
            self.soundQ.put("당일거래집계를 저장하였습니다.")
        else:
            self.windowQ.put([1, "totaltradelist DB 저장 완료"])

    def GetBnfbuycodes(self):
        self.windowQ.put([4, "BNF 매수 검색"])
        self.list_bb05 = self.SendCondition(str(screen_csrc + 5), self.df_cdb['조건명'][5], 5, 0)
        self.list_bb00 = self.SendCondition(str(screen_csrc + 6), self.df_cdb['조건명'][6], 6, 0)
        bnfb1list = []
        for code in self.list_bb05:
            name = self.GetMasterCodeName(code)
            bnfb1list.append(name)
        bnfb2list = []
        for code in self.list_bb00:
            name = self.GetMasterCodeName(code)
            bnfb2list.append(name)
        bnfb1text = ", ".join(bnfb1list)
        bnfb2text = ", ".join(bnfb2list)
        self.windowQ.put([2, f"BNF 1차 매수종목 : {bnfb1text}"])
        self.windowQ.put([2, f"BNF 2차 매수종목 : {bnfb2text}"])
        if self.bool_sound:
            self.soundQ.put("전략BNF 매수종목을 검색하였습니다.")
        else:
            self.windowQ.put([2, "BNF 매수 종목 추출 완료"])
        self.UpdateTrtime()

    def BuyBnf(self):
        self.windowQ.put([4, "BNF 매수 실행"])
        codes1 = [code for code in self.list_bb05 if code not in self.df_jg.index and code in self.df_bdb.index]
        codes2 = [code for code in self.list_bb00 if
                  code in self.df_jg.index and code in self.df_bbc.index and self.df_bbc['매수횟수'][code] == 1]
        count = len(codes1)
        if count > 0:
            codelist = ";".join(codes1)
            df = self.Block_Request("optkwfid", codelist, count, output="관심종목정보", next=0)
            df = df.set_index('종목코드')
            for code in df.index:
                name = df['종목명'][code]
                c = abs(int(df['현재가'][code]))
                oc = int(round(self.int_bbat / len(codes1 + codes2) / c))
                if self.int_ysgm >= c * oc:
                    self.int_ysgm -= c * oc
                    if self.bool_bnf and not self.bool_test:
                        self.Buy(code, "BNF", 0, oc, name)
                else:
                    self.windowQ.put([2, f"BNF 매수 조건 확인 FALSE [시드부족] {name}"])
        if self.int_ysgm < self.int_bbat:
            return
        count = len(codes2)
        if count > 0:
            codelist = ";".join(codes2)
            df = self.Block_Request("optkwfid", codelist, count, output="관심종목정보", next=0)
            df = df.set_index('종목코드')
            for code in df.index:
                name = df['종목명'][code]
                c = abs(int(df['현재가'][code]))
                oc = int(round(self.int_bbat / len(codes1 + codes2) / c))
                if self.int_ysgm >= c * oc:
                    self.int_ysgm -= c * oc
                    if self.bool_bnf and not self.bool_test:
                        self.Buy(code, "BNF", 1, oc, name)
                else:
                    self.windowQ.put([2, f"BNF 매수 조건 확인 FALSE [시드부족] {name}"])
        if self.bool_sound:
            self.soundQ.put("전략BNF 추출종목을 매수주문하였습니다.")
        else:
            self.windowQ.put([1, "BNF 추출 종목 매수 주문 완료"])
        self.UpdateTrtime()

    def GetCadbuycodes(self):
        self.windowQ.put([4, "CAD 매수 검색"])
        self.list_cad = self.SendCondition(str(screen_csrc + 4), self.df_cdb['조건명'][4], 4, 0)
        cadb1list = []
        for i, code in enumerate(self.list_cad):
            name = self.GetMasterCodeName(code)
            cadb1list.append(name)
        cadbtext = ", ".join(cadb1list)
        self.windowQ.put([2, f"CAD 매수종목 : {cadbtext}"])
        if self.bool_sound:
            self.soundQ.put("전략카드 매수종목을 검색하였습니다.")
        else:
            self.windowQ.put([2, "CAD 매수 종목 추출 완료"])
        self.UpdateTrtime()

    def BuyCad(self):
        self.windowQ.put([4, "CAD 매수 실행"])
        delcbclist = []
        if len(self.list_cad) > 0:
            codelist = ";".join(self.list_cad)
            df = self.Block_Request("optkwfid", codelist, len(self.list_cad), output="관심종목정보", next=0)
            df = df.set_index('종목코드')
            for code in df.index:
                name = df['종목명'][code]
                c = abs(int(df['현재가'][code]))
                oc = int(round(self.int_dbat / len(self.list_cad) / c))
                if self.int_ysgm >= c * oc:
                    self.int_ysgm -= c * oc
                    if self.bool_cad and not self.bool_test:
                        self.Buy(code, "CAD", 0, oc, name)
                    if code in self.df_jg.index and code in self.df_cbc.index:
                        delcbclist.append(code)
                else:
                    self.windowQ.put([2, f"CAD 매수 조건 확인 FALSE [시드부족] {name}"])
        if len(delcbclist) > 0:
            for code in delcbclist:
                self.df_cbc.drop(index=code, inplace=True)
            self.queryQ.put(f"DELETE FROM casbuycount WHERE 종목코드 in ({delcbclist})")
        if self.bool_sound:
            self.soundQ.put("전략카드 추출종목을 매수주문하였습니다.")
        else:
            self.windowQ.put([1, "CAD 추출 종목 매수 주문 완료"])
        self.UpdateTrtime()

    def UpdateTrtime(self):
        if self.count_tr > self.int_trct:
            self.time_tran = self.start_tr + datetime.timedelta(seconds=+self.count_tr * (self.int_trot - self.int_sedt))
            remaintime = (self.time_tran - datetime.datetime.now()).total_seconds()
            if remaintime > 0:
                self.windowQ.put([1, f"TR 조회 재요청까지 남은 시간은 {round(remaintime, 2)}초입니다."])
            self.count_tr = 0
        else:
            pass

    def Buy(self, code, st, bc, oc, name):
        df = pd.DataFrame({'전략구분': [st], '매수횟수': [bc]}, index=[code])
        self.df_od = self.df_od.append(df)
        order = ["매수", "4989", self.str_acct, 1, code, oc, 0, "03", "", name, st]
        self.workerQ.put(order)

    def Sell(self, code, st, bc, oc, name):
        df = pd.DataFrame({'전략구분': [st], '매수횟수': [bc]}, index=[code])
        self.df_od = self.df_od.append(df)
        order = ["매도", "4989", self.str_acct, 2, code, oc, 0, "03", "", name, st]
        self.workerQ.put(order)

    def _h_login(self, err_code):
        if err_code == 0:
            self.bool_conn = True

    def _h_cond_load(self, ret, msg):
        if msg == "":
            return
        if ret == 1:
            self.bool_cdload = True

    def _h_cond_data(self, screen, code_list, cond_name, cond_index, nnext):
        if screen == "" and cond_name == "" and cond_index == "" and nnext == "":
            return
        codes = code_list.split(';')[:-1]
        self.list_trcddata = codes
        self.bool_trcdload = True

    def _h_tran_data(self, screen, rqname, trcode, record, nnext):
        if screen == "" and record == "":
            return
        self.windowQ.put([1, f"TR 조회 수신 알림 {rqname} {trcode}"])
        items = None
        if nnext == '2':
            self.bool_trremained = True
        else:
            self.bool_trremained = False
        for output in self.list_tritems['output']:
            record = list(output.keys())[0]
            items = list(output.values())[0]
            if record == self.list_trrecord:
                break
        rows = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        if rows == 0:
            rows = 1
        df2 = []
        for row in range(rows):
            row_data = []
            for item in items:
                data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, row, item)
                row_data.append(data.strip())
            df2.append(row_data)
        df = pd.DataFrame(data=df2, columns=items)
        self.df_trdata = df
        self.bool_received = True

    def _h_real_cond(self, code, IorD, cname, cindex):
        if cname == "":
            return
        self.int_ctcr += 1
        name = self.GetMasterCodeName(code)
        if IorD == "I":
            if cindex == "1" and code not in self.df_gs.index:
                self.df_gs = self.df_gs.append(pd.DataFrame({
                    '종목명': [name], 'HMP': [0], '현재가': [0], '등락율': [0], '거래대금': [0], '증감비율': [0],
                    '체결강도': [0], '종목코드': [code], '시가': [0], '고가': [0], '저가': [0], '전일종가': [0],
                    'HML': [0]}, index=[code]))
            elif cindex == "2" and code in self.df_gs.index:
                c = self.df_gs['현재가'][code]
                if c != 0:
                    self.CheckCasbuy('rc', code, name, "", c)
            elif cindex in ["7", "8"]:
                self.CheckBnfsell(code, name, cindex)
        elif IorD == "D":
            if cindex == "1" and code in self.df_gs.index:
                self.df_gs.drop(index=code, inplace=True)
                if code not in self.df_jg.index:
                    self.workerQ.put(["ALL", code])

    def CheckBnfsell(self, code, name, cindex):
        self.int_ctsc += 1
        if code not in self.df_od.index and code in self.df_jg.index and code in self.df_bbc.index:
            if cindex == "7":
                self.windowQ.put([2, f"BNF 매도 조건 확인 TTRUE [1차수익라인] {name}"])
            else:
                self.windowQ.put([2, f"BNF 매도 조건 확인 TTRUE [2차수익라인] {name}"])
            jc = self.df_jg['보유수량'][code]
            bc = self.df_bbc['매수횟수'][code]
            oc = int(round(jc / self.int_bdsp))
            if oc == 0:
                oc = 1
            if self.bool_bnf and not self.bool_test:
                self.Sell(code, "BNF", bc, oc, name)
        elif code in self.df_od.index and code in self.df_jg.index and code in self.df_bbc.index:
            self.windowQ.put([2, f"BNF 매도 조건 확인 FALSE [주문종목] {name}"])

    def _h_real_data(self, code, realtype, realdata):
        if realdata == "":
            return
        if realtype == "장시작시간":
            try:
                self.int_oper = int(self.GetCommRealData(code, 215))
                current = self.GetCommRealData(code, 20)
                remain = self.GetCommRealData(code, 214)
            except Exception as e:
                self.log.info(f"[{strtime()}] _h_real_data 장시작시간 {e}")
            else:
                if self.int_oper == 3:
                    self.CjTtTdInit()
                if self.bool_sound:
                    if current == "084000":
                        self.soundQ.put("장시작 20분 전입니다.")
                    elif current == "085000":
                        self.soundQ.put("장시작 10분 전입니다.")
                    elif current == "085500":
                        self.soundQ.put("장시작 5분 전입니다.")
                    elif current == "085900":
                        self.soundQ.put("장시작 1분 전입니다.")
                    elif current == "085930":
                        self.soundQ.put("장시작 30초 전입니다.")
                    elif current == "085950":
                        self.soundQ.put("장시작 10초 전입니다.")
                    elif current == "090000":
                        self.soundQ.put(f"{self.str_tday[:4]}년 {self.str_tday[4:6]}월 {self.str_tday[6:]}일 "
                                        "장이 시작되었습니다.")
                    elif current == "152000":
                        self.soundQ.put("장마감 10분 전입니다.")
                    elif current == "153000":
                        self.soundQ.put(f"{self.str_tday[:4]}년 {self.str_tday[4:6]}월 {self.str_tday[6:]}일 "
                                        "장이 종료되었습니다.")
                else:
                    self.windowQ.put([1, f"장운영시간 알림 {self.int_oper} {current[:2]}:{current[2:4]}:{current[4:]} "
                                         f"남은시간 {remain[:2]}:{remain[2:4]}:{remain[4:]}"])
        elif realtype == "업종지수":
            try:
                d = self.GetCommRealData(code, 20)
                c = abs(int(float(self.GetCommRealData(code, 10)) * 100))
            except Exception as e:
                self.log.info(f"[{strtime()}] _h_real_data 업종지수 {e}")
            else:
                if d not in ['장마감', '장종료']:
                    if code == "001":
                        self.chartQ.put(['코스피현재가', d, c])
                    elif code == "101":
                        self.chartQ.put(['코스닥현재가', d, c])
        elif realtype == "주식체결":
            self.int_ctjc += 1
            self.int_ctrjc += 1
            try:
                c = abs(int(self.GetCommRealData(code, 10)))  # current 현재가
                per = float(self.GetCommRealData(code, 12))   # 등락율 percent
                vp = abs(int(float(self.GetCommRealData(code, 30))))    # 전일거래량대비율 volume percent
                ch = int(float(self.GetCommRealData(code, 228)))    # 체결강도 chaegyeol height
                m = int(self.GetCommRealData(code, 14))     # 누적거래대금
                o = abs(int(self.GetCommRealData(code, 16)))    # 시가 open
                h = abs(int(self.GetCommRealData(code, 17)))    # 고가 high
                ll = abs(int(self.GetCommRealData(code, 18)))   # 저가 low
                prec = self.GetMasterLastPrice(code)    # 전일종가?          ===> 전일대비를 이용하면 될텐데 즉, c - 11
                v = int(self.GetCommRealData(code, 15)) # volume 거래량
                d = self.GetCommRealData(code, 20)  # 체결시간 datetime
                name = self.GetMasterCodeName(code)     # 종목명
            except Exception as e:
                self.log.info(f"[{strtime()}] _h_real_data 주식체결 {e}")
            else:
                self.UpdateJusicchegeolData(code, name, c, per, vp, ch, m, o, h, ll, prec, v, d)
        elif realtype == "주식호가잔량":
            self.int_cthj += 1
            self.int_ctrhj += 1
            try:
                vp = [
                    int(float(self.GetCommRealData(code, 139))),
                    int(self.GetCommRealData(code, 90)),
                    int(self.GetCommRealData(code, 89)),
                    int(self.GetCommRealData(code, 88)),
                    int(self.GetCommRealData(code, 87)),
                    int(self.GetCommRealData(code, 86)),
                    int(self.GetCommRealData(code, 85)),
                    int(self.GetCommRealData(code, 84)),
                    int(self.GetCommRealData(code, 83)),
                    int(self.GetCommRealData(code, 82)),
                    int(self.GetCommRealData(code, 81)),
                    int(self.GetCommRealData(code, 91)),
                    int(self.GetCommRealData(code, 92)),
                    int(self.GetCommRealData(code, 93)),
                    int(self.GetCommRealData(code, 94)),
                    int(self.GetCommRealData(code, 95)),
                    int(self.GetCommRealData(code, 96)),
                    int(self.GetCommRealData(code, 97)),
                    int(self.GetCommRealData(code, 98)),
                    int(self.GetCommRealData(code, 99)),
                    int(self.GetCommRealData(code, 100)),
                    int(float(self.GetCommRealData(code, 129)))
                ]
                jc = [
                    int(self.GetCommRealData(code, 121)),
                    int(self.GetCommRealData(code, 70)),
                    int(self.GetCommRealData(code, 69)),
                    int(self.GetCommRealData(code, 68)),
                    int(self.GetCommRealData(code, 67)),
                    int(self.GetCommRealData(code, 66)),
                    int(self.GetCommRealData(code, 65)),
                    int(self.GetCommRealData(code, 64)),
                    int(self.GetCommRealData(code, 63)),
                    int(self.GetCommRealData(code, 62)),
                    int(self.GetCommRealData(code, 61)),
                    int(self.GetCommRealData(code, 71)),
                    int(self.GetCommRealData(code, 72)),
                    int(self.GetCommRealData(code, 73)),
                    int(self.GetCommRealData(code, 74)),
                    int(self.GetCommRealData(code, 75)),
                    int(self.GetCommRealData(code, 76)),
                    int(self.GetCommRealData(code, 77)),
                    int(self.GetCommRealData(code, 78)),
                    int(self.GetCommRealData(code, 79)),
                    int(self.GetCommRealData(code, 80)),
                    int(self.GetCommRealData(code, 125))
                ]
                hg = [
                    self.GetSanghanga(code),
                    abs(int(self.GetCommRealData(code, 50))),
                    abs(int(self.GetCommRealData(code, 49))),
                    abs(int(self.GetCommRealData(code, 48))),
                    abs(int(self.GetCommRealData(code, 47))),
                    abs(int(self.GetCommRealData(code, 46))),
                    abs(int(self.GetCommRealData(code, 45))),
                    abs(int(self.GetCommRealData(code, 44))),
                    abs(int(self.GetCommRealData(code, 43))),
                    abs(int(self.GetCommRealData(code, 42))),
                    abs(int(self.GetCommRealData(code, 41))),
                    abs(int(self.GetCommRealData(code, 51))),
                    abs(int(self.GetCommRealData(code, 52))),
                    abs(int(self.GetCommRealData(code, 53))),
                    abs(int(self.GetCommRealData(code, 54))),
                    abs(int(self.GetCommRealData(code, 55))),
                    abs(int(self.GetCommRealData(code, 56))),
                    abs(int(self.GetCommRealData(code, 57))),
                    abs(int(self.GetCommRealData(code, 58))),
                    abs(int(self.GetCommRealData(code, 59))),
                    abs(int(self.GetCommRealData(code, 60))),
                    self.GetHahanga(code)
                ]
                prec = self.GetMasterLastPrice(code)
                per = [
                    round((hg[0] / prec - 1) * 100, 2),
                    round((hg[1] / prec - 1) * 100, 2),
                    round((hg[2] / prec - 1) * 100, 2),
                    round((hg[3] / prec - 1) * 100, 2),
                    round((hg[4] / prec - 1) * 100, 2),
                    round((hg[5] / prec - 1) * 100, 2),
                    round((hg[6] / prec - 1) * 100, 2),
                    round((hg[7] / prec - 1) * 100, 2),
                    round((hg[8] / prec - 1) * 100, 2),
                    round((hg[9] / prec - 1) * 100, 2),
                    round((hg[10] / prec - 1) * 100, 2),
                    round((hg[11] / prec - 1) * 100, 2),
                    round((hg[12] / prec - 1) * 100, 2),
                    round((hg[13] / prec - 1) * 100, 2),
                    round((hg[14] / prec - 1) * 100, 2),
                    round((hg[15] / prec - 1) * 100, 2),
                    round((hg[16] / prec - 1) * 100, 2),
                    round((hg[17] / prec - 1) * 100, 2),
                    round((hg[18] / prec - 1) * 100, 2),
                    round((hg[19] / prec - 1) * 100, 2),
                    round((hg[20] / prec - 1) * 100, 2),
                    round((hg[21] / prec - 1) * 100, 2)
                ]
            except Exception as e:
                self.log.info(f"[{strtime()}] _h_real_data 주식호가잔량 {e}")
            else:
                self.UpdateHogajanryangData(code, vp, jc, hg, per)

    def CjTtTdInit(self):
        self.df_cj = pd.DataFrame(
            columns=['종목명', '주문구분', '주문수량', '미체결수량', '주문가격', '체결가', '체결시간',
                     '종목코드'])
        self.df_tt = pd.DataFrame(
            columns=['거래횟수', '총매수금액', '총매도금액', '총수익금액', '총손실금액', '수익률', '수익금합계'])
        self.df_td = pd.DataFrame(
            columns=['종목명', '매수가', '매도가', '주문수량', '수익률', '수익금', '체결시간',
                     '종목코드', '매수금액', '매도금액', '전략구분'])
        self.windowQ.put(self.df_cj)
        self.windowQ.put(self.df_tt)
        self.windowQ.put(self.df_td)

    def UpdateJusicchegeolData(self, code, name, c, per, vp, ch, m, o, h, ll, prec, v, d):
        if code == self.hoga_code[0]:
            self.hogaQ.put(['left', v])
        if code == self.hoga_code[1]:
            self.hogaQ.put(['right', v])
        if code == self.chart_code[0]:
            self.chartQ.put(['left분봉일봉', d, c, v, m, ""])
        if code == self.chart_code[1]:
            self.chartQ.put(['left주봉월봉', "", c, v, "", ""])
        if code == self.chart_code[2]:
            self.chartQ.put(['right분봉일봉', d, c, v, m, ""])
        if code == self.chart_code[3]:
            self.chartQ.put(['right주봉월봉', "", c, v, "", ""])
        if code == self.chart_code[4]:
            self.chartQ.put(['center분봉일봉', d, c, v, m, ""])
        if code == self.chart_code[5]:
            self.chartQ.put(['chegeol분봉일봉', d, c, v, m, ""])
        if code in self.df_gs.index and self.df_gs['HML'][code] != 0:
            self.UpdateGoansim(code, name, m, ch, per, vp, c, o, h, ll, prec)
        if code in self.df_jg.index:
            self.UpdateJango(code, name, c, o, h, ll, prec)
            self.UpdateTotaljango()
        if datetime.datetime.now() > self.time_updf:
            self.df_gs.sort_values(by=['HMP'], ascending=False, inplace=True)
            self.df_jg.sort_values(by=['매입금액'], ascending=False, inplace=True)
            self.windowQ.put(self.df_gs)
            self.windowQ.put(self.df_jg)
            self.windowQ.put(self.df_tj)
            self.time_updf = datetime.datetime.now() + datetime.timedelta(seconds=+self.int_gjut)

    def UpdateGoansim(self, code, name, m, ch, per, vp, c, o, h, ll, prec):
        mpc = self.df_gs['현재가'][code]
        HML = self.df_gs['HML'][code]
        _HML = int(HML * self.int_hmlp / 100)
        timetominute = datetime.datetime.now().hour * 60 + datetime.datetime.now().minute
        if 539 < timetominute < 931:
            HMP = int(m / (_HML * (timetominute - 539) / 390) * 100)
        else:
            HMP = int(m / _HML * 100)
        if HMP >= 100 and ch >= 100:
            if code in self.df_gs.index:
                self.df_gs.at[code, ['HMP', '현재가', '등락율', '거래대금', '증감비율', '체결강도',
                                     '시가', '고가', '저가', '전일종가']] = \
                    HMP, c, per, m, vp, ch, o, h, ll, prec
                if code not in self.df_dbc.index and c > ll and per <= self.int_hper and \
                        h <= prec * (1 + (self.int_hper + abs(self.int_cpsp)) / 100):
                    self.CheckCasbuy('gs', code, name, mpc, c)
        else:
            if code in self.df_gs.index:
                self.df_gs.drop(index=code, inplace=True)
                if code not in self.df_jg.index:
                    self.workerQ.put(["ALL", code])

    def CheckCasbuy(self, gubun, code, name, mpc, c):
        if mpc == 0:
            return
        A = True
        if gubun == 'gs':
            BUY1 = self.df_hm['BUY1'][code]
            BUY2 = self.df_hm['BUY2'][code]
            BUY3 = self.df_hm['BUY3'][code]
            BUY4 = self.df_hm['BUY4'][code]
            BUY5 = self.df_hm['BUY5'][code]
            BUY6 = self.df_hm['BUY6'][code]
            BUY7 = self.df_hm['BUY7'][code]
            A = mpc > BUY1 >= c or mpc > BUY2 >= c or mpc > BUY3 >= c or \
                mpc > BUY4 >= c or mpc > BUY5 >= c or mpc > BUY6 >= c or mpc > BUY7 >= c
        elif gubun == 'jg':
            BUY1 = self.df_cbc['BUY1'][code]
            BUY2 = self.df_cbc['BUY2'][code]
            BUY3 = self.df_cbc['BUY3'][code]
            BUY4 = self.df_cbc['BUY4'][code]
            BUY5 = self.df_cbc['BUY5'][code]
            BUY6 = self.df_cbc['BUY6'][code]
            BUY7 = self.df_cbc['BUY7'][code]
            A = mpc > BUY1 >= c or mpc > BUY2 >= c or mpc > BUY3 >= c or \
                mpc > BUY4 >= c or mpc > BUY5 >= c or mpc > BUY6 >= c or mpc > BUY7 >= c
        elif gubun == 'rc':
            A = True
        if not A:
            return
        B = (code in self.list_kosd and self.bool_kdcs) or (code not in self.list_kosd and self.bool_kpcs)
        if len(name) > 5:
            name_ = name[:5]
        else:
            name_ = name
        self.int_ctsc += 1
        if gubun == 'jg' or not self.bool_jstd or \
                (self.bool_jstd and gubun in ['gs', 'rc'] and (B or (not B and name_ in self.ThemaJudoju))):
            if gubun in ['gs', 'rc']:
                if self.bool_atbj:
                    oc = self.GetCasordercount(code)
                else:
                    oc = int(self.int_cbat / c)
            else:
                oc = self.df_jg['보유수량'][code]
            if code not in self.df_od.index:
                if code not in self.df_cbc.index:
                    if self.bool_jstd and gubun in ['gs', 'rc'] and not B and name_ in self.ThemaJudoju:
                        self.windowQ.put([2, f"CAS 매수 조건 확인 TTRUE [테마매수] {name}"])
                    elif gubun == 'gs':
                        self.windowQ.put([2, f"CAS 매수 조건 확인 TTRUE [신규매수] {name}"])
                    elif gubun == 'rc':
                        self.windowQ.put([2, f"CAS 매수 조건 확인 TTRUE [눌림매수] {name}"])
                    if self.int_ysgm >= c * oc and self.bool_cas and not self.bool_test:
                        self.Buy(code, "CAS", 0, oc, name)
                    elif self.int_ysgm < c * oc:
                        self.windowQ.put([2, f"CAS 매수 조건 확인 FALSE [시드부족] {name}"])
                        self.UpdateBuycount("매수", 0, code, "CAS", name)
                else:
                    bc = self.df_cbc['매수횟수'][code]
                    if (code not in self.df_jg.index and bc != 0) or \
                            (code in self.df_jg.index and c < self.df_jg['매입가'][code] * (1 + self.int_cpsp / 100)):
                        if self.int_ysgm >= c * oc and self.bool_cas and not self.bool_test:
                            self.windowQ.put([2, f"CAS 매수 조건 확인 TTRUE [추가매수] {name}"])
                            self.Buy(code, "CAS", bc, oc, name)
                        elif self.int_ysgm < c * oc:
                            self.windowQ.put([2, f"CAS 매수 조건 확인 FALSE [시드부족] {name}"])
                            self.UpdateBuycount("매수", bc, code, "CAS", name)
                    else:
                        if code not in self.df_jg.index and bc == 0:
                            self.windowQ.put([2, f"CAS 매수 조건 확인 FALSE [청산종목] {name}"])
                        if code in self.df_jg.index and c >= self.df_jg['매입가'][code] * (1 + self.int_cpsp / 100):
                            self.windowQ.put([2, f"CAS 매수 조건 확인 FALSE [매입가격] {name}"])
            else:
                self.windowQ.put([2, f"CAS 매수 조건 확인 FALSE [주문종목] {name}"])
        else:
            if code in self.list_kosd and not self.bool_kdcs:
                self.windowQ.put([2, f"CAS 매수 조건 확인 FALSE [지수하락] {name}"])
            if code not in self.list_kosd and not self.bool_kpcs:
                self.windowQ.put([2, f"CAS 매수 조건 확인 FALSE [지수하락] {name}"])

    def GetCasordercount(self, code):
        c = self.df_gs['현재가'][code]
        hmp = self.df_gs['HMP'][code]
        vp = self.df_gs['증감비율'][code]
        df = self.df_gs[self.df_gs['HMP'] != 0]
        avg_hmp = df['HMP'].mean()
        avg_vp = df['증감비율'].mean()
        count = int(self.int_cbat * (hmp / avg_hmp) * (vp / avg_vp) / c)
        if count * c > self.df_tj['추정예탁자산'][0] / self.int_mcbp:
            count = int(self.df_tj['추정예탁자산'][0] / self.int_mcbp / c)
        if count * c > self.int_ysgm > self.int_cbat:
            count = int(self.int_cbat / c)
        if count == 0:
            count = 1
        return count

    def UpdateJango(self, code, name, c, o, h, ll, prec):
        mpc = self.df_jg['현재가'][code]
        bp = self.df_jg['매입가'][code]
        bg = self.df_jg['매입금액'][code]
        jc = self.df_jg['보유수량'][code]
        phsp = self.df_jg['최고수익률'][code]
        plsp = self.df_jg['최저수익률'][code]
        sssr = 1 - (self.int_stax / 1000 + self.int_fees / 100) / 100
        bssr = 1 - self.int_btax / 1000 / 100
        sp = round((c * jc * sssr / (bp * jc * bssr) - 1) * 100, 2)
        if sp > phsp:
            hsp = sp
        else:
            hsp = phsp
        if sp < plsp:
            lsp = sp
        else:
            lsp = plsp
        sg = int(bg * sp / 100)
        fg = bg + sg
        self.df_jg.at[code, :] = name, bp, c, sp, sg, bg, fg, code, o, h, ll, prec, jc, hsp, lsp
        if sp < 0 and code not in self.df_gs.index and code in self.df_cbc.index:
            self.CheckCasbuy('jg', code, name, mpc, c)
        if code in self.df_cbc.index and code not in self.df_od.index:
            self.CheckCasSell(code, name, c, phsp, hsp, lsp, sp)
        if code in self.df_dbc.index and code not in self.df_od.index:
            self.CheckCadSell(code, name, sp, phsp, hsp)

    def CheckCasSell(self, code, name, c, phsp, hsp, lsp, sp):
        if phsp < self.int_dper <= hsp or phsp < self.int_dper * 2 <= hsp or phsp < self.int_dper * 3 <= hsp or \
                phsp < self.int_dper * 4 <= hsp or phsp < self.int_dper * 5 <= hsp or \
                phsp < self.int_dper * 6 <= hsp or phsp < self.int_dper * 7 <= hsp or \
                phsp < self.int_dper * 8 <= hsp or phsp < self.int_dper * 9 <= hsp or \
                phsp < self.int_dper * 10 <= hsp or phsp < self.int_dper * 12 <= hsp or \
                phsp < self.int_dper * 14 <= hsp or phsp < self.int_dper * 16 <= hsp or \
                phsp < self.int_dper * 18 <= hsp or phsp < self.int_dper * 20 <= hsp:
            bc = self.df_cbc['매수횟수'][code]
            bg = self.df_jg['매입금액'][code]
            jc = self.df_jg['보유수량'][code]
            if bg > self.int_sbgm * 1000:
                oc = int(jc / self.int_cdsp)
            else:
                oc = jc
            if oc == 0:
                oc = 1
            self.windowQ.put([2, f"CAS 매도 조건 확인 TTRUE [수익라인] {name}"])
            if self.bool_cas and not self.bool_test:
                self.Sell(code, "CAS", bc, oc, name)
        if c < self.df_cbc['SELL'][code] or (sp < 0 and hsp > self.int_dper) or (sp > 0 and lsp < self.int_cslp):
            bc = self.df_cbc['매수횟수'][code]
            jc = self.df_jg['보유수량'][code]
            self.windowQ.put([2, f"CAS 매도 조건 확인 TTRUE [청산라인] {name}"])
            if self.bool_cas and not self.bool_test:
                self.Sell(code, "CAS", bc, jc, name)

    def CheckCadSell(self, code, name, sp, phsp, hsp):
        if phsp < self.int_dper <= hsp or phsp < self.int_dper * 2 <= hsp or phsp < self.int_dper * 3 <= hsp or \
                phsp < self.int_dper * 4 <= hsp or phsp < self.int_dper * 5 <= hsp or \
                phsp < self.int_dper * 6 <= hsp or phsp < self.int_dper * 7 <= hsp or \
                phsp < self.int_dper * 8 <= hsp or phsp < self.int_dper * 9 <= hsp or \
                phsp < self.int_dper * 10 <= hsp or phsp < self.int_dper * 12 <= hsp or \
                phsp < self.int_dper * 14 <= hsp or phsp < self.int_dper * 16 <= hsp or \
                phsp < self.int_dper * 18 <= hsp or phsp < self.int_dper * 20 <= hsp:
            bg = self.df_jg['매입금액'][code]
            jc = self.df_jg['보유수량'][code]
            if bg > self.int_sbgm * 1000:
                oc = int(jc / self.int_cdsp)
            else:
                oc = jc
            if oc == 0:
                oc = 1
            self.windowQ.put([2, f"CAD 매도 조건 확인 TTRUE [수익라인] {name}"])
            if self.bool_cad and not self.bool_test:
                self.Sell(code, "CAD", 0, oc, name)
        if sp < self.int_cbsp or (sp < 0 and hsp > self.int_dper):
            jc = self.df_jg['보유수량'][code]
            self.windowQ.put([2, f"CAD 매도 조건 확인 TTRUE [청산라인] {name}"])
            if self.bool_cad and not self.bool_test:
                self.Sell(code, "CAD", 0, jc, name)

    @Thread_Decorator
    def UpdateHogajanryangData(self, code, vp, jc, hg, per):
        for i in range(len(per)):
            if 0 < i < 21 and per[i] == -100:
                per[i] = 0
        if code == self.hoga_code[0]:
            self.hogaQ.put('left미체결수량')
            self.hogaQ.put(['left', vp, jc, hg, per])
            self.hogaQ.put('left미체결수량업데이트')
            if code in self.df_jg.index:
                self.df_hj_left = self.df_jg[self.df_jg['종목코드'] == code]
                self.windowQ.put(self.df_hj_left.rename(columns={'종목명': 'left호가종목명'}))
            elif code in self.df_gs.index:
                self.df_hj_left = self.df_gs[self.df_gs['종목코드'] == code]
                self.windowQ.put(self.df_hj_left.rename(columns={'종목명': 'left호가종목명'}))
        elif code == self.hoga_code[1]:
            self.hogaQ.put('right미체결수량')
            self.hogaQ.put(['right', vp, jc, hg, per])
            self.hogaQ.put('right미체결수량업데이트')
            if code in self.df_jg.index:
                self.df_hj_right = self.df_jg[self.df_jg['종목코드'] == code]
                self.windowQ.put(self.df_hj_right.rename(columns={'종목명': 'right호가종목명'}))
            elif code in self.df_gs.index:
                self.df_hj_right = self.df_gs[self.df_gs['종목코드'] == code]
                self.windowQ.put(self.df_hj_right.rename(columns={'종목명': 'right호가종목명'}))

    def _h_cjan_data(self, gubun, itemcnt, fidlist):
        if gubun != "0" and itemcnt != "" and fidlist != "":
            return
        on = self.GetChejanData(9203)
        if on == "":
            return
        self.int_ctcj += 1
        code = self.GetChejanData(9001).strip('A')
        name = self.GetChejanData(302).strip(" ").strip("'")
        og = self.GetChejanData(905)[1:]
        ot = self.GetChejanData(913)
        oc = int(self.GetChejanData(900))
        omc = int(self.GetChejanData(902))
        d = int(self.str_tday + self.GetChejanData(908))
        op = int(self.GetChejanData(901))
        oon = self.GetChejanData(904)
        try:
            cp = int(self.GetChejanData(910))
        except ValueError:
            cp = 0
        self.UpdateChejanData(code, name, on, og, ot, oc, omc, d, op, cp, oon)

    def UpdateChejanData(self, code, name, on, og, ot, oc, omc, d, op, cp, oon):
        if ot == "접수":
            if og == "매수취소" and code in self.df_od.index:
                oc = self.df_cj['주문수량'][oon] - oc
                if oc > 0:
                    st = self.df_od['전략구분'][code]
                    bc = self.df_od['매수횟수'][code]
                    cp = self.df_cj['체결가'][oon]
                    og = "매수"
                    self.int_ysgm -= cp * oc
                    self.windowQ.put([2, f"{name} {oc}주 매수 완료"])
                    if name not in self.list_buy:
                        self.list_buy.append(name)
                    self.BuyUpdate(code, name, og, oc, cp, bc, st)
                if code in self.df_od.index:
                    self.df_od.drop(index=code, inplace=True)
            elif og == "매도취소" and code in self.df_od.index:
                oc = self.df_cj['주문수량'][oon] - oc
                if oc > 0:
                    st = self.df_od['전략구분'][code]
                    bc = self.df_od['매수횟수'][code]
                    bp = self.df_jg['매입가'][code]
                    cp = self.df_cj['체결가'][oon]
                    on = oon
                    og = "매도"
                    sssr = 1 - (self.int_stax / 1000 + self.int_fees / 100) / 100
                    bssr = 1 - self.int_btax / 1000 / 100
                    sp = round((cp * oc * sssr / (bp * oc * bssr) - 1) * 100, 2)
                    sg = int(bp * oc * sp / 100)
                    self.int_ysgm += bp * oc + sg
                    self.windowQ.put([2, f"{name} {oc}주 매도 수익률{sp}% 수익금{format(sg, ',')}원"])
                    if name not in self.list_sell:
                        self.list_sell.append(name)
                    self.SellUpdate(code, name, og, oc, bp, cp, bc, sp, sg, st, on)
                if code in self.df_od.index:
                    self.df_od.drop(index=code, inplace=True)
        elif ot == "체결" and omc == 0 and code in self.df_od.index:
            st = self.df_od['전략구분'][code]
            bc = self.df_od['매수횟수'][code]
            if og == "매수":
                self.int_ysgm -= cp * oc
                self.windowQ.put([2, f"{name} {oc}주 매수 완료"])
                if name not in self.list_buy:
                    self.list_buy.append(name)
                self.BuyUpdate(code, name, og, oc, cp, bc, st)
            elif og == "매도":
                bp = self.df_jg['매입가'][code]
                sssr = 1 - (self.int_stax / 1000 + self.int_fees / 100) / 100
                bssr = 1 - self.int_btax / 1000 / 100
                sp = round((cp * oc * sssr / (bp * oc * bssr) - 1) * 100, 2)
                sg = int(bp * oc * sp / 100)
                self.int_ysgm += bp * oc + sg
                self.windowQ.put([2, f"{name} {oc}주 매도 수익률{sp}% 수익금{format(sg, ',')}원"])
                if name not in self.list_sell:
                    self.list_sell.append(name)
                self.SellUpdate(code, name, og, oc, bp, cp, bc, sp, sg, st, on)
            if code in self.df_od.index:
                self.df_od.drop(index=code, inplace=True)
        self.UpdateChejeollist(on, code, name, og, oc, omc, op, cp, d)
        if code == self.hoga_code[0] and self.bool_hgup:
            self.hogaQ.put(['left', og, omc, op])
        if code == self.hoga_code[1] and self.bool_hgup:
            self.hogaQ.put(['right', og, omc, op])

    @Thread_Decorator
    def UpdateChejeollist(self, on, code, name, og, oc, omc, op, cp, d):
        df = pd.DataFrame({'종목명': [name], '주문구분': [og], '주문수량': [oc], '미체결수량': [omc], '주문가격': [op],
                           '체결가': [cp], '체결시간': [d], '종목코드': [code], '주문번호': [on]})
        df = df.set_index('주문번호')
        if on in self.df_cj.index:
            self.df_cj.at[on, :] = name, og, oc, omc, op, cp, d, code
        else:
            self.df_cj = self.df_cj.append(df)
        self.df_cj.sort_values(by=['체결시간'], ascending=False, inplace=True)
        self.windowQ.put(self.df_cj)
        if omc == 0:
            self.queryQ.put([df, "chegeollist", "append"])

    @Thread_Decorator
    def BuyUpdate(self, code, name, og, oc, cp, bc, st):
        self.UpdateChegeoljango(og, code, name, oc, cp)
        self.UpdateBuycount(og, bc, code, st, name)
        self.UpdateTotaljango()

    @Thread_Decorator
    def SellUpdate(self, code, name, og, oc, bp, cp, bc, sp, sg, st, on):
        self.UpdateChegeoljango(og, code, name, oc, cp)
        if st == 'BNF' or (st in ["CAS", "수동"] and code not in self.df_jg.index):
            self.UpdateBuycount(og, bc, code, st, name)
        self.UpdateTotaljango()
        self.UpdateTradelist(code, name, bp, cp, oc, sp, sg, st, on)

    def UpdateChegeoljango(self, og, code, name, oc, cp):
        if og == "매수":
            if code not in self.df_jg.index:
                bg = oc * cp
                sssr = 1 - (self.int_stax / 1000 + self.int_fees / 100) / 100
                bssr = 1 - self.int_btax / 1000 / 100
                sp = round((bg * sssr / (bg * bssr) - 1) * 100, 2)
                sg = int(bg * sp / 100)
                fg = bg + sg
                self.df_jg = self.df_jg.append(pd.DataFrame({
                    '종목명': [name], '매입가': [cp], '현재가': [cp], '수익률': [sp], '평가손익': [sg], '매입금액': [bg],
                    '평가금액': [fg], '종목코드': [code], '시가': [0], '고가': [0], '저가': [0], '전일종가': [0],
                    '보유수량': [oc], '최고수익률': [0], '최저수익률': [0]}, index=[code]))
                if code not in self.df_gs.index:
                    self.workerQ.put([screen_jgjc, code, "10;12;14;30;228", 1])
            else:
                o = self.df_jg['시가'][code]
                h = self.df_jg['고가'][code]
                ll = self.df_jg['저가'][code]
                pc = self.df_jg['전일종가'][code]
                jc = self.df_jg['보유수량'][code]
                bg = self.df_jg['매입금액'][code]
                hsp = self.df_jg['최고수익률'][code]
                lsp = self.df_jg['최저수익률'][code]
                jc = jc + oc
                bg = bg + oc * cp
                bp = int(bg / jc)
                sssr = 1 - (self.int_stax / 1000 + self.int_fees / 100) / 100
                bssr = 1 - self.int_btax / 1000 / 100
                sp = round((cp * jc * sssr / (bp * jc * bssr) - 1) * 100, 2)
                sg = int(bg * sp / 100)
                fg = bg + sg
                self.df_jg.at[code, :] = name, bp, cp, sp, sg, bg, fg, code, o, h, ll, pc, jc, hsp, lsp
            if self.bool_sound:
                self.soundQ.put(f"{name} {oc}주를 매수하였습니다")
        elif og == "매도":
            bp = self.df_jg['매입가'][code]
            sssr = 1 - (self.int_stax / 1000 + self.int_fees / 100) / 100
            bssr = 1 - self.int_btax / 1000 / 100
            sp = round((cp * oc * sssr / (bp * oc * bssr) - 1) * 100, 2)
            sg = int(bp * oc * sp / 100)
            jc = self.df_jg['보유수량'][code]
            if jc - oc == 0:
                self.df_jg.drop(index=code, inplace=True)
                if code not in self.df_gs.index:
                    self.workerQ.put(["ALL", code])
            else:
                o = self.df_jg['시가'][code]
                h = self.df_jg['고가'][code]
                ll = self.df_jg['저가'][code]
                pc = self.df_jg['전일종가'][code]
                hsp = self.df_jg['최고수익률'][code]
                lsp = self.df_jg['최저수익률'][code]
                jc = jc - oc
                bg = jc * bp
                fg = jc * cp
                self.df_jg.at[code, :] = name, bp, cp, sp, sg, bg, fg, code, o, h, ll, pc, jc, hsp, lsp
            if self.bool_sound:
                self.soundQ.put(f"{name} {oc}주를 매도하였습니다")
        self.df_jg.sort_values(by=['매입금액'], ascending=False, inplace=True)
        self.windowQ.put(self.df_jg)

    @Thread_Decorator
    def UpdateBuycount(self, og, bc, code, st, name):
        if og == "매수":
            if st in ["CAS", "수동"]:
                if code in self.df_hm.index:
                    SELL = self.df_hm['SELL'][code]
                    BUY1 = self.df_hm['BUY1'][code]
                    BUY2 = self.df_hm['BUY2'][code]
                    BUY3 = self.df_hm['BUY3'][code]
                    BUY4 = self.df_hm['BUY4'][code]
                    BUY5 = self.df_hm['BUY5'][code]
                    BUY6 = self.df_hm['BUY6'][code]
                    BUY7 = self.df_hm['BUY7'][code]
                else:
                    SELL = self.df_cbc['SELL'][code]
                    BUY1 = self.df_cbc['BUY1'][code]
                    BUY2 = self.df_cbc['BUY2'][code]
                    BUY3 = self.df_cbc['BUY3'][code]
                    BUY4 = self.df_cbc['BUY4'][code]
                    BUY5 = self.df_cbc['BUY5'][code]
                    BUY6 = self.df_cbc['BUY6'][code]
                    BUY7 = self.df_cbc['BUY7'][code]
                d = str(datetime.datetime.now())
                bc += 1
                df = pd.DataFrame({'종목명': [name], '매수횟수': [bc], '체결시간': [d], 'SELL': [SELL],
                                   'BUY1': [BUY1], 'BUY2': [BUY2], 'BUY3': [BUY3], 'BUY4': [BUY4],
                                   'BUY5': [BUY5], 'BUY6': [BUY6], 'BUY7': [BUY7], '종목코드': [code]})
                df = df.set_index('종목코드')
                if bc == 1:
                    self.df_cbc = self.df_cbc.append(df)
                    self.queryQ.put([df, "casbuycount", "append"])
                else:
                    self.df_cbc.at[code, '매수횟수'] = bc
                    self.queryQ.put(f"UPDATE casbuycount SET 매수횟수 = {bc} WHERE 종목코드 = '{code}'")
            elif st == "CAD":
                d = str(datetime.datetime.now())
                df = pd.DataFrame({'종목명': [name], '매수횟수': [0], '체결시간': [d], '종목코드': [code]})
                df = df.set_index('종목코드')
                self.df_dbc = self.df_dbc.append(df)
                self.queryQ.put([df, "cadbuycount", "append"])
            elif st == "BNF":
                d = str(datetime.datetime.now())
                bc += 1
                df = pd.DataFrame({'종목명': [name], '매수횟수': [bc], '체결시간': [d], '종목코드': [code]})
                df = df.set_index('종목코드')
                if bc == 1:
                    self.df_bbc = self.df_bbc.append(df)
                    self.queryQ.put([df, "bnfbuycount", "append"])
                else:
                    self.df_bbc.at[code, '매수횟수'] = bc
                    self.queryQ.put(f"UPDATE bnfbuycount SET 매수횟수 = 2 WHERE 종목코드 = '{code}'")
        elif og == "매도":
            if st in ["CAS", "수동"]:
                self.df_cbc.at[code, '매수횟수'] = 0
                self.queryQ.put(f"UPDATE casbuycount SET 매수횟수 = 0 WHERE 종목코드 = '{code}'")
            elif st == "BNF":
                if bc == 1:
                    self.df_bbc.drop(index=code, inplace=True)
                    self.queryQ.put(f"DELETE FROM bnfbuycount WHERE 종목코드 = '{code}'")
                elif bc == 2:
                    self.df_bbc.at[code, '매수횟수'] = 1
                    self.queryQ.put(f"UPDATE bnfbuycount SET 매수횟수 = 1 WHERE 종목코드 = '{code}'")

    def UpdateTotaljango(self):
        if len(self.df_jg) > 0:
            tbsg = self.df_jg['평가손익'].sum()
            tbg = self.df_jg['매입금액'].sum()
            tpg = self.df_jg['평가금액'].sum()
            asp = round(self.df_jg['수익률'].mean(), 2)
            tsp = round((tpg / tbg - 1) * 100, 2)
            ttg = self.int_ysgm + tpg
            self.df_tj = pd.DataFrame({
                '추정예탁자산': [ttg], '추정예수금': [self.int_ysgm], '수익률평균': [asp], '총수익률': [tsp],
                '총평가손익': [tbsg], '총매입금액': [tbg], '총평가금액': [tpg]}, index=[0])
        else:
            self.df_tj = pd.DataFrame({
                '추정예탁자산': [self.int_ysgm], '추정예수금': [self.int_ysgm], '수익률평균': [0.00], '총수익률': [0.00],
                '총평가손익': [0], '총매입금액': [0], '총평가금액': [0]}, index=[0])

    def UpdateTradelist(self, code, name, bp, cp, oc, sp, sg, st, on):
        d = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        df = pd.DataFrame({'종목명': [name], '매수가': [bp], '매도가': [cp], '주문수량': [oc], '수익률': [sp],
                           '수익금': [sg], '체결시간': [d], '종목코드': [code], '매수금액': [bp * oc],
                           '매도금액': [cp * oc], '전략구분': [st], '주문번호': [on]})
        df = df.set_index('주문번호')
        self.df_td = self.df_td.append(df)
        self.df_td.sort_values(by=['체결시간'], ascending=False, inplace=True)
        self.windowQ.put(self.df_td)
        self.queryQ.put([df, "tradelist", "append"])
        self.TelegramMsg(f"{name} {oc}주 매도 수익률{sp}% 수익금{format(sg, ',')}원")
        self.UpdateTotaltradelist()

    def UpdateTotaltradelist(self):
        tbg = self.df_td['매수금액'].sum()
        tsg = self.df_td['매도금액'].sum()
        sssr = 1 - (self.int_stax / 1000 + self.int_fees / 100) / 100
        bssr = 1 - self.int_btax / 1000 / 100
        sp = round((tsg * sssr / (tbg * bssr) - 1) * 100, 2)
        df = self.df_td[self.df_td['수익금'] > 0]
        tsig = df['수익금'].sum()
        df = self.df_td[self.df_td['수익금'] < 0]
        tssg = df['수익금'].sum()
        sg = self.df_td['수익금'].sum()
        self.df_tt = pd.DataFrame({
            '거래횟수': [len(self.df_td)], '총매수금액': [tbg], '총매도금액': [tsg], '총수익금액': [tsig],
            '총손실금액': [tssg], '수익률': [sp], '수익금합계': [sg], '일자': [self.str_tday]})
        self.df_tt = self.df_tt.set_index('일자')
        self.windowQ.put(self.df_tt)
        self.TelegramMsg(
            f"거래횟수 {len(self.df_td)}회 / 총매수금액 {format(tbg, ',')}원 / 총매도금액 {format(tsg, ',')}원 / "
            f"총수익금액 {format(tsig, ',')}원 / 총손실금액 {format(tssg, ',')}원 / 수익률 {sp}% / "
            f"수익금합계 {format(sg, ',')}원")

    def Block_Request(self, *args, **kwargs):
        if self.count_tr == 0:
            self.start_tr = datetime.datetime.now()
        trcode = args[0].lower()
        liness = read_enc(trcode)
        self.list_tritems = parse_dat(trcode, liness)
        self.list_trrecord = kwargs["output"]
        nnext = kwargs["next"]
        for i in kwargs:
            if i.lower() != "output" and i.lower() != "next":
                self.ocx.dynamicCall("SetInputValue(QString, QString)", i, kwargs[i])
        self.bool_received = False
        self.bool_trremained = False
        if trcode == "optkwfid":
            codelist = args[1]
            ccount = args[2]
            self.ocx.dynamicCall("CommKwRqData(QString, bool, int, int, QString, QString)",
                                 codelist, 0, ccount, "0", self.list_trrecord, str(screen_brrq))
        else:
            self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)",
                                 self.list_trrecord, trcode, nnext, str(screen_brrq))
        sleeptime = datetime.datetime.now() + datetime.timedelta(seconds=+self.int_sedt)
        while not self.bool_received or datetime.datetime.now() < sleeptime:
            pythoncom.PumpWaitingMessages()
            time.sleep(self.int_elst)
        self.int_cttr += 1
        self.count_tr += 1
        return self.df_trdata

    def SendCondition(self, screen, cond_name, cond_index, search):
        if self.count_tr == 0:
            self.start_tr = datetime.datetime.now()
        self.bool_trcdload = False
        self.ocx.dynamicCall("SendCondition(QString, QString, int, int)", screen, cond_name, cond_index, search)
        sleeptime = datetime.datetime.now() + datetime.timedelta(seconds=+self.int_sedt)
        while not self.bool_trcdload or datetime.datetime.now() < sleeptime:
            pythoncom.PumpWaitingMessages()
            time.sleep(self.int_elst)
        self.int_cttr += 1
        self.count_tr += 1
        return self.list_trcddata

    def GetChejanData(self, fid):
        return self.ocx.dynamicCall("GetChejanData(int)", fid)

    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return data

    def GetCodeListByMarket(self, market):
        data = self.ocx.dynamicCall("GetCodeListByMarket(QString)", market)
        tokens = data.split(';')[:-1]
        return tokens

    def GetMasterLastPrice(self, code):
        data = self.ocx.dynamicCall("GetMasterLastPrice(QString)", code)
        return int(data)

    def GetMasterCodeName(self, code):
        return self.ocx.dynamicCall("GetMasterCodeName(QString)", code)

    def TelegramMsg(self, msg):
        if self.str_bot != "":
            bot = telegram.Bot(self.str_bot)
            bot.sendMessage(chat_id=self.int_id, text=msg)
        else:
            self.windowQ.put([1, "텔레그램 봇이 설정되지 않아 메세지를 보낼 수 없습니다."])

    @property
    def TrtimeCondition(self):
        return datetime.datetime.now() > self.time_tran

    @property
    def RemainedTrtime(self):
        return round((self.time_tran - datetime.datetime.now()).total_seconds(), 2)

    def GetSanghanga(self, code):
        predayclose = self.GetMasterLastPrice(code)
        kosdaq = code in self.list_kosd
        uplimitprice = int(predayclose * 1.30)
        if uplimitprice < 1000:
            x = 1
        elif 1000 <= uplimitprice < 5000:
            x = 5
        elif 5000 <= uplimitprice < 10000:
            x = 10
        elif 10000 <= uplimitprice < 50000:
            x = 50
        elif kosdaq:
            x = 100
        elif 50000 <= uplimitprice < 100000:
            x = 100
        elif 100000 <= uplimitprice < 500000:
            x = 500
        else:
            x = 1000
        return uplimitprice - uplimitprice % x

    def GetHahanga(self, code):
        predayclose = self.GetMasterLastPrice(code)
        kosdaq = code in self.list_kosd
        downlimitprice = int(predayclose * 0.70)
        if downlimitprice < 1000:
            x = 1
        elif 1000 <= downlimitprice < 5000:
            x = 5
        elif 5000 <= downlimitprice < 10000:
            x = 10
        elif 10000 <= downlimitprice < 50000:
            x = 50
        elif kosdaq:
            x = 100
        elif 50000 <= downlimitprice < 100000:
            x = 100
        elif 100000 <= downlimitprice < 500000:
            x = 500
        else:
            x = 1000
        return downlimitprice + (x - downlimitprice % x)

    def DownloadData(self):
        if self.bool_sound:
            self.soundQ.put("데이터다운로드를 시작합니다.")
        self.windowQ.put([4, "데이터 다운로드"])
        self.windowQ.put([2, "일봉 데이터 다운로드 및 업데이트 시작"])
        self.TelegramMsg("일봉 데이터 다운로드 및 업데이트 시작")
        start = datetime.datetime.now()
        con = sqlite3.connect(self.db_day)
        dblist = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        downlist = self.SendCondition(str(screen_csrc), self.df_cdb['조건명'][0], 0, 0)
        count = 0
        lastday = self.str_tday
        for i, code in enumerate(downlist):
            name = self.GetMasterCodeName(code)
            self.windowQ.put([2, f"다운로드 중 {i + 1}/{len(downlist)} [{code}]{name}"])
            dblastday = ""
            if code in dblist['name'].values:
                df = pd.read_sql(f"SELECT 일자 FROM '{code}' ORDER BY 일자 DESC LIMIT 1", con)
                dblastday = df['일자'][0]
                if dblastday == lastday:
                    continue
            df2 = []
            df3 = self.Block_Request("opt10081", 종목코드=code, 기준일자=self.str_tday, 수정주가구분=1,
                                     output="주식일봉차트조회", next=0)
            count += 1
            df2.append(df3)
            while self.bool_trremained and dblastday == "":
                df3 = self.Block_Request("opt10081", 종목코드=code, 기준일자=self.str_tday, 수정주가구분=1,
                                         output="주식일봉차트조회", next=2)
                count += 1
                df2.append(df3)
            df2 = pd.concat(df2)
            df2 = df2.set_index('일자')
            if lastday != df2.index[0]:
                lastday = df2.index[0]
            df2 = df2[::-1]
            self.downQ.put([df2, i + 1, len(downlist), code, name, dblastday])
            if count > self.int_trct:
                self.windowQ.put([2, f"다음 다운로드까지 남은 시간은"
                                     f" [{round(count * (self.int_trot - self.int_sedt), 2)}]초입니다."])
                time.sleep(count * (self.int_trot - self.int_sedt))
                count = 0
        con.close()
        time.sleep(10)
        zip_file = zipfile.ZipFile(f"{self.db_bac}db_{self.str_tday}.zip", "w", compression=zipfile.ZIP_DEFLATED)
        zip_file.write(self.db_day)
        zip_file.write(self.db_etc)
        zip_file.close()
        last_time = int((datetime.datetime.now() + datetime.timedelta(days=-30)).strftime("%Y%m%d"))
        flist = os.listdir(self.db_bac)
        list_backup = [x for x in flist if x.endswith('.zip')]
        list_remove = [file for file in list_backup if int(file[3:11]) < last_time]
        for file in list_remove:
            os.remove(f"{self.db_bac}{file}")
        end = datetime.datetime.now()
        self.windowQ.put([2, "데이터 백업 및 오래된 데이터 삭제 완료"])
        self.windowQ.put([2, f"일봉 데이터 다운로드 및 업데이트 완료 / 소요시간 {end - start}"])
        self.TelegramMsg(f"일봉 데이터 다운로드 및 업데이트 완료 / 소요시간 {end - start}")
        if self.bool_sound:
            self.soundQ.put("데이터다운로드가 완료되었습니다.")

    def UpdateInfo(self):
        float_memory = float2str3p2(self.float_memory)
        float_cpuper = float2str2p2(self.float_cpuper)
        info = [3, float_memory, self.int_threads, float_cpuper, len(self.df_gs), len(self.df_jg), len(self.list_buy),
                len(self.list_sell), self.int_cttr, self.int_ctcj, self.int_ctcr, self.int_cthj, self.int_ctjc,
                self.int_ctrjc, self.int_ctrhj, self.int_ctsc]
        self.windowQ.put(info)
        self.int_ctrjc = 0
        self.int_ctrhj = 0
        self.UpdateSysinfo()

    @Thread_Decorator
    def UpdateSysinfo(self):
        p = psutil.Process(os.getpid())
        self.float_memory = round(p.memory_info()[0] / 2 ** 20.65, 2)
        self.int_threads = p.num_threads()
        self.float_cpuper = round(p.cpu_percent(interval=2) / 3, 2)

    def SysExit(self):
        if self.bool_sound:
            self.soundQ.put("십초 후 시스템을 종료합니다.")
        else:
            self.windowQ.put([1, "10초 후 시스템을 종료합니다."])
        i = 10
        while i > 0:
            self.windowQ.put([1, f"시스템 종료 카운터 {i}"])
            i -= 1
            time.sleep(1)
        self.soundQ.put("시스템 종료")
        self.queryQ.put("시스템 종료")
        self.hogaQ.put("시스템 종료")
        self.chartQ.put("시스템 종료")
        self.windowQ.put([1, "시스템 종료"])
        sys.exit()
