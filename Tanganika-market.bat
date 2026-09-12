@echo off
cd /d "C:\market-app\kivu"

call ".venv\Scripts\activate.bat"

python manage.py runserver 0.0.0.0:8000

pause