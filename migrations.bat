@echo off
setlocal

title Installation Kivu SuperMarket

echo ============================================================
echo             KIVU SUPERMARKET - INSTALLATION
echo ============================================================
echo.

cd /d "C:\market-app\kivu"

if errorlevel 1 (
    echo [ERREUR] Impossible d'acceder a C:\market-app\kivu
    pause
    exit /b 1
)

echo Dossier du projet :
echo %CD%
echo.

if not exist "manage.py" (
    echo [ERREUR] manage.py est introuvable dans :
    echo C:\market-app\kivu
    echo.
    pause
    exit /b 1
)

echo [OK] Projet Django detecte.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv

    if errorlevel 1 (
        echo [ERREUR] Impossible de creer le .venv.
        pause
        exit /b 1
    )
)

echo Activation du .venv...
call ".venv\Scripts\activate.bat"

echo.
echo Mise a jour de pip...
python -m pip install --upgrade pip

if errorlevel 1 (
    echo [ERREUR] Echec de la mise a jour de pip.
    pause
    exit /b 1
)

echo.

if exist "requirements.txt" (
    echo Installation des dependances...
    python -m pip install -r requirements.txt

    if errorlevel 1 (
        echo [ERREUR] Installation des dependances echouee.
        pause
        exit /b 1
    )
) else (
    echo [AVERTISSEMENT] requirements.txt introuvable.
)

echo.
echo Creation des migrations...
python manage.py makemigrations

if errorlevel 1 (
    echo [ERREUR] makemigrations a echoue.
    pause
    exit /b 1
)

echo.
echo Application des migrations...
python manage.py migrate

if errorlevel 1 (
    echo [ERREUR] migrate a echoue.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo              CREATION DU SUPERUTILISATEUR
echo ============================================================
echo.

python manage.py createsuperuser

if errorlevel 1 (
    echo.
    echo [ERREUR] Creation du superutilisateur echouee.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo                 INSTALLATION TERMINEE
echo ============================================================
echo.
echo Projet       : C:\market-app\kivu
echo Dependances  : OK
echo Migrations   : OK
echo Base de donnees : OK
echo Superuser    : OK
echo.
echo Pour lancer le projet :
echo.
echo     .venv\Scripts\activate
echo     python manage.py runserver
echo.
echo ============================================================

pause
exit /b 0