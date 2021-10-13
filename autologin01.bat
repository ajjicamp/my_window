@echo off
cd c:\Users\USER\PycharmProjects\my_window
python login\autologin.py 2
python trader\mainwindow.py
@echo "number1 process start"
@echo %ErrorLevel%
pause
