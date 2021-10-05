import pywinauto
from pywinauto.application import Application

app = Application(backend="uia").start('notepad.exe')  # process 실행
procs = pywinauto.findwindows.find_elements()

for proc in procs:
    print(proc, proc.process_id)
    # if proc.name == '*제목 없음 - Windows 메모장':
    #     break
# app = Application(backend="uia").connect(process=proc.process_id) # process 연결
# app = Application(backend='uia').connect(title="*제목 없음 - Windows 메모장")