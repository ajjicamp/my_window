# 호가창을 업데이트하는 모듈

class Hoga:
    def __init__(self, windwowQ, hogaQ):
        self.windowQ = windwowQ
        self.hogaQ = hogaQ

        self.start()

    def start(self):
        while True:
            if not self.hogaQ.empty():
                hoga = self.hogaQ.get()
                output = ['호가갱신', hoga[1]]
                self.windowQ.put(output)
                # print("hoga", hoga[0], hoga[1])
                print('hogaQ size: ', self.hogaQ.qsize())
