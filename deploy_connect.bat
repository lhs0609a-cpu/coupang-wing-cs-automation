@echo off
REM Vercel + Fly.io 자동 연결 배포 스크립트

echo ========================================================================
echo   Vercel ⭐⭐⭐⭐⭐ + Fly.io ⭐⭐⭐⭐⭐ 자동 연결 배포
echo ========================================================================
echo.

REM 색상 설정을 위한 ANSI 코드 (Windows 10 이상)
setlocal EnableDelayedExpansion

REM 1. 사전 확인
echo [1/5] 사전 확인 중...
echo.

REM Fly CLI 확인
where fly >nul 2>nul
if %errorlevel% neq 0 (
    echo [오류] Fly CLI가 설치되어 있지 않습니다.
    echo.
    echo 설치 방법 (PowerShell 관리자 권한):
    echo   iwr https://fly.io/install.ps1 -useb ^| iex
    echo.
    pause
    exit /b 1
)
echo ✓ Fly CLI 설치됨

REM Vercel CLI 확인
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo [오류] Vercel CLI가 설치되어 있지 않습니다.
    echo.
    echo 설치 방법:
    echo   npm install -g vercel
    echo.
    pause
    exit /b 1
)
echo ✓ Vercel CLI 설치됨
echo.

REM 2. Fly.io 로그인 확인
echo [2/5] Fly.io 로그인 확인 중...
echo.

fly auth whoami >nul 2>nul
if %errorlevel% neq 0 (
    echo Fly.io에 로그인되어 있지 않습니다.
    echo 브라우저가 열립니다. 로그인해주세요.
    echo.
    fly auth login
    if %errorlevel% neq 0 (
        echo [오류] Fly.io 로그인 실패
        pause
        exit /b 1
    )
)
echo ✓ Fly.io 로그인됨
echo.

REM 3. 백엔드 배포 (Fly.io)
echo [3/5] 백엔드를 Fly.io에 배포 중...
echo ========================================================================
echo.

cd backend

REM 환경변수 설정 확인
echo 환경변수를 설정해야 합니다.
echo.
set /p OPENAI_KEY="OpenAI API Key를 입력하세요 (sk-...): "

if "%OPENAI_KEY%"=="" (
    echo [오류] OpenAI API Key가 필요합니다.
    pause
    exit /b 1
)

echo.
echo 환경변수 설정 중...
fly secrets set OPENAI_API_KEY="%OPENAI_KEY%"
fly secrets set DATABASE_URL="sqlite:///./database/coupang_cs.db"
fly secrets set SECRET_KEY="change-this-super-secret-key-in-production"
fly secrets set ENVIRONMENT="production"
fly secrets set LOG_LEVEL="INFO"

echo.
echo 백엔드 배포 중... (5-10분 소요될 수 있습니다)
echo.

fly deploy
if %errorlevel% neq 0 (
    echo [오류] 백엔드 배포 실패!
    cd ..
    pause
    exit /b 1
)

echo.
echo ✓ 백엔드 배포 완료!
echo.

REM 백엔드 URL 확인
for /f "tokens=*" %%i in ('fly status --json ^| findstr "Hostname"') do set BACKEND_INFO=%%i
echo 백엔드 URL 정보: %BACKEND_INFO%
echo.

REM 사용자에게 백엔드 URL 입력 받기
echo 배포된 백엔드 URL을 입력하세요.
echo 예: coupang-wing-cs.fly.dev (https:// 제외, 끝의 / 제외)
set /p BACKEND_URL="백엔드 URL: "

if "%BACKEND_URL%"=="" (
    echo [경고] URL을 입력하지 않았습니다. 기본값 사용: your-backend-app.fly.dev
    set BACKEND_URL=your-backend-app.fly.dev
)

echo.
echo 백엔드 URL: https://%BACKEND_URL%
echo.

cd ..

REM 4. 프론트엔드 설정 업데이트
echo [4/5] 프론트엔드 설정 업데이트 중...
echo.

cd frontend

REM .env.production 업데이트
echo VITE_API_URL=https://%BACKEND_URL% > .env.production
echo ✓ .env.production 업데이트 완료

REM vercel.json 업데이트는 수동으로 해야 함 (복잡한 JSON 파싱 필요)
echo.
echo [중요] vercel.json 파일을 수동으로 업데이트하세요:
echo   파일: frontend\vercel.json
echo   변경: "your-backend-app.fly.dev" → "%BACKEND_URL%"
echo.
pause

REM 빌드 테스트
echo 프론트엔드 빌드 테스트 중...
call npm run build
if %errorlevel% neq 0 (
    echo [오류] 빌드 실패!
    cd ..
    pause
    exit /b 1
)
echo ✓ 빌드 성공
echo.

REM 5. Vercel 배포
echo [5/5] 프론트엔드를 Vercel에 배포 중...
echo ========================================================================
echo.

REM Vercel 로그인 확인
vercel whoami >nul 2>nul
if %errorlevel% neq 0 (
    echo Vercel에 로그인되어 있지 않습니다.
    echo 브라우저가 열립니다. 로그인해주세요.
    echo.
    vercel login
    if %errorlevel% neq 0 (
        echo [오류] Vercel 로그인 실패
        cd ..
        pause
        exit /b 1
    )
)

echo 프론트엔드 배포 중...
echo.

vercel --prod
if %errorlevel% neq 0 (
    echo [오류] 프론트엔드 배포 실패!
    cd ..
    pause
    exit /b 1
)

echo.
echo ✓ 프론트엔드 배포 완료!
echo.

cd ..

REM 완료
echo ========================================================================
echo   배포 완료!
echo ========================================================================
echo.
echo 백엔드 URL:
echo   - 메인: https://%BACKEND_URL%
echo   - 헬스체크: https://%BACKEND_URL%/health
echo   - API 문서: https://%BACKEND_URL%/docs
echo.
echo 프론트엔드 URL:
echo   - 위의 Vercel 출력에서 확인하세요
echo.
echo 다음 단계:
echo   1. 프론트엔드 URL로 접속
echo   2. ChatGPT 연결 상태 확인
echo   3. 모든 페이지 테스트
echo.
echo Vercel Dashboard에서 환경변수도 추가하세요:
echo   https://vercel.com/dashboard
echo   Settings ^> Environment Variables
echo   VITE_API_URL = https://%BACKEND_URL%
echo.
echo ========================================================================
echo.

pause
