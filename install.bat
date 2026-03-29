@echo off
chcp 65001 >nul
title PrintBot AI - Auto Installer
color 0A

echo ==========================================
echo    PrintBot AI - Automatic Installer
echo ==========================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Please run this file as Administrator!
    echo Right-click on install.bat and select "Run as administrator"
    pause
    exit /b 1
)

:: Check if Python is installed
echo 🔍 Checking for Python...
python --version >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Python is already installed
    python --version
    goto :PYTHON_OK
)

:: Download and install Python
echo 📥 Python not found. Downloading Python 3.11...
echo This may take a few minutes...

:: Download Python installer
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"

if not exist "%TEMP%\python_installer.exe" (
    echo ❌ Failed to download Python
    echo Please manually install Python from https://python.org/downloads
    pause
    exit /b 1
)

:: Install Python
echo 🔧 Installing Python (this may take a few minutes)...
start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: Clean up
del "%TEMP%\python_installer.exe"

:: Verify installation
echo 🔍 Verifying Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python installation failed
    echo Please manually install Python from https://python.org/downloads
    pause
    exit /b 1
)

echo ✅ Python installed successfully!
python --version

:PYTHON_OK
echo.
echo ==========================================
echo    Installing Dependencies
echo ==========================================
echo.

:: Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo 📦 Installing required packages...
if exist "python\requirements.txt" (
    pip install -r python\requirements.txt
) else (
    echo ❌ requirements.txt not found!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo    Creating Environment File
echo ==========================================
echo.

if not exist ".env" (
    if exist ".env.example" (
        echo 📝 Creating .env file from template...
        copy .env.example .env
        echo ✅ .env file created!
        echo.
        echo ⚠️  IMPORTANT: Edit .env file with your API keys!
        echo    - Shopify Store URL
        echo    - Shopify Admin API Token
        echo    - Printful API Key
        echo    - OpenAI API Key
    ) else (
        echo ⚠️  .env.example not found. You'll need to create .env manually.
    )
) else (
    echo ✅ .env file already exists
)

echo.
echo ==========================================
echo    Setup Complete!
echo ==========================================
echo.
echo 🎉 PrintBot AI is ready!
echo.
echo Next steps:
echo 1. Edit the .env file with your API keys
echo 2. Run: python start.py
echo 3. Open: http://localhost:8080
echo.
echo Need help getting API keys?
echo Visit: https://nkzoe4rayvwts.ok.kimi.link/setup.html
echo.
pause
