@echo off
cd /d "C:\market-app\kivu"

call ".venv\Scripts\activate.bat"

waitress-serve --listen=0.0.0.0:8000 facture.wsgi:application  

pause