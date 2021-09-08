 # tick_data 분석용 차트프로그램 최종본이다.(7/3)
import sqlite3
import sys
import time
import datetime
import pandas as pd
import numpy as np
import math
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import gridspec
from PyQt5.QAxContainer import *
import pythoncom
import logging

# logging.basicConfig(level=logging.INFO)
logging.basicConfig(filename="../log.txt", level=logging.ERROR)

# 한글폰트 깨짐방지
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False #한글 폰트 사용시 마이너스 폰트 깨짐 해결

form_class = uic.loadUiType("tick_calc.ui")[0]
hoga_window = uic.loadUiType("hoga_window.ui")[0]

class MyKiwoom:
    def __init__(self):
        self.connected = False              # for login event
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signals_slots()
        self.CommConnect()

    def _handler_login(self, err_code):
        logging.info(f"hander login {err_code}")
        if err_code == 0:
            self.connected = True

    def _handler_tr(self, screen, rqname, trcode, record, next):
        logging.info(f"OnReceiveTrData {screen} {rqname} {trcode} {record} {next}")

    def _set_signals_slots(self):
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveTrData.connect(self._handler_tr)

    def _handler_msg(self, screen, rqname, trcode, msg):
        logging.info(f"OnReceiveMsg {screen} {rqname} {trcode} {msg}")

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

