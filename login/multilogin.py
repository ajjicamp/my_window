from autologin import

for x, par in enumerate(sys.argv):
    print('param', x, par)
num = int(sys.argv[1])
# num = 3
print(type(num), num)
login_info = f'{openapi_path}/system/Autologin.dat'
print('login_info', login_info)
if os.path.isfile(login_info):
    os.remove(f'{openapi_path}/system/Autologin.dat')
print('\n 자동 로그인 설정 파일 삭제 완료\n')
if num == 1 or num == 2:  # 첫번째계정 모의서버(1), 실서버(2)
    gubun = 1  # 첫번째 계정
elif num == 3 or num == 4:  # 두번째계정 모의서버(3), 실서버(4)
    gubun = 2  # 두번째 계정
p = Process(target=Window, args=(gubun,))  # 여기 gubun은 auto_on(gubun)으로 사용됨.
p.start()
# p.join()
print(' 자동 로그인 설정용 프로세스 시작\n')