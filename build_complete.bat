@echo off
chcp 65001 > nul
title Coupang Wing CS - Build Executable v3.0 (COMPLETE)

echo.
echo ======================================================================
echo   Coupang Wing CS - Executable Builder v3.0 (COMPLETE)
echo   Includes ALL required modules: loguru, apscheduler, selenium, etc.
echo ======================================================================
echo.

REM Check Python
echo [Check 1/3] Checking Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    pause
    exit /b 1
)

python --version
echo           OK
echo.

REM Check backend folder
echo [Check 2/3] Checking backend folder...
if not exist "backend" (
    echo.
    echo [ERROR] backend folder not found!
    echo.
    pause
    exit /b 1
)
echo           Found!
echo.

REM Check/Create virtual environment
echo [Check 3/3] Checking virtual environment...
if not exist "venv" (
    echo           Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to create virtual environment
        echo.
        pause
        exit /b 1
    )
    echo           Created!
) else (
    echo           Exists!
)
echo.

echo ======================================================================
echo   Installing dependencies...
echo ======================================================================
echo.

REM Activate venv
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo [1/2] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo       Done!
echo.

REM Install requirements
echo [2/2] Installing requirements (this may take a few minutes)...
pip install -r backend\requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install requirements
    echo.
    pause
    exit /b 1
)
echo       Done!
echo.

echo ======================================================================
echo   Starting COMPLETE build process...
echo   This version includes ALL required modules!
echo ======================================================================
echo.

REM Run COMPLETE build script
python build_executable_complete.py

REM Deactivate
call deactivate 2>nul

echo.
echo ======================================================================
pause
