@echo off
cd C:\Users\USER\PycharmProjects\my_window
python login\autologin.py 2
python get_data\get_minute_data02.py 02 kosdaq
@echo "number2 process start"
@echo %ErrorLevel%
pause

