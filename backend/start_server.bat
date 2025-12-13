@echo off
echo 🚀 쿠팡 윙 CS 자동화 서버 시작...
echo.

cd /d E:\u\coupang-wing-cs-automation\backend

echo 📦 가상환경 활성화...
call venv\Scripts\activate.bat

echo 🔄 데이터베이스 마이그레이션...
python migrate_db.py

echo.
echo 🌐 서버 시작 (포트 8000)...
echo 📖 Swagger UI: http://localhost:8000/docs
echo 🛑 종료하려면 Ctrl+C를 누르세요
echo.

python -m uvicorn app.main:app --reload --port 8000
