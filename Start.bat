@echo off
cd \
cd kivu
cd facture

if not exist mediafiles mkdir mediafiles
cd mediafiles
if not exist facture mkdir facture

python manage.py retrieve_profile    
python manage.py runserver 0.0.0.0:80