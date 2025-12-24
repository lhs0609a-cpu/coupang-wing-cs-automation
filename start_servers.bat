@echo off
chcp 65001 >nul
echo ====================================
echo 쿠팡윙 CS 자동화 서버 시작
echo ====================================
echo.

REM 현재 실행 중인 서버 종료
echo [1/4] 기존 서버 종료 중...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo   포트 8000 사용 중인 프로세스 종료: %%a
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo   포트 3000 사용 중인 프로세스 종료: %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo   완료!
echo.

REM 데이터베이스 계정 확인
echo [2/4] 데이터베이스 계정 확인 중...
venv\Scripts\python.exe check_accounts.py
echo.

REM 백엔드 서버 시작
echo [3/4] 백엔드 서버 시작 중...
echo   URL: http://localhost:8000
start "쿠팡윙 CS 백엔드" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
echo   완료!
echo.

REM 프론트엔드 서버 시작
echo [4/4] 프론트엔드 서버 시작 중...
echo   URL: http://localhost:3000
start "쿠팡윙 CS 프론트엔드" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 /nobreak >nul
echo   완료!
echo.

echo ====================================
echo 서버 시작 완료!
echo ====================================
echo.
echo 백엔드: http://localhost:8000
echo 프론트엔드: http://localhost:3000
echo API 문서: http://localhost:8000/docs
echo.
echo 브라우저에서 http://localhost:3000 을 열어보세요.
echo.
pause
