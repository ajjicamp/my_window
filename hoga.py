# 호가창을 업데이트하는 모듈

class HogaUpdate:
    def __init__(self, hogaQ):
        self.hogaQ = hogaQ

    def start(self):
        while True:
            if not self.hogaQ.empty():
                hoga = self.hogaQ.get()
                print("hoga\n", hoga)
