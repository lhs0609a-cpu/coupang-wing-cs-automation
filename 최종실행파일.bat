@echo off
cls

python "최종실행파일.py"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to run launcher
    echo Check if Python is installed
    pause
)

exit
