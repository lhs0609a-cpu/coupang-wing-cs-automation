@echo off
echo 🚀 쿠팡 윙 CS 자동화 프론트엔드 시작...
echo.

cd /d E:\u\coupang-wing-cs-automation\frontend

echo 📦 의존성 설치 확인...
if not exist "node_modules" (
    echo 📥 의존성 설치 중...
    call npm install
)

echo.
echo 🌐 프론트엔드 서버 시작 (포트 3000)...
echo 🌍 브라우저: http://localhost:3000
echo 🛑 종료하려면 Ctrl+C를 누르세요
echo.

npm run dev
