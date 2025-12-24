@echo off
chcp 65001 >nul
echo ====================================
echo 쿠팡윙 CS 자동화 배포 스크립트
echo ====================================
echo.

echo [1/4] 프론트엔드 빌드 중...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo 프론트엔드 패키지 설치 실패!
    pause
    exit /b 1
)

call npm run build
if %errorlevel% neq 0 (
    echo 프론트엔드 빌드 실패!
    pause
    exit /b 1
)
cd ..
echo 프론트엔드 빌드 완료!
echo.

echo [2/4] Vercel 프론트엔드 배포 중...
echo 배포 URL: https://frontend-fkv6mtyud-fewfs-projects-83cc0821.vercel.app
call vercel --prod
if %errorlevel% neq 0 (
    echo Vercel 배포 실패!
    pause
    exit /b 1
)
echo 프론트엔드 배포 완료!
echo.

echo [3/4] Fly.io 백엔드 배포 준비 중...
echo 백엔드 URL: https://coupang-wing-cs-backend.fly.dev

REM Fly.io 로그인 확인
powershell -Command "& ''C:\Users\u\.fly\bin\flyctl.exe'' auth whoami" >nul 2>&1
if %errorlevel% neq 0 (
    echo Fly.io 로그인이 필요합니다.
    powershell -Command "& ''C:\Users\u\.fly\bin\flyctl.exe'' auth login"
)

echo [4/4] Fly.io 백엔드 배포 중...
powershell -Command "& ''C:\Users\u\.fly\bin\flyctl.exe'' deploy -a coupang-wing-cs-backend"
if %errorlevel% neq 0 (
    echo Fly.io 배포 실패!
    pause
    exit /b 1
)
echo.

echo ====================================
echo 배포 완료!
echo ====================================
echo.
echo 프론트엔드: https://frontend-fkv6mtyud-fewfs-projects-83cc0821.vercel.app
echo 백엔드: https://coupang-wing-cs-backend.fly.dev
echo.
echo 배포 상태 확인:
powershell -Command "& ''C:\Users\u\.fly\bin\flyctl.exe'' status -a coupang-wing-cs-backend"
echo.
pause
