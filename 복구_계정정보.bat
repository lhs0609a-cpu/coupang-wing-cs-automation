@echo off
chcp 65001 >nul
echo.
echo ====================================
echo 계정 정보 복구
echo ====================================
echo.
echo .env 파일의 계정 정보를 데이터베이스에 저장합니다...
echo.

venv\Scripts\python.exe init_accounts.py

echo.
echo 완료! 아무 키나 누르면 종료됩니다.
pause
