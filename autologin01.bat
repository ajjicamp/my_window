@echo off
:repeat
Timeout 2

@tasklist | find "python get_data\get_minute_data01.py"
IF %ErrorLevel%==1 goto 1
IF NOT %ErrorLevel%==1 goto 0

:0
@echo errorlevel %ErrorLevel%
goto repeat

:1
@echo errorlevel %ErrorLevel%
cd C:\Users\USER\PycharmProjects\my_window
python login\autologin.py 1
python get_data\get_minute_data01.py 01 kosdaq
@echo "number2 process terminated"
goto repeat
pause

