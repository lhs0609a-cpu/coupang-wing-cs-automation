@echo off
cd /d E:\u\coupang-wing-cs-automation\backend
echo Starting backend server on port 8001...
C:\Python314\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
pause
