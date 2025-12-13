@echo off
title Vercel 배포
color 0A

echo.
echo ========================================================
echo     🚀 Vercel 프로덕션 배포
echo     Deploying to Vercel Production
echo ========================================================
echo.

cd /d E:\u\coupang-wing-cs-automation\frontend

echo [1/2] 프로덕션 빌드 중...
call npm run build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 빌드 실패!
    pause
    exit /b 1
)

echo.
echo [2/2] Vercel에 배포 중...
call vercel --prod

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 배포 실패!
    pause
    exit /b 1
)

echo.
echo ========================================================
echo ✅ 배포 완료!
echo.
echo 🌐 프로젝트: naver-pay-delivery-tracker
echo 📡 백엔드: https://coupang-wing-cs-backend.fly.dev
echo.
echo 배포 URL은 위 출력에서 확인하세요!
echo ========================================================
echo.

pause
