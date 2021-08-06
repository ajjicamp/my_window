import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
import pythoncom
import datetime
import parser
from RealType import *
import pandas as pd
import time
from multiprocessing import Process, Queue
from hoga import HogaUpdate
import logging

# app = QApplication(sys.argv)

# logging.basicConfig(filename="../log.txt", level=logging.ERROR)
# logging.basicConfig(level=logging.INFO)

# class Worker(Process):
class Worker:
    def __init__(self, hogaQ, login=False):
        # super().__init__()
        if not QApplication.instance():
            app = QApplication(sys.argv)

        self.hogaQ = hogaQ
        self.connected = False              # for login event
        self.received = False               # for tr event
        self.tr_remained = False
        self.condition_loaded = False

        self.tr_items = None                # tr input/output items
        self.tr_data = None                 # tr output data
        self.tr_record = None

        self.realType = RealType()        # class 인스턴스
        self.real_data_dict = {}
        self.real_data_df = {}           # 딕셔너리의 값에 DataFrame을 저장할 변수

        self.list_kosd = None
        self.code_list = None

        # 조건식때문에 작동하지 않는다. 언제 작동하려고 준비한건지
        # if login:
        #     self.CommConnect()
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        # self._set_signals_slots()
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_tr)
        self.ocx.OnReceiveRealData.connect(self._handler_real)
        self.ocx.OnReceiveConditionVer.connect(self._handler_condition_load)
        self.ocx.OnReceiveTrCondition.connect(self._handler_tr_condition)
        self.ocx.OnReceiveMsg.connect(self._handler_msg)
        self.ocx.OnReceiveChejanData.connect(self._handler_chejan)
        self.start()

    def start(self):
        self.CommConnect(block=True)
        self.list_kosd = self.GetCodeListByMarket("10")
        self.code_list = self.GetCondition()
        # print('관심종목리스트:', self.code_list)
        self.SetRealReg("1001", self.code_list, "20;41", "0")
        real_event_loop = 
        # app.exec_()
        # self.EventLoop()

    '''
    def EventLoop(self):
        while True:
            if not self.hogaQ.empty():
                work = self.hogaQ.get()
                if type(work) == list:
                    self.UpdateRealreg(work)
                elif type(work) == str:
                    self.RunWork(work)
            time_loop = timedelta_sec(0.25)
            while datetime.datetime.now() < time_loop:
                pythoncom.PumpWaitingMessages()
                time.sleep(loop_sleeptime)
    '''

    def GetCondition(self):
        # 조건식 load
        self.GetConditionLoad()
        conditions = self.GetConditionNameList()
        # 0번 조건식에 해당하는 종목 리스트 출력
        condition_index = conditions[0][0]
        condition_name = conditions[0][1]
        codes = self.SendCondition("0101", condition_name, condition_index, 0)

        code_list =None
        for i, code in enumerate(codes):
            if i == 0:
                code_list = code
            else:
                code_list = code_list + ';' + code

        # print('종목코드: ', len(codes), codes)
        return  code_list


    def _handler_login(self, err_code):
        logging.info(f"hander login {err_code}")
        if err_code == 0:
            self.connected = True

    def _handler_condition_load(self, ret, msg):
        if ret == 1:
            self.condition_loaded = True

    def _handler_tr_condition(self, screen_no, code_list, cond_name, cond_index, next):
        # print('code_list: ', code_list)
        codes = code_list.split(';')[:-1]
        self.tr_condition_data = codes
        self.tr_condition_loaded= True

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

    def _handler_real(self, code, realtype, realdata):

        # logging.info(f"OnReceiveRealData {code} {realtype} {realdata}")
        print('real_data', realtype)
        # self.real_data_dict = {}
        # self.start_time = str(datetime.datetime.now().strftime("%H%M%S.%f"))

        if realtype == "주식체결":
            print('실시간 주식체결')
            try:
                c = abs(int(self.GetCommRealData(code, 10)))  # current 현재가
                per = float(self.GetCommRealData(code, 12))  # 등락율 percent
                vp = abs(int(float(self.GetCommRealData(code, 30))))  # 전일거래량대비율 volume percent
                ch = int(float(self.GetCommRealData(code, 228)))  # 체결강도 chaegyeol height
                m = int(self.GetCommRealData(code, 14))  # 누적거래대금 mount
                o = abs(int(self.GetCommRealData(code, 16)))  # 시가 open
                h = abs(int(self.GetCommRealData(code, 17)))  # 고가 high
                ll = abs(int(self.GetCommRealData(code, 18)))  # 저가 low
                prec = self.GetMasterLastPrice(code)  # pre price 전일종가?          ===> 전일대비를 이용하면 될텐데 즉, c - 11
                v = int(self.GetCommRealData(code, 15))  # volume 거래량
                d = self.GetCommRealData(code, 20)  # 체결시간 datetime
                name = self.GetMasterCodeName(code)  # 종목명

            except Exception as e:
                print('에러발생:', e)
                # self.log.info(f"[{strtime()}] _h_real_data 주식체결 {e}")

            else:
                # pass
                self.UpdateChaegyeolData(code, name, c, per, vp, ch, m, o, h, ll, prec, v, d)

        elif realtype == "주식호가잔량":
            print('실시간 호가잔량: ', realtype)

            # self.int_cthj += 1
            # self.int_ctrhj += 1
            try:
                # 직전대비
                hg_cp = [
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

                # 호가수량
                hg_q = [
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

                # 호가(금액)
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
                # logging.info(f"[{strtime()}] _handler_real 주식호가잔량 {e}")
                logging.info(f"에러발생 : _handler_real 주식호가잔량 {e}")
            else:
                self.UpdateHogaData(code, hg_cp, hg_q, hg, per)

    def UpdateChaegyeolData(self, code, name, c, per, vp, ch, m, o, h, ll, prec, v, d):
        pass

    def UpdateHogaData(self, code, hg_cp, hg_q, hg, per):
        pass
        # self.hogaQ.put([code, hg_cp, hg_q, hg, per])
        # HogaUpdate()

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

    def _handler_msg(self, screen, rqname, trcode, msg):
        logging.info(f"OnReceiveMsg {screen} {rqname} {trcode} {msg}")

    def _handler_chejan(self, gubun, item_cnt, fid_list):
        logging.info(f"OnReceiveChejanData {gubun} {item_cnt} {fid_list}")

    #-------------------------------------------------------------------------------------------------------------------
    # OpenAPI+ 메서드
    #-------------------------------------------------------------------------------------------------------------------
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

    def SendOrder(self, rqname, screen, accno, order_type, code, quantity, price, hoga, order_no):
        """
        주식 주문을 서버로 전송하는 메서드
        시장가 주문시 주문단가는 0으로 입력해야 함 (가격을 입력하지 않음을 의미)
        :param rqname: 사용자가 임의로 지정할 수 있는 요청 이름
        :param screen: 화면번호 ('0000' 또는 '0' 제외한 숫자값으로 200개로 한정된 값
        :param accno: 계좌번호 10자리
        :param order_type: 1: 신규매수, 2: 신규매도, 3: 매수취소, 4: 매도취소, 5: 매수정정, 6: 매도정정
        :param code: 종목코드
        :param quantity: 주문수량
        :param price: 주문단가
        :param hoga: 00: 지정가, 03: 시장가,
                     05: 조건부지정가, 06: 최유리지정가, 07: 최우선지정가,
                     10: 지정가IOC, 13: 시장가IOC, 16: 최유리IOC,
                     20: 지정가FOK, 23: 시장가FOK, 26: 최유리FOK,
                     61: 장전시간외종가, 62: 시간외단일가, 81: 장후시간외종가
        :param order_no: 원주문번호로 신규 주문시 공백, 정정이나 취소 주문시에는 원주문번호를 입력
        :return:
        """
        ret = self.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                   [rqname, screen, accno, order_type, code, quantity, price, hoga, order_no])
        return ret

    def SetInputValue(self, id, value):
        """
        TR 입력값을 설정하는 메서드
        :param id: TR INPUT의 아이템명
        :param value: 입력 값
        :return: None
        """
        self.ocx.dynamicCall("SetInputValue(QString, QString)", id, value)

    def DisconnectRealData(self, screen):
        """
        화면번호에 대한 리얼 데이터 요청을 해제하는 메서드
        :param screen: 화면번호
        :return: None
        """
        self.ocx.dynamicCall("DisconnectRealData(QString)", screen)

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
        ret = self.ocx.dynamicCall("CommKwRqData(QString, bool, int, int, QString, QString)", arr_code, next, code_count, type, rqname, screen);
        return ret

    def GetAPIModulePath(self):
        """
        OpenAPI 모듈의 경로를 반환하는 메서드
        :return: 모듈의 경로
        """
        ret = self.ocx.dynamicCall("GetAPIModulePath()")
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

    def GetConnectState(self):
        """
        현재접속 상태를 반환하는 메서드
        :return: 0:미연결, 1: 연결완료
        """
        ret = self.ocx.dynamicCall("GetConnectState()")
        return ret

    def GetMasterCodeName(self, code):
        """
        종목코드에 대한 종목명을 얻는 메서드
        :param code: 종목코드
        :return: 종목명
        """
        data = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return data

    def GetMasterListedStockCnt(self, code):
        """
        종목에 대한 상장주식수를 리턴하는 메서드
        :param code: 종목코드
        :return: 상장주식수
        """
        data = self.ocx.dynamicCall("GetMasterListedStockCnt(QString)", code)
        return data

    def GetMasterConstruction(self, code):
        """
        종목코드에 대한 감리구분을 리턴
        :param code: 종목코드
        :return: 감리구분 (정상, 투자주의 투자경고, 투자위험, 투자주의환기종목)
        """
        data = self.ocx.dynamicCall("GetMasterConstruction(QString)", code)
        return data

    def GetMasterListedStockDate(self, code):
        """
        종목코드에 대한 상장일을 반환
        :param code: 종목코드
        :return: 상장일 예: "20100504"
        """
        data = self.ocx.dynamicCall("GetMasterListedStockDate(QString)", code)
        return datetime.datetime.strptime(data, "%Y%m%d")

    def GetMasterLastPrice(self, code):
        """
        종목코드의 전일가를 반환하는 메서드
        :param code: 종목코드
        :return: 전일가
        """
        data = self.ocx.dynamicCall("GetMasterLastPrice(QString)", code)
        return int(data)

    def GetMasterStockState(self, code):
        """
        종목의 종목상태를 반환하는 메서드
        :param code: 종목코드
        :return: 종목상태
        """
        data = self.ocx.dynamicCall("GetMasterStockState(QString)", code)
        return data.split("|")

    def GetDataCount(self, record):
        count = self.ocx.dynamicCall("GetDataCount(QString)", record)
        return count

    def GetOutputValue(self, record, repeat_index, item_index):
        count = self.ocx.dynamicCall("GetOutputValue(QString, int, int)", record, repeat_index, item_index)
        return count

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

    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return data

    def GetChejanData(self, fid):
        data = self.ocx.dynamicCall("GetChejanData(int)", fid)
        return data

    def GetThemeGroupList(self, type=1):
        data = self.ocx.dynamicCall("GetThemeGroupList(int)", type)
        tokens = data.split(';')
        if type == 0:
            grp = {x.split('|')[0]:x.split('|')[1] for x in tokens}
        else:
            grp = {x.split('|')[1]: x.split('|')[0] for x in tokens}
        return grp

    def GetThemeGroupCode(self, theme_code):
        data = self.ocx.dynamicCall("GetThemeGroupCode(QString)", theme_code)
        data = data.split(';')
        return [x[1:] for x in data]

    def GetFutureList(self):
        data = self.ocx.dynamicCall("GetFutureList()")
        return data

    def GetCommDataEx(self, trcode, record):
        data = self.ocx.dynamicCall("GetCommDataEx(QString, QString)", trcode, record)
        return data

    def block_request(self, *trcode, **kwargs):
        '''
        tr조회함수
        :param args: ex) 'opt10001'
        :param kwargs: 종목코드="005930", output="주식기본정보", next=0
        :return:
        '''
        trcode = trcode[0].lower()
        lines = parser.read_enc(trcode)
        self.tr_items = parser.parse_dat(trcode, lines)
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

        return self.tr_data

    def SetRealReg(self, screen, code_list, fid_list, real_type):
        ret = self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen, code_list, fid_list, real_type)
        print('ret:', ret)
        return ret

    def SetRealRemove(self, screen, del_code):
        ret = self.ocx.dynamicCall("SetRealRemove(QString, QString)", screen, del_code)
        return ret

    def GetConditionLoad(self, block=True):
        self.condition_loaded = False
        self.ocx.dynamicCall("GetConditionLoad()")
        if block:
            while not self.condition_loaded:
                pythoncom.PumpWaitingMessages()

    def GetConditionNameList(self):
        data = self.ocx.dynamicCall("GetConditionNameList()")
        conditions = data.split(";")[:-1]

        # [('000', 'perpbr'), ('001', 'macd'), ...]
        result = []
        for condition in conditions:
            cond_index, cond_name = condition.split('^')
            result.append((cond_index, cond_name))

        return result

    def SendCondition(self, screen, cond_name, cond_index, search):
        self.tr_condition_loaded = False
        self.ocx.dynamicCall("SendCondition(QString, QString, int, int)", screen, cond_name, cond_index, search)

        while not self.tr_condition_loaded:
            pythoncom.PumpWaitingMessages()

        return self.tr_condition_data

    def SendConditionStop(self, screen, cond_name, index):
        self.ocx.dynamicCall("SendConditionStop(QString, QString, int)", screen, cond_name, index)

    def GetCommDataEx(self, trcode, rqname):
        data = self.ocx.dynamicCall("GetCommDataEx(QString, QString)", trcode, rqname)
        return data

    def SendOrder(self, rqname, screen, accno, order_type, code, quantity, price, hoga, order_no):
        self.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                             [rqname, screen, accno, order_type, code, quantity, price, hoga, order_no])
        # 주문 후 0.2초 대기
        time.sleep(0.2)

    def CurrentTime(self):
        return time.strftime('%H%M%S')

if __name__ == "__main__":
    # queue = Queue
    queue = "Queue"
    Process(target=Worker, args=(queue,), daemon=True).start()
    # worker = Worker(queue)
    # worker.start()
    # worker = Worker(queue)
    app = QApplication(sys.argv)
    app.exec_()