# class Mywindow(QWidget, form_class):
class Mywindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        stime = time.time()
        print('stime: ', stime)

        #### 변수선언
        self.jongmok = []
        # mykiwoom = MyKiwoom()
        # 데이터 전처리
        self.receive_data()      #  sqlite db로부터 데이터를 읽어와서 합치고 sort하고 null값을 채우는 전처리과정

        print('소요시간:', time.time() - stime)   # 읽어오는데 24초나 걸린다.

        # 미리 그려둔 window화면
        self.setupUi(self)       # 여기서 종목선택하고 마치면 다시 돌아온다.

        # 위 미리 그려둔 window화면내 self.comboBox에 item을 추가하는 것임. data 전처리과정에서 종목리스트 생성
        for i in range(len(self.jongmok)):
            self.comboBox.addItem(self.jongmok[i])

        # 이밴트를 처리하는 슬롯  ===> 콤보박스 내 item을 선택하면 실행하는 로직.
        self.comboBox.activated[str].connect(self.onActivated)
        self.show()

    def onActivated(self, text):
        # self.lbl.setText(text)
        # self.lbl.adjustSize()
        self.sCode = text
        # print('code: ', text, self.sCode)

        # 선택된 종목코드를 기준으로 필터링하고 reset_index

        self.code_data = self.dfs[self.sCode]
        # self.code_data = self.dfs[self.dfs['종목코드'] == self.sCode]
        self.code_data.reset_index(inplace=True)   # 원본을 덮어씀

        self.show_ticks = 400
        self.curr_pos = 0
        self.base_graph()

    def base_graph(self, ex=False):
        # print("base-graph$$")
        # 첫번째 그래프 작성(x축:시계열 데이터, y축: '매도호가1'
        # 앞으로 한화면에 나타낼 series 슬라이싱은 실질 인덱스 번호를 기준으로 핸들링한다.
        # 그래프를 분할하여 그릴 화면개수 계산; 총틱수를 한화면틱개수로 나누어서 소수점 미만 올림

        data = self.code_data
        self.scr_cnt = math.ceil(len(data) / self.show_ticks)    # int + 1 하면 동일한 효과일 것 같으나, 소숫점 미만이 0인 경우의 값이 1크게 된다.
        # print('scr_cnt: ', self.scr_cnt)

        plots = []
        for i in range(self.scr_cnt):
            start = i * self.show_ticks        # start 변수는 여기 for문 내에서만 사용된다.
            end = start + self.show_ticks -1   # loc기준 슬라이싱은 마지막 번호를 포함하므로 의도한 show_ticks를 나타내려면 1을 차감해야 한다.
            x_data = data['수신시간'].loc[start:end]
            y_data = data['매도호가1'].loc[start:end]
            plots.append((x_data, y_data))
            # print(f'plots[{i}]', plots[i])

        self.plots = plots
        # print('plots: ', plots)
            # 여기까지만 하고 화면번호 지정/변경 및 plt.show()는 별도로 한다.

        # 여기서 기존 그래프를 덮어쓰기 하는 방법을 알아야 한다.

        if ex:    # 새로 figure를 만들지 않고 기존 fig와 ax를 사용하여 덮어씀. 그래야 기존 figure를 지우는 효과
            fig = self.fig
            ax = self.ax
            ax.cla()
        else:
            # fig = plt.figure(figsize=(19, 13))
            fig = plt.figure()
            ax = fig.add_subplot(111)

        # plt.rcParams['lines.linewidth'] = 4
        # plt.rcParams['lines.color'] = 'r'
        # plt.tight_layout(pad=0)
        plt.subplots_adjust(left=0.08, bottom=0.10, right=0.95, top=0.90, wspace=0.1, hspace=0.01)
        ax.margins(x=0, y=0)

        fig.canvas.mpl_connect('key_press_event', self.key_event)
        fig.canvas.mpl_connect("button_press_event", self.clicked_graph)  # <= 이렇게 하면 마우스버튼을 클릭하면 동작하게 된다.

        self.fig = fig
        self.ax = ax

        redraw =False
        self.base_graph_draw( redraw,ex)

    def base_graph_draw(self, redraw,ex):

        ax =self.ax
        fig = self.fig

        if redraw:
            ax.cla()         # ax자체는 그대로 두고 그래프만 다시 그린다.(축설정 새로)

        x = self.plots[self.curr_pos][0]                    # x, y 축 변수는 지역변수이므로 다음에 다른 함수에서 다시 써도 된다.
        y = self.plots[self.curr_pos][1]
        # print('x----', x)
        # print('y----', y)

        plt.suptitle(self.sCode + '종목 틱시세 변동추이',y=0.98, size= 20)
        plt.title(str(self.curr_pos+1) + ' / ' + str(self.scr_cnt), {'fontsize' : 15},loc='left', pad=10 )
        # plt.tight_layout()
        ax.plot(x, y, linewidth = 3, label='매도호가1')
        ax.legend()

        # x축 눈금설정
        ax.set_xticks(x)

        # x축 눈금 레이블 설정
        # xt_label = list(map(lambda i: i[11:22], x)) #lambda 함수를 이용하여 for문을 대신하여 x의 요소를 슬라이싱하여 리스트에 저장
        # xt_label = [ i[11:22] for i in x]   # 위의 코딩을 더 간단히 한것이다.
        # ax.set_xticklabels([ xt_label, rotation = 90)

        ax.set_xticklabels([i[11:22] for i in x], rotation=90)  # 위 두줄 코딩을 한줄에 했다.
        # 눈금레이블을 5칸 간격으로 표시하고 작은 눈금은 선으로만 표시
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))

        # Y축 눈금 및 레이블 설정
        hogaunit = self.hogaUnitCalc(y.iloc[0])  # y[start]인덱싱해도 동일한 결과일 수 있으나 start사용방식에 따라 달라질 수 있다.
        ytick = np.arange((min(y) - hogaunit), (max(y) + hogaunit * 2), hogaunit)
        if min(y) == max(y):
            ytick = np.arange(y.iloc[0], (y.iloc[0] + hogaunit), hogaunit)
        ax.set_yticks(ytick)
        ax.set_yticklabels( [str(int(i)) for i in ytick], fontdict={'size':13})

        ## y축이름 레이블
        rate = hogaunit / y.iloc[0] * 100
        ylabel = '호가단위: ' + str(int(hogaunit)) + '원' + '(' + str(round(rate, 2)) + '% )'
        ax.set_ylabel(ylabel, color='green', fontdict={'size': 13})

        ax.grid(True, color='gray', linewidth=0.2)

        if redraw or ex:
            fig.canvas.draw()
        else:
            plt.show()

        # 실질 index를 기준으로 slicing ; 끝번호를 포함한다.  ==> out of bound되면 empty series를 반환한다.
        # x = self.code_data['수신시간'].loc[start: end-1]
        # y = self.code_data['매도호가1'].loc[start: end-1]

        # 암묵적 정수인덱스(행번호)를 기준으로 slicing; 끝번호를 제외한다.  ==> out of bound되면 empty series를 반환한다.
        # x = self.code_data['수신시간'].iloc[start: end]
        # y = self.code_data['매도호가1'].iloc[start: end]

        # 아래처럼 loc 또는 iloc없이 그냥 인덱스 번호를 넣어도 되지만 실질 index가 정수형인 경우는 행번호와 혼동되므로 사용을 피한다.
        # 아래처럼 정수인덱스를 사용할 경우 행번호를 기준으로 사용하게 된다. 비록 실질 index 가 정수형이라 하더라도
        # x = self.code_data['수신시간'][start: end]
        # y = self.code_data['매도호가1'][start: end]

        # 아래처럼 속성을 이용해도 된다.
        # x = self.code_data.수신시간.loc[start: end-1]
        # y = self.code_data.매도호가1'.loc[start: end-1]

        # print(x,y)           # x는 object이다. 문자열은 dtype object로 나타난다.

        # 이상하게도 막대그래프가 한개로 합쳐져서 그려진다.  ==> 이유는 matplotlib는 막대그래프를 일(day)기준으로 그리기 때문이다.
        # plt.bar(x,y)

    def key_event(self, e):
        # print('key_event_handler')
        show_ticks = self.show_ticks
        if e.key == 'right':
            self.curr_pos += 1
        elif e.key == 'left':
            self.curr_pos -= 1
        elif e.key == 'up':
            self.show_ticks += 50
            # show_ticks가 증가함에 따라 curr_pos를 맞추어 조정
        elif e.key == 'down':
            self.show_ticks -= 50

        elif e.key == 'pageup':
            self.show_ticks = len(self.code_data)           # 한화면에 다 그린다.

        # keyboard key값이 사용될수 있는 것: pageup, delete, insert, home, control 등 소문자로 사용하면 대체로 통한다.

        # elif e.key == 'Ctrl_up':
        #     print('ctrl + up')
        # ctrl up key 누르면 전체데이터를 한화면에 그래프를 그림.

        if e.key == 'up' or e.key == 'down':
            # show_ticks가 증가함에 따라 curr_pos를 맞추어 조정
            self.curr_pos = int((self.curr_pos * show_ticks) / self.show_ticks)
            # 기존그래프를 완전히 지우고 새로 그린다.
            # self.fig.clf()    # 기존그래프를 지우는 것이 아니라 작동은 무효화시키는 것 같다.??subplot이 있을때는 동작을 안하는 것 같다.
            # plt.fig(0  # 위와 마찬가지이다. 화면에서 사라지지 않는다.
            # plt.cla()  # 위와 마찬가지이다. 화면에서 사라지지 않는다.
            # plt.clf()  # 이것도 위와 동일 화면은 사라지지 않음.
            # time.sleep(5)
            # plt.close()    # 이렇게 하면 그래프가 지워지는 것은 맞는데 프로그램이 종료된다. 2개이면 나중 그래프가 닫힌다.

            self.base_graph(ex=True)
            return

        elif e.key == 'pageup':
            self.curr_pos = int((self.curr_pos * show_ticks) / self.show_ticks)
            self.base_graph(ex=True)
            return

        self.curr_pos = self.curr_pos % self.scr_cnt

        print('curr_pos: ', self.curr_pos)
        print('show-ticks: ', self.show_ticks)
        self.base_graph_draw(redraw=True, ex=False)

    def clicked_graph(self, event):
        # print('clicked')
        if event.xdata == None:  # 마우스 클릭한 위치가 그래프 좌표를 벗어난 경우
            return

        x_ = int(event.xdata)
        # print("x_base: ", x_)

        x_pos = self.curr_pos * self.show_ticks + x_
        # print("x_pos: ", x_pos)

        # 기준값을 시작점으로 50개 그래프에 나타내기
        self.new_plot(x_pos)

    def new_plot(self, x_pos):
        data = self.code_data
        self.show_ticks_new = 50          # new_plot의 한화면 틱개수 설정
        self.scr_cnt_new = int(len(data) / self.show_ticks_new) +1    # 이건 따로 정의해야 한다.

        fig = plt.figure(figsize=(19, 13))
        fig.canvas.mpl_connect('key_press_event', self.key_event2)  # new_plot 내에서 화살표키로 이동하는 이벤트설정
        fig.canvas.mpl_connect("button_press_event", self.clicked_act)  # <= 이렇게 하면 마우스버튼을 클릭하면 동작하게 된다.


        # 화면설정
        gs = gridspec.GridSpec(nrows=2,  # row 몇 개
                               ncols=1,  # col 몇 개
                               height_ratios=[1, 3],
                               width_ratios=[20]
                               )
        plt.subplots_adjust(left=0.05, bottom=0.10, right=0.95, top=0.95, wspace=0.1, hspace=0.01)
        # plt.tight_layout()
        # plt.rc('axes', labelsize = 13 )

        self.ax0 = plt.subplot(gs[0])   # nrows[0]에 그릴 그래프(매도호가1)
        self.ax0_twinx = self.ax0.twinx()  # nws 1에 그릴 그래프(체결강도 막대그래프인데 invisible로 그림)
        self.ax0_twinx2 = self.ax0.twinx() # 체결강도 선그래프
        # self.ax0_twiny = self.ax0.twiny()
        self.ax0.margins(x=0)

        self.ax1 = plt.subplot(gs[1])
        self.ax1.margins(x=0)

        self.start_num = x_pos
        self.end_num = x_pos + self.show_ticks_new
        self.new_plot_draw(redraw=False)

    def new_plot_draw(self, redraw):

        if redraw:
            self.ax0.cla()
            self.ax1.cla()
            self.ax0_twinx.cla()
            self.ax0_twinx2.cla()
            # self.ax0_twiny.cla()

        print('start_num, end_num', self.start_num, self.end_num)

        y = {}
        x = self.code_data['수신시간'].loc[self.start_num:self.end_num]         #todo
        # x1 = self.code_data['수신시간dt'].loc[self.start_num:self.end_num]
        y = self.code_data['매도호가1'].loc[self.start_num:self.end_num]
        y2 = self.code_data['매수체결'].loc[self.start_num:self.end_num]
        y3 = self.code_data['매도체결'].loc[self.start_num:self.end_num]
        y4 = self.code_data['체결강도'].loc[self.start_num:self.end_num]
        y5 = self.code_data['매수호가수량1'].loc[self.start_num:self.end_num]
        y6 = self.code_data['매도호가수량1'].loc[self.start_num:self.end_num]
        y7 = self.code_data['매수호가수량2'].loc[self.start_num:self.end_num]
        y8 = self.code_data['매도호가수량2'].loc[self.start_num:self.end_num]
        y57 = y5 + y7     #  매수호가수량 1호가 + 2호가까지의 합
        y68 = y6 + y8     #  매도호가수량 1호가 + 2호가까지의 합
        y9 = self.code_data['매수호가수량3'].loc[self.start_num:self.end_num]
        y10 = self.code_data['매도호가수량3'].loc[self.start_num:self.end_num]
        y579 = y5 + y7 + y9   # 매수호가수량1호가 + 2호가 + 3호가
        y6810 = y6 + y8 + y10  # 매도호가수량 1화+ 2호가 + 3호가

        y11 = self.code_data['매수호가직전대비1'].loc[self.start_num:self.end_num]
        y12 = self.code_data['매도호가직전대비1'].loc[self.start_num:self.end_num]
        y13 = self.code_data['매수호가1'].loc[self.start_num:self.end_num]

        ###############################
        # ax0 그래프 그림
        ax0 = self.ax0
        # ax0.plot(x, y, 'go-', fillstyle= 'top', linewidth=2, label='매도호가1')
        ax0.plot(x, y, linewidth=3, label='매도호가1')
        ax0.legend()

        # y축 눈금 설정 및 레이블표시 ; ## 호가단위 계산하여 y축 저장
        hogaunit = self.hogaUnitCalc(y[self.start_num])       # 여기는 반드시 iloc를 써야한다. 화살표키를 기준으로 하면 실질인덱스는 0이 아니게 된다.
        ytick = np.arange((min(y) - hogaunit), (max(y) + hogaunit * 2), hogaunit)
        # 한 화면에서 최고가와 최저가가 동일하면 겹쳐보인다.
        if min(y) == max(y):
            ytick = np.arange(y[self.start_num], (y[self.start_num] + hogaunit), hogaunit)

        ax0.set_yticks(ytick)
        ax0.set_yticklabels([str(int(i)) for i in ytick],  fontdict={'size':11})

        ## y축이름 레이블
        ylabel = '호가단위: ' + str(int(hogaunit)) + '원'
        ax0.set_ylabel(ylabel, color='green', fontdict={'size': 11})

        # ax0그래프 grid 설정
        # ax0.grid(True, color='gray', linewidth=0.2)

        # 체결강도 맏대그래프:invisibla ===> 보이지 않게 그린다. ax1 그래프와 눈금맞추는게 목적
        ax0_twinx = self.ax0_twinx
        ax0_twinx.bar(x, y4, visible=False)
        ax0_twinx.set_visible(False)  # 눈금과 눈금레이블을 보이지 않게 한다. 눈금만 또는 label만 안보이게 할수도 있다.

        # 체결강도 선그래프
        ax0_twinx2 = self.ax0_twinx2
        ax0_twinx2.plot(x, y4, color='red', linestyle='--', linewidth=1.0, label='체결강도')
        ax0_twinx2.legend()
        ax0_twinx2.tick_params(axis='y', labelsize=11)

        # ax0_twinx2.set_yticks(y4)  # 이걸 설정하면 눈금 간격이 고르지 않게 된다.
        # ax0_twinx2.set_yticklabels(y4,  fontdict={'size':11})

        # 이하부분 ax0, ax_twin, ax_twin2의 x축은 동일하므로 xtick의 설정은 3가지 모두를 기술한 후 마지막에 한번만 하면 된다.
        ax0.set_xticks(x )

        # xticklabel 설정 ==> 시간을 초단위로 설정하고 화면상단(top)에 경과시간을 나타냄.
        xt_ = [ datetime.datetime.strptime(i,'%Y-%m-%d %H:%M:%S.%f') for i in x ]     # x값을 datetime으로 변경
        xts = [ datetime.datetime.timestamp(i) for i in xt_]                # 위 값을 다시 timestamp(float type)로 변환
        # print('xt:$$', str(round(xts[0], 2)))
        xtick_ = []
        stime = xts[0]
        for i in xts:
            cnt = i - stime
            xtick_.append(str(round(cnt, 2)))

        # ax0.set_xticklabels([i[17:22]+'초' for i in x])  # 위 넉줄 코딩을 한줄에 했다.
        ax0.set_xticklabels(xtick_)  # 위 넉줄 코딩을 한줄에 했다.
        ax0.tick_params(axis='x', top= True, labeltop=True, labelbottom=False, width=0.2, labelsize=11)
        # ax0.tick_params(axis='x', bottom = False, labelbottom=False, width=0.2, labelsize=10)
        ax0.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax0.xaxis.set_minor_locator(ticker.MultipleLocator(1))
        ax0.grid(True, which='both', color='gray', linewidth=0.2)  # True: x,y축에 grid표시,

        # ax1 = plt.subplot(gs[1])
        ax1 = self.ax1

        # 매도체결 bar그래프
        ax1.bar(x, y3, color='blue', edgecolor='black', label='매도체결')

        # 매수체결 bar그래프
        ax1.bar(x, y2, color='red', edgecolor='black', label='매수체결')

        # 매수호가수량1 선그래프
        ax1.plot(x, y5, linewidth=2, color='red', label='매수호가수량1')

        # 매도호가수량1 선그래프
        ax1.plot(x, y6, linewidth=2, color='blue', label='매도호가수량1')
        # ax1.plot(x, y57, color='red', label='매수호가수량2')
        # ax1.plot(x, y68, color='blue', label='매도호가수량2')
        # ax1.plot(x, y579, color='red', label='매수호가수량3')
        # ax1.plot(x, y6810, color='blue', label='매도호가수량3')

        # ax1.fill_between(x, 0, y5, color='lavenderblush')
        # ax1.fill_between(x, 0, y6, color='lightcyan')
        ax1.fill_between(x, y5-y5/10, y5, color='lavenderblush')
        ax1.fill_between(x, y6-y6/10, y6, color='lightcyan')

        ax1.bar(x, y11, color='white', edgecolor='red', label='매수호가대비1')
        ax1.bar(x, y12, color='white', edgecolor='blue', label='매도호가대비1')

        ax1.legend()

        # x축 눈금 및 레이블 설정
        ax1.set_xticks(x)
        # x축 눈금에 label표시 및 기울기
        # x_label_ = []
        # for x_ in x:
        #     x_label_.append(x_[11:22])  # 눈금레애블을 hh:mm:ss.f2 스타일로 설정
        # ax1.set_xticklabels(x_label_, rotation=-90)
        ax1.set_xticklabels([i[11:22] for i in x], rotation=90)  # 위 넉줄 코딩을 한줄에 했다.
        ax1.tick_params(axis='y', labelsize=11)

        ax1.grid(True, which='both', color='gray', linewidth=0.2)

        # plt.savefig('../../assets/images/markdown_img/change_subplot_size_20180516.svg')
        # plt.savefig('figsize.svg')  # 그림파일저장 ---> 화살표키를 이용하여 그림을 갱신할때 필요하다. 이게 없으면 동작하지 않는다.
        # 위 이유를 잘 모르겠으나 위줄 코당 있는 상태에서는 아래에서 plt.show만 해도 유효한데, 없으면 figure.canvas.draw해야 한다.

        # plt.subplots(constrained_layout=True)
        if redraw:
            self.ax0.figure.canvas.draw()
            self.ax0_twinx.figure.canvas.draw()
            self.ax0_twinx2.figure.canvas.draw()
            self.ax1.figure.canvas.draw()
        else:
            plt.show()

    def key_event2(self, e):

        if e.key == 'right':
            print('key_event_handler')
            self.start_num += self.show_ticks_new
            self.end_num += self.show_ticks_new
        elif e.key == 'left':
            self.start_num -= self.show_ticks_new
            self.end_num -= self.show_ticks_new

        if self.start_num >= len(self.code_data) or self.end_num >= len(self.code_data):
            self.start_num = 0
            self.end_num = self.show_ticks_new

        if self.start_num < 0:
            self.start_num = len(self.code_data) - self.show_ticks_new
            self.end_num = self.start_num + self.show_ticks_new

        self.new_plot_draw(redraw=True)

    def hogaUnitCalc(self, price, jang='kosdaq'): # 호가단위 계산함수 우선 kosdaq 으로만 계산한다.
        hogaUnit = 1

        if price < 1000:
            hogaUnit = 1
        elif price < 5000:
            hogaUnit = 5
        elif price < 10000:
            hogaUnit = 10
        elif price < 50000:
            hogaUnit = 50
        elif price < 100000 and jang == "kospi":
            hogaUnit = 100
        elif price < 500000 and jang == "kospi":
            hogaUnit = 500
        elif price >= 500000 and jang == "kospi":
            hogaUnit = 1000
        elif price >= 50000 and jang == "kosdaq":
            hogaUnit = 100

        return (hogaUnit)


    def receive_data(self):
        stime = time.time()
        # sqlite3 db 읽기 ---> '주식체결' 및 '주식호가잔량' table을 각각 dataframe으로 읽어 옴.
        # con = sqlite3.connect('mh02.db')
        con = sqlite3.connect('C:/Users/USER/PycharmProjects/my_window/db/mh02.db')
        df = pd.read_sql("SELECT * FROM sign", con, index_col=None)
        df01 = pd.read_sql("SELECT * FROM hoga", con, index_col=None)

        print('sql읽는데 소요된시간: ', time.time() - stime)

        # DataFrame 합치기
        dfs = pd.concat([df, df01])

        print('합치는데까지 시간', time.time() - stime)

        # 합친 dataframe sort해서 새로 저장
        dfs.sort_values(by=['종목코드', 'index'], inplace=True, ignore_index=True)

        print('합친 후 sort 시간: ', time.time() - stime)
        # 합친 dataframe의 null값 채우기
        self.dfs =self.rep_null(dfs)

        print('null값 채우는데까지 소요시간: ', time.time() -stime)

    def rep_null(self, dfs):
        stime = time.time()
        print('rep_null_stime: ', stime)

        # dfs의 column명 ['index']를 ['수신시간']으로 변경 ===> 이 column은 nan이 없다.
        dfs.rename(columns={'index': '수신시간'}, inplace=True)

        ## dataframe 행의 null값을 0 또는 특정값으로 대체하는 작업수행 모듈
        # 먼저 column 중 매수체결, 매도체결, 체결강도, 매수도호가직전대비1,2,3 column의 nan 값을 0으로 대체
        dfs['체결시간'] = dfs['체결시간'].fillna(0)
        dfs['매수체결'] = dfs['매수체결'].fillna(0)
        dfs['매도체결'] = dfs['매도체결'].fillna(0)
        dfs['매도호가직전대비1'] = dfs['매도호가직전대비1'].fillna(0)
        dfs['매수호가직전대비1'] = dfs['매수호가직전대비1'].fillna(0)
        dfs['매도호가직전대비2'] = dfs['매도호가직전대비2'].fillna(0)
        dfs['매수호가직전대비2'] = dfs['매수호가직전대비2'].fillna(0)
        dfs['매도호가직전대비3'] = dfs['매도호가직전대비3'].fillna(0)
        dfs['매수호가직전대비3'] = dfs['매수호가직전대비3'].fillna(0)
        dfs['매도호가직전대비4'] = dfs['매도호가직전대비3'].fillna(0)
        dfs['매수호가직전대비4'] = dfs['매수호가직전대비3'].fillna(0)
        dfs['매도호가직전대비5'] = dfs['매도호가직전대비3'].fillna(0)
        dfs['매수호가직전대비5'] = dfs['매수호가직전대비3'].fillna(0)
        dfs['매도호가직전대비6'] = dfs['매도호가직전대비3'].fillna(0)
        dfs['매수호가직전대비6'] = dfs['매수호가직전대비3'].fillna(0)
        dfs['매도호가직전대비7'] = dfs['매도호가직전대비3'].fillna(0)
        dfs['매수호가직전대비7'] = dfs['매수호가직전대비3'].fillna(0)
        dfs['매도호가직전대비8'] = dfs['매도호가직전대비3'].fillna(0)
        dfs['매수호가직전대비8'] = dfs['매수호가직전대비3'].fillna(0)
        dfs['매도호가직전대비9'] = dfs['매도호가직전대비3'].fillna(0)
        dfs['매수호가직전대비9'] = dfs['매수호가직전대비3'].fillna(0)
        dfs['매도호가직전대비10'] = dfs['매도호가직전대비3'].fillna(0)
        dfs['매수호가직전대비10'] = dfs['매수호가직전대비3'].fillna(0)

        dfs['매수호가총잔량직전대비'] = dfs['매수호가총잔량직전대비'].fillna(0)
        dfs['매도호가총잔량직전대비'] = dfs['매도호가총잔량직전대비'].fillna(0)

        print('fillna(0): ', time.time() - stime)

        # 나머지 column은 같은 종목코드을 기준으로 (필터링 필요) 직전 row값으로 대체.(체결강도 ; 호가시간 ;  매수호가1,2,3 ; 매도호가1,2,3 ; 매수호가수량1,2,3 ; 매도호가수량1,2,3 ;매수/매도호가 총잔량)
        # ['종목코드']column에서 종목을 추출하여 jongmok 리스트에 저장
        # jongmok = []
        save_row = None
        for row in dfs['종목코드']:
            if row != save_row:
                self.jongmok.append(row)
            save_row = row

        print('같은 종목기준 직전값으로 대체: ', time.time() -stime)

        # 덮어쓰지 말고 나중에 결국 종목별데이터를 만들려고 하는 code_data로 바로 저장해서 쓰면 안될까? 이 방향으로 정했다.
        # 즉, code_data ={}, code_data[jongmok[0]] = dfs[dfs['종목코드'] == code].fillna(method='ffill')
        code_data = {}
        for code in self.jongmok:
            # 앞방향으로 채우기한 후 맨앞쪽은 뒤방향으로 채우기

            # 아래 두줄은 20초 이상 소요된다. 덮어쓰기 때문에
            # dfs[dfs['종목코드'] == code] = dfs[dfs['종목코드'] == code].fillna(method='ffill')
            # dfs[dfs['종목코드'] == code] = dfs[dfs['종목코드'] == code].fillna(method='bfill')

            # 아래 두줄은 2초도 안 걸린다. 당연히 위 두줄처럼 할 필요가 없다.
            code_data[code] = dfs[dfs['종목코드'] == code].fillna(method='ffill')
            code_data[code] = code_data[code].fillna(method='bfill') #이렇게 해야 한다. 즉, ffill한 데이터를 다시 bfill

        print('앞방향 뒤방향 채우기: ', time.time() - stime)

        # 수신시간을 timedelta로 바꾼다. ==> 여러가지 유용       다음에 한다. 그래프그릴때 에러가 나서 사용하기 어렵다
        # dfs['수신시간dt'] = pd.to_datetime(dfs['수신시간'])

        # print('수신시간dt[0]타입;', type(dfs['수신시간dt'][0]))   # type : <class 'pandas._libs.tslibs.timestamps.Timestamp'>
        # print('dfs[수신시간dt]: ', dfs['수신시간dt'])
        # self.jongmok = jongmok


        # return dfs
        return code_data
    #######################################
    def clicked_act(self, event):
        self.xdata2 = event.xdata

        if event.xdata == None:  # 마우스 클릭한 위치가 그래프 좌표를 벗어난 경우
            return
        self.x_pos_nw = self.start_num + round(event.xdata)  # start_num은 index[num]이다.
        print('start_num, event.xdata:', self.start_num, int(event.xdata))

        self.new_window = NewWindow(self.x_pos_nw, self.code_data)
        if event.xdata < 25:
            self.new_window.move(1200,5)
        else:
            self.new_window.move(10,5)

        self.new_window.show()

        # self.day_chart()

    def day_chart(self):
        print('day_chart')
        # self.mykiwoom.ocx.dynamicCall("SetInputValue(QString, int, int)", '005930',1 , 1)
        # self.mykiwoom.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", '주식분봉차트조회', 'opt10080', 0, "1002")

