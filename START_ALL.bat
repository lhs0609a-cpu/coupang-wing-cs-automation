@echo off
title 쿠팡 윙 CS 자동화 시스템 시작
color 0A

echo.
echo ========================================================
echo     🤖 쿠팡 윙 CS 자동화 시스템
echo     Coupang Wing CS Automation System
echo ========================================================
echo.
echo 🚀 시스템을 시작합니다...
echo.

REM 백엔드 서버 시작
echo [1/2] 백엔드 서버 시작 중...
start "백엔드 서버 (포트 8000)" cmd /k "cd /d E:\u\coupang-wing-cs-automation\backend && start_server.bat"

REM 3초 대기
timeout /t 3 /nobreak >nul

REM 프론트엔드 서버 시작
echo [2/2] 프론트엔드 서버 시작 중...
start "프론트엔드 서버 (포트 3000)" cmd /k "cd /d E:\u\coupang-wing-cs-automation\frontend && start_frontend.bat"

echo.
echo ========================================================
echo ✅ 시스템이 시작되었습니다!
echo.
echo 📡 백엔드 API: http://localhost:8000
echo 📖 API 문서: http://localhost:8000/docs
echo 🌐 프론트엔드: http://localhost:3000
echo.
echo 💡 잠시 후 브라우저에서 http://localhost:3000 접속하세요
echo 🛑 종료하려면 각 서버 창에서 Ctrl+C를 누르세요
echo ========================================================
echo.

REM 5초 대기 후 브라우저 열기
timeout /t 5 /nobreak >nul
start http://localhost:3000

pause
