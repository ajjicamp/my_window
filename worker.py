import sys
from PyQt5 import QtWidgets, QAxContainer

app = QtWidgets.QApplication(sys.argv)

class worker:
    def __init__(self):
        self.bool_conn = False
        self.bool_cdload = False
        self.bool_trcdload = False
        self.bool_trremained = True

        self.ocx = QAxContainer.QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._h_login)
        self.ocx.OnReceiveTrData.connect(self._h_tran_data)
        self.ocx.OnReceiveRealData.connect(self._h_real_data)
        self.ocx.OnReceiveChejanData.connect(self._h_cjan_data)
        self.ocx.OnReceiveTrCondition.connect(self._h_cond_data)
        self.ocx.OnReceiveConditionVer.connect(self._h_cond_load)
        self.ocx.OnReceiveRealCondition.connect(self._h_real_cond)
        self.Start()

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
                data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, row,
                                            item)
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
