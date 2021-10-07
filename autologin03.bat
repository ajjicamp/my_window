@echo off
cd C:\Users\USER\PycharmProjects\my_window
python login\autologin.py 3
python get_data\get_minute_data01.py 03 kosdaq
@echo "number2 process start"
@echo %ErrorLevel%
pause

