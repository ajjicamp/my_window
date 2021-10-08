@echo off
cd c:\Users\USER\PycharmProjects\my_window
python login\autologin.py 4
python get_data\get_minute_data01.py 04 kosdaq
@echo "number1 process start"
@echo %ErrorLevel%
pause
