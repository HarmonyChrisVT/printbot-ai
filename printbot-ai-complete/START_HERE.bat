@echo off
echo ==========================================
echo   PRINTBOT AI - AUTOMATED STORE SYSTEM
echo ==========================================
echo.
echo This will set up everything automatically!
echo.
echo Step 1: Checking Python installation...

python --version
if errorlevel 1 (
    echo.
    echo Python not found! Please install Python 3.11 from python.org
    echo Then run this file again.
    echo.
    pause
    exit /b
)

echo.
echo Python found! Continuing setup...
echo.
echo Step 2: Installing required packages...
echo This may take a few minutes...
echo.

cd app
pip install -r requirements.txt

echo.
echo Step 3: Setting up database...
python -c "from database.models import init_db; init_db()"

echo.
echo ==========================================
echo   SETUP COMPLETE!
echo ==========================================
echo.
echo Starting the dashboard...
echo.
echo The dashboard will open in your browser at:
echo http://localhost:3000
echo.
echo Press CTRL+C to stop the server
echo.

start http://localhost:3000
python main.py

pause