class NewWindow(QMainWindow, hoga_window):
    def __init__(self, xpos, data):
        super(NewWindow, self).__init__()

        print('xdata 전달하기', xpos)

        self.setupUi(self)
        print('self???', self)
        # self.move(300,100)
        self.hoga_draw(xpos, data)

    def hoga_draw(self, xpos, data):
        # 매도호가 총잔량
        item_sell = format(int(data['매도호가총잔량'].loc[xpos]),',')
        item_sell = QTableWidgetItem(str(item_sell))
        item_sell.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
        self.tableWidget.setItem(21,1,item_sell )

        # 매수호가 총잔량
        item_sell = format(int(data['매수호가총잔량'].loc[xpos]),',')
        item_sell = QTableWidgetItem(str(item_sell))
        item_sell.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
        self.tableWidget.setItem(21,3,item_sell )

        for i in range(10):
            # 매도호가, 매도호가수량, 매도호가직전대비 입력
            hoga = '매도호가' + str(10-i)
            row = i + 1

            # 매도호가 천단위로 입력
            item_0 = format(int(data[hoga].loc[xpos]), ",")
            item_0 = QTableWidgetItem(str(item_0))
            item_0.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
            self.tableWidget.setItem(row,2,item_0)
            self.tableWidget.item(row, 2).setBackground(QtGui.QColor(0, 70, 100, 50))

            # 매도호가수량 천단위로 입력
            hoga_quant = "매도호가수량" + str(10-i)
            item_1 = format(int(data[hoga_quant].loc[xpos]), ",")
            item_1 = QTableWidgetItem(str(item_1))
            item_1.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
            self.tableWidget.setItem(row,1,item_1)

            # 매도호가 직전대비 입력
            hoga_daebi = "매도호가직전대비" + str(10-i)
            # item_2 = format(int(data[hoga_daebi])
            item_2 = QTableWidgetItem(str(int(data[hoga_daebi].loc[xpos])))
            item_2.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
            self.tableWidget.setItem(row,0,item_2)

            # 매수호가, 매수호가수량, 매수호가직전대비
            row = 20 - i

            # 매수호가 천단위로 입력
            hoga = '매수호가' + str(10-i)
            item_0 = format(int(data[hoga].loc[xpos]), ",")
            item_0 = QTableWidgetItem(str(item_0))
            item_0.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
            self.tableWidget.setItem(row,2,item_0)
            self.tableWidget.item(row, 2).setBackground(QtGui.QColor(100, 0, 0, 50))

            # 매수호가수량 천단위로 입력
            hoga_quant = "매수호가수량" + str(10-i)
            item_1 = format(int(data[hoga_quant].loc[xpos]), ",")
            item_1 = QTableWidgetItem(str(item_1))
            item_1.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
            self.tableWidget.setItem(row,3,item_1)

            # 매수호가직전대비 입력
            hoga_daebi = "매수호가직전대비" + str(10-i)
            item_2 = format(int(data[hoga_daebi].loc[xpos]), ",")
            item_2 = QTableWidgetItem(str(item_2))
            item_2.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
            self.tableWidget.setItem(row,4,item_2)

            # 체결내역 입력
            row = 11 + i    # 11번째 줄에서부터 입력해서 한줄씩 아래로..
            # xpos_m = xpos - i   # 현재값부터 입력하고 순차적으로 한칸씩 이전의 값을 입력  첫째값은 xpos와 동일 (-i는 0이므로)
            if xpos - i >= 0 :    # 최초 10번째 틱 이전을 클릭하면 -값이 나오므로 이를 제외 # 0보다 작으면 아무일도 하지 않음.
                # 매도체결, 매수체결은 순차적으로 나타나게 되어있다. 절대로 같이 나타나지 않는다. 그리고 nan값을 처리하기 위하여
                # 0으로 채워놓았으므로 여기서는 2개 중 0이 아닌 값을 선택해서 넣고 둘다 0이면 0으로 넣어야 한다.

                sign_sell = data['매도체결'].loc[xpos-i]
                sign_buy = data['매수체결'].loc[xpos-i]
                item_3 = None
                c = None
                if sign_sell == 0 and sign_buy == 0:
                    item_3 = str(int(0))
                    c = 'gray'
                else:
                    if sign_sell != 0:
                        item_3 = format(int(data['매도체결'].loc[xpos - i]), ",")
                        item_3 = "-" + str(item_3)
                        c = 'blue'
                    elif sign_buy != 0:
                        item_3 = format(int(data['매수체결'].loc[xpos - i]), ",")
                        item_3 = str(item_3)
                        c = 'red'

                item_3 = QTableWidgetItem(item_3)
                item_3.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
                self.tableWidget.setItem(row,1,item_3)
                if c == 'blue':
                    # self.tableWidget.item(row,1).setBackground(QtGui.QColor(0,100,100, 30))
                    self.tableWidget.item(row,1).setForeground(QtGui.QColor(0,0,255, 100))
                elif c == 'red':
                    self.tableWidget.item(row,1).setForeground(QtGui.QColor(250, 0, 0, 100))
                elif c == 'gray':
                    self.tableWidget.item(row,1).setForeground(QtGui.QBrush(Qt.gray))

            # 현재가 미수신상태 ==>수신한 후 코드 복원
            # item_4 = format(int(data['현재가'].loc[xpos-i]), ',')
            # item_4 = QTableWidgetItem(str(item_4))
            # item_4.setTextAlignment(int(Qt.AlignRight) | int(Qt.AlignVCenter))
            # self.tableWidget.setItem(row,1,item_4)
        # self.move(20, 10)
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        # elif e.key() == Qt.Key_F:
        #     self.showFullScreen()
        # elif e.key() == Qt.Key_N:
        #     self.showNormal()

        elif e.key() == Qt.Key_Left :       # Left라고 입력하니 안되던데, .프롬프터 창에서 key를 선택하고 - 입력후 또 창에서 선택하니 되더라.
            # self.close()
            mywindow.x_pos_nw -=1
            # self.new_window = NewWindow(mywindow.x_pos_nw, mywindow.code_data)
            # self.new_window.show()
            self.hoga_draw(mywindow.x_pos_nw, mywindow.code_data)

        elif e.key() == Qt.Key_Right :
            # self.close()
            mywindow.x_pos_nw +=1
            # self.new_window = NewWindow(mywindow.x_pos_nw, mywindow.code_data)
            # self.new_window.show()
            self.hoga_draw(mywindow.x_pos_nw, mywindow.code_data)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # mykiwoom = MyKiwoom()
    mywindow= Mywindow()
    app.exec_()



