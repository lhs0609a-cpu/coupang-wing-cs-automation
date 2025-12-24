@echo off
chcp 65001 >nul
echo.
echo ====================================
echo 계정 세트 테이블 생성
echo ====================================
echo.

venv\Scripts\python.exe migrate_account_sets.py

echo.
pause
