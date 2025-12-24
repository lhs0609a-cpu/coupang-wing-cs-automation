@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ==========================================
echo   쿠팡 윙 CS 자동화 시스템 v2.0.0
echo ==========================================
echo.
echo 서버를 시작합니다...
echo.
CoupangWingCS_Server.exe
pause
