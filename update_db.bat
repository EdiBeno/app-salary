@echo off
set FLASK_APP=main.py
flask db migrate -m "Auto migration"
flask db upgrade
pause
