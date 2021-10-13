import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
import pythoncom
import datetime
# from RealType import *
import pandas as pd
import time
import zipfile
import logging
from multiprocessing import Value, Process, Queue, current_process, Manager
# from hoga import Hoga

app = QApplication(sys.argv)
# logging.basicConfig(filename="../log.txt", level=logging.ERROR)
logging.basicConfig(level=logging.INFO)

class Worker:
    def __init__(self, N_, L_ACC_jango, D_GSJM_name, D_GSJM_code, windowQ, workerQ, hogaQ, login=False):
        if not QApplication.instance():
            app = QApplication(sys.argv)
        # print('name:$$', current_process().name)
        self.N_ = N_
        self.L_ACC_jango = L_ACC_jango
        self.D_GSJM_name = D_GSJM_name
        self.D_GSJM_code = D_GSJM_code
        print('N_, D_', self.N_, self.D_GSJM_code, self.D_GSJM_name)
        self.windowQ = windowQ
        self.workerQ = workerQ
        self.hogaQ = hogaQ
        self.connected = False              # for login event
        self.received = False               # for tr event
        self.tr_remained = False
        self.condition_loaded = False

        # self.dict_code_name = {} # 조건검색결과 종목코드리스트의 {종목코드:종목명, 종목코드: 종목명 ,,,,,}
        # self.dict_name_code = {}

        self.tr_items = None                # tr input/output items
        self.tr_data = None                 # tr output data
        self.tr_record = None

        # self.realType = RealType()        # class 인스턴스

        columns_gs = ['종목명', '현재가', '등락율', '전일거래량대비율', '체결강도', '누적거래대금', '시가' , '고가', '저가', '전일종가', '거래량', '체결시간']
        self.chaegyeol_data_df = pd.DataFrame(columns=columns_gs)  # real_data를 저장할 DataFrame 변수

        # self.dict_gsjm = {}   # 관심종목 key:code, value:dataframe   #즉, 종목별로 df_table 별도

        ###############
        # self.selected_code = None
        self.list_kosd = None
        self.code_list = None

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_tr)
        self.ocx.OnReceiveRealData.connect(self._handler_real)
        self.ocx.OnReceiveConditionVer.connect(self._handler_condition_load)
        self.ocx.OnReceiveTrCondition.connect(self._handler_tr_condition)
        self.ocx.OnReceiveMsg.connect(self._handler_msg)
        self.ocx.OnReceiveChejanData.connect(self._handler_chejan)
        self.start()

    def start(self):
        self.createDatabase()
        self.loadDatabase()
        self.CommConnect(block=True)
        self.list_kosd = self.GetCodeListByMarket('10')
        self.GetCondition()
        self.accno = self.GetLoginInfo('ACCNO')    # list
        self.GetAccountJango()   # 보유종목이 바뀔때마다 실행되도록 해야 함.
        # self.GetAccountEvaluation()
        self.EventLoop()
        app.exec_()

    def createDatabase(self):
        pass

    def loadDatabase(self):
        pass

    def EventLoop(self):
        def now():
            return datetime.datetime.now()

        while True:
            if not self.workerQ.empty():
                data = self.workerQ.get()
                print('workerQ_data 수신')
                if data == 'GetAccountJango':
                    self.GetAccountJango()
                elif data == 'GetAccountEvaluation':
                    self.GetAccountEvaluation()

            time_loop = now() + datetime.timedelta(seconds=0.25)
            # print(now(), time_loop)
            while now() < time_loop:
                pythoncom.PumpWaitingMessages()
                time.sleep(0.0001)

    def GetCondition(self):
        # kiwoom 조건검색식 load
        self.GetConditionLoad()
        conditions = self.GetConditionNameList()
        # 0번 조건식 가져오기
        condition_index = conditions[0][0]      # 첫번째 조건검색식의 이름 (여기서는 '마하세븐)
        condition_name = conditions[0][1]       # 첫번째 조건검색식의 번호 (첫번째라고 반드시 1번은 아니다.)

        codes = self.SendCondition("0101", condition_name, condition_index, 0)    # 조건검색식에 해당하는 종목리스트 얻기

        '''
        # codes[0]은 list type의 리스트로써 종목명을 얻는 tr > GetMasterCodeName()할때 필요.
        # codes[1]은 ';'로 구분된 str type으로써 real 등록 > SetRaalReg할 때 필요.
        '''

        # 관심종목의 namelistdict{code:name}를 만듬.
        for code in codes[0]:
            name = self.GetMasterCodeName(code)
            # self.dict_code_name[code] = name
            self.D_GSJM_name[code] = name
            self.D_GSJM_code[name] = code

        self.N_.code = self.D_GSJM_name.keys()[0]

        # print('worker129 관심종목코드dict', self.D_GSJM_code)

        self.windowQ.put(['GSJM', ('initial', self.D_GSJM_name, self.D_GSJM_code)])

        # 관심종목 실시간 등록
        ret = self.SetRealReg("1001", codes[1], "20;41", "0")
        if ret == 0:
            print("관심종목의 실시간 데이터수신을 시작합니다.")

    # tr방식으로 잔고업데이트
    def GetAccountJango(self):
        # self.accno = ['8000707411']
        print('계좌번호:', self.accno)
        dfs = []
        df = self.block_request('opw00018', 계좌번호=self.accno[0], 비밀번호='0000', 비밀번호입력매체구분='00',
                            조회구분=2, output='계좌평가잔고개별합산', next=0)
        dfs.append(df)

        while self.tr_remained:
            df = self.block_request('opw00018', 계좌번호=self.accno[0], 비밀번호='0000', 비밀번호입력매체구분='00',
                                  조회구분=2, output='계좌평가잔고개별합산', next=2)
            dfs.append(df)
            time.sleep(1)
        # print('00018\n', dfs)

        cnt = len(df)
        # acc_jango = []    #
        self.L_ACC_jango[:] = []
        real_code_list = []    # 계좌보유종목리스트를 생성 ---> 실시간 감시종목으로 추가하기 위해서
        for row in range(cnt):
            if not df.loc[row]['종목명'] == '':    # 종목명이 있다

                code = df.loc[row]['종목번호'][1:]
                name = df.loc[row]['종목명']
                quan =int(df.loc[row]['보유수량'])
                buy_prc = int(df.loc[row]['매입가'])
                cur = int(df.loc[row]['현재가'])
                Y_rate = float(df.loc[row]['수익률(%)'])
                EG = int(df.loc[row]['평가손익'])
                EA = int(df.loc[row]['평가금액'])
                data = (code, name, quan, buy_prc, cur, Y_rate, EG, EA)

                # acc_jango.append(data)    # [(data),(data),(data) ...]

                # 공유메모리 리스트에 보유종목코드 리스트를 저장
                self.L_ACC_jango.append(data)

                real_code_list.append(code)

                # 관심종목 리스트에 추가,
                self.D_GSJM_name[code] = name
                self.D_GSJM_code[name] = code

            else:   # 계좌잔고가 하나도 없으면 ...
                self.windowQ.put(['AccJango', ''])

        # print('l acc jango', self.L_ACC_jango)

        # 잔고종목을 실시간 감시하기 위하여 리스트를 tr용 (;) 문자열 형식으로 변환하고 setrealreg
        real_reg_list = ''  # SetRealReg 용 문자열
        for item in real_code_list:
            real_reg_list += item + ';'
        self.SetRealReg("1001",real_reg_list,"20;41", "1" )

        # todo ????
        # self.windowQ.put(['GSJM', ('initial', self.D_GSJM_name, self.D_GSJM_code)])

        # 계좌잔고창 update 지시
        # print('accjango', acc_jango)
        self.windowQ.put(['AccJango'])

    def GetAccountEvaluation(self):
        df = self.block_request('opw00018', 계좌번호=self.accno[0], 비밀번호='0000', 비밀번호입력매체구분='00',
                            조회구분=2, output='계좌평가결과', next=0)

        accno = self.accno[0]
        E_Assets = int(df.loc[0]['추정예탁자산'])
        Y_rate= float(df.loc[0]['총수익률(%)'])
        eva_profit = int(df.loc[0]['총평가손익금액'])
        eva_amount = int(df.loc[0]['총평가금액'])
        buy_amount = int(df.loc[0]['총매입금액'])
        acc_eva_info = (accno, E_Assets, Y_rate, eva_profit, eva_amount, buy_amount)

        self.windowQ.put(['AccEvaluation', acc_eva_info])

    #######################
    # Kiwoom _handler [SLOT]
    #######################

    def _handler_login(self, err_code):
        # logging.info(f"hander login {err_code}")
        if err_code == 0:
            self.connected = True

    def _handler_condition_load(self, ret, msg):
        if ret == 1:
            self.condition_loaded = True

    def _handler_tr_condition(self, screen_no, code_list, cond_name, cond_index, next):
        # print('code_list: ', code_list)
        self.code_list = code_list  # 코드리스트 구분자 ';'    type(str)
        codes = self.code_list.split(';')[:-1]
        self.tr_condition_data = codes  # 코드리스트 구분자를 없앤 type(list)
        # print('codes:$$ ', self.tr_condition_data)
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

    '''
    # real data 수신
    '''
    def _handler_real(self, code, realtype, realdata):

        # logging.info(f"OnReceiveRealData {code} {realtype} {realdata}")
        # print('real_data', realtype)

        receiving_time = str(datetime.datetime.now().strftime("%H%M%S.%f"))
        # 여기서 real_data 수신로그를 windowQ로 보낸다
        self.windowQ.put(['LOG',('수신시간', realtype , receiving_time)])

        if realdata == '':
            return
        if realtype == "주식체결":
            # print('실시간 주식체결')
            try:
                # real에서 종목명을 조회하면 tr 조회가 너무 많아져서 lock

                name = self.D_GSJM_name[code]  # 종목명
                # name = self.dict_code_name[code]  # 종목명
                c = abs(int(self.GetCommRealData(code, 10)))  # current 현재가
                db = int(self.GetCommRealData(code, 11))  # 전일대비
                per = float(self.GetCommRealData(code, 12))  # 등락율 percent
                v = int(self.GetCommRealData(code, 15))  # volume 거래량
                cv = int(self.GetCommRealData(code, 13))  # 누적 거래량
                cva = int(self.GetCommRealData(code, 14))  # 누적거래대금 amount
                o = abs(int(self.GetCommRealData(code, 16)))  # 시가 open
                h = abs(int(self.GetCommRealData(code, 17)))  # 고가 high
                ll = abs(int(self.GetCommRealData(code, 18)))  # 저가 low
                vp = abs(int(float(self.GetCommRealData(code, 30))))  # 전일거래량대비율 volume percent
                ch = int(float(self.GetCommRealData(code, 228)))  # 체결강도 chaegyeol height
                prec = self.GetMasterLastPrice(code)  # pre price 전일종가?          ===> 전일대비를 이용하면 될텐데 즉, c - 11
                d = self.GetCommRealData(code, 20)  # 체결시간 datetime

            except Exception as e:
                print('에러발생:', e)
                # self.log.info(f"[{strtime()}] _h_real_data 주식체결 {e}")

            else:
                self.UpdateChaegyeolData(code, name, c, db, per, v, cv,cva, o, h, ll, vp, ch, prec, d)

        elif realtype == "주식호가잔량":
            try:
                # 호가시간
                # hg_tm = self.GetCommRealData(code, 21)

                # 직전대비
                hg_db = [
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
                hg_sr = [
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
                sanghanga = self.GetSanghanga(code)
                hahanga =  self.GetHahanga(code)

                hg_ga = [
                    sanghanga,
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
                    hahanga
                ]

                prec = self.GetMasterLastPrice(code)

                per = [
                    round((hg_ga[0] / prec - 1) * 100, 2),
                    round((hg_ga[1] / prec - 1) * 100, 2),
                    round((hg_ga[2] / prec - 1) * 100, 2),
                    round((hg_ga[3] / prec - 1) * 100, 2),
                    round((hg_ga[4] / prec - 1) * 100, 2),
                    round((hg_ga[5] / prec - 1) * 100, 2),
                    round((hg_ga[6] / prec - 1) * 100, 2),
                    round((hg_ga[7] / prec - 1) * 100, 2),
                    round((hg_ga[8] / prec - 1) * 100, 2),
                    round((hg_ga[9] / prec - 1) * 100, 2),
                    round((hg_ga[10] / prec - 1) * 100, 2),
                    round((hg_ga[11] / prec - 1) * 100, 2),
                    round((hg_ga[12] / prec - 1) * 100, 2),
                    round((hg_ga[13] / prec - 1) * 100, 2),
                    round((hg_ga[14] / prec - 1) * 100, 2),
                    round((hg_ga[15] / prec - 1) * 100, 2),
                    round((hg_ga[16] / prec - 1) * 100, 2),
                    round((hg_ga[17] / prec - 1) * 100, 2),
                    round((hg_ga[18] / prec - 1) * 100, 2),
                    round((hg_ga[19] / prec - 1) * 100, 2),
                    round((hg_ga[20] / prec - 1) * 100, 2),
                    round((hg_ga[21] / prec - 1) * 100, 2)
                ]
            except Exception as e:
                # logging.info(f"[{strtime()}] _handler_real 주식호가잔량 {e}")
                logging.info(f"에러발생 : _handler_real 주식호가잔량 {e}")

            else:
                self.UpdateHogaData(code, hg_db, hg_sr, hg_ga, per)


        # elif realtype == '장시작시간':     # 일단 soulsnow의 code를 잠시 그대로 둔다.
        #     if self.dict_intg['장운영상태'] == 8:
        #         return
        #     try:
        #         self.dict_intg['장운영상태'] = int(self.GetCommRealData(code, 215))
        #         current = self.GetCommRealData(code, 20)
        #         remain = self.GetCommRealData(code, 214)
        #     except Exception as e:
        #         self.windowQ.put([1, f'OnReceiveRealData 장시작시간 {e}'])
        #     else:
        #         self.OperationAlert(current, remain)

        # elif realtype == '업종지수':
            # if self.dict_bool['실시간데이터수신중단']:
            #     return
            # self.dict_intg['주식체결수신횟수'] += 1
            # self.dict_intg['초당주식체결수신횟수'] += 1
            # try:
            #     c = abs(float(self.GetCommRealData(code, 10)))
            #     v = int(self.GetCommRealData(code, 15))
            #     d = self.GetCommRealData(code, 20)
            # except Exception as e:
            #     self.windowQ.put([1, f'OnReceiveRealData 업종지수 {e}'])
            # else:S
                # self.UpdateUpjongjisu(code, d, c, v)

    def UpdateChaegyeolData(self, code, name, c, db, per, v, cv, cva, o, h, ll, vp, ch, prec, d):

        # self.SaveChaegyeolData(code, c, db, per, v, cv, cva, o, h, ll, vp, ch, prec, d)
        self.windowQ.put(['GSJM', ('real', code, name, c, db, per, cv, cva, ch)])

        # if code == self.selected_code:
        if code == self.N_.code:
            self.windowQ.put(['HOGA', ('chaegyeol', v)])
        # self.SaveChaegyeolData()

        # 호가창의 체결내역, 관심종목창, 보유잔고창을 업데이트 해야한다.
        # 다음으로 매수, 매도, 조건분석을 위해 data를 datafragme, sqlite3 DB에 저장해야 한다.

    '''
    def SaveChaegyeolData(self, code, c, db, per, v, cv, cva, o, h, ll, vp, ch, prec, d):
        file_name = "mh_" + datetime.datetime.now().strftime("%m%d") + ".db"
        con = sqlite3.connect(file_name)

        # cursor = con.cursor()
        with con:
            df_len = len(self.real_sign_df)
            print('df_len01: ', df_len)
            print('null??: ', self.real_sign_df['현재시간'].isnull().sum())
            # self.real_sign_df.to_sql('주식체결' , con, if_exists='append', chunksize=df_len)
            # self.real_sign_df.to_sql('주식체결' , con, if_exists='append', chunksize=2100)

            self.real_sign_df.to_sql('sign' , con, if_exists='append', chunksize=2100)


            df_len = len(self.real_hoga_df)
            print('df_len02: ', df_len)
            # #self.real_hoga_df.to_sql('주식호가잔량' , con, if_exists='append', chunksize=df_len)
            self.real_hoga_df.to_sql('hoga' , con, if_exists='append', chunksize=2100)
    '''

    def UpdateHogaData(self, code, hg_db, hg_sr, hg_ga, per):
        # 호가창, 관심종목창, 주식잔고창 update
        # todo 호가창에 보내는 데이터는 선택된 종몸의 것만 보내야 한다.
        # if code == self.selected_code:
        if code == self.N_.code:
            self.windowQ.put(['HOGA', ('hoga', hg_db, hg_sr, hg_ga, per)])

            # self.windowQ.put()

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
        # lines = parser.read_enc(trcode)
        lines = self.ReadEnc(trcode)

        self.tr_items = self.ParseDat(trcode, lines)
        self.tr_record = kwargs["output"]
        # next = kwargs["next"]

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

        return self.tr_data       # df output항목을 columns로 하는 데이터프레임을 반환(_handler_tr과 상호작용

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

    def SetRealReg(self, screen, code_list, fid_list, real_type):
        ret = self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen, code_list, fid_list, real_type)
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

        return (self.tr_condition_data, self.code_list)

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
