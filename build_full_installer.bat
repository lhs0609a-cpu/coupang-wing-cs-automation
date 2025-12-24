@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   완전 자동 설치 패키지 빌드 스크립트
echo ============================================================
echo.

set "SOURCE_DIR=%~dp0"
set "TARGET_DIR=%~dp0CoupangWingCS_FullAutoInstaller"
set "APP_DIR=%TARGET_DIR%\app"

echo [확인] 소스 디렉토리: %SOURCE_DIR%
echo [확인] 타겟 디렉토리: %TARGET_DIR%
echo.

:: ========================================
:: App 폴더 생성
:: ========================================
echo [작업] app 폴더 생성 중...

if exist "%APP_DIR%" (
    echo [삭제] 기존 app 폴더 삭제 중...
    rmdir /s /q "%APP_DIR%"
)

mkdir "%APP_DIR%"
echo [완료] app 폴더 생성 완료
echo.

:: ========================================
:: Backend 복사
:: ========================================
echo [복사] Backend 폴더 복사 중...

if exist "%SOURCE_DIR%backend" (
    xcopy /E /I /Y /Q "%SOURCE_DIR%backend" "%APP_DIR%\backend"
    echo [완료] Backend 폴더 복사 완료
) else (
    echo [오류] backend 폴더를 찾을 수 없습니다!
    pause
    exit /b 1
)
echo.

:: ========================================
:: Frontend 복사
:: ========================================
echo [복사] Frontend 폴더 복사 중...

if exist "%SOURCE_DIR%frontend" (
    xcopy /E /I /Y /Q "%SOURCE_DIR%frontend" "%APP_DIR%\frontend"
    echo [완료] Frontend 폴더 복사 완료
) else (
    echo [오류] frontend 폴더를 찾을 수 없습니다!
    pause
    exit /b 1
)
echo.

:: ========================================
:: Launcher 파일 복사
:: ========================================
echo [복사] Launcher 파일 복사 중...

if exist "%TARGET_DIR%\launcher_final.py" (
    copy /Y "%TARGET_DIR%\launcher_final.py" "%APP_DIR%\launcher.py"
    echo [완료] Launcher 파일 복사 완료
) else (
    echo [경고] launcher_final.py를 찾을 수 없습니다!
)
echo.

:: ========================================
:: README 파일 생성
:: ========================================
echo [생성] README 파일 생성 중...

(
echo ============================================================
echo   쿠팡 윙 CS 자동화 시스템 v3.0.0
echo   완전 자동 설치 및 실행 버전
echo ============================================================
echo.
echo 사용 방법:
echo   1. START.bat 파일을 더블클릭하세요
echo   2. 자동으로 필요한 프로그램이 설치됩니다
echo   3. 설치 완료 후 자동으로 프로그램이 실행됩니다
echo.
echo 시스템 요구사항:
echo   - Windows 10 이상
echo   - 인터넷 연결 (최초 설치 시)
echo   - 디스크 여유 공간 약 500MB
echo.
echo 설치되는 프로그램:
echo   - Python 3.11.9 ^(임베디드 버전^)
echo   - Node.js 20.18.1 ^(포터블 버전^)
echo   - 모든 필수 Python 패키지
echo   - 모든 필수 npm 패키지
echo.
echo 문제 해결:
echo   - 방화벽 경고가 나타나면 '액세스 허용'을 클릭하세요
echo   - 설치 중 오류가 발생하면 관리자 권한으로 실행해보세요
echo   - 포트 8000-8009가 사용 중이면 다른 프로그램을 종료하세요
echo.
echo 제작: CoupangWingCS Team
echo 버전: 3.0.0
echo 날짜: 2025-10-31
echo ============================================================
) > "%TARGET_DIR%\README.txt"

echo [완료] README 파일 생성 완료
echo.

:: ========================================
:: 배포 패키지 검증
:: ========================================
echo [검증] 배포 패키지 검증 중...
echo.

set "VALID=1"

if not exist "%TARGET_DIR%\START.bat" (
    echo [오류] START.bat이 없습니다!
    set "VALID=0"
)

if not exist "%TARGET_DIR%\install_python.bat" (
    echo [오류] install_python.bat이 없습니다!
    set "VALID=0"
)

if not exist "%TARGET_DIR%\install_nodejs.bat" (
    echo [오류] install_nodejs.bat이 없습니다!
    set "VALID=0"
)

if not exist "%TARGET_DIR%\install_dependencies.bat" (
    echo [오류] install_dependencies.bat이 없습니다!
    set "VALID=0"
)

if not exist "%APP_DIR%\backend" (
    echo [오류] app\backend 폴더가 없습니다!
    set "VALID=0"
)

if not exist "%APP_DIR%\frontend" (
    echo [오류] app\frontend 폴더가 없습니다!
    set "VALID=0"
)

if "%VALID%"=="0" (
    echo.
    echo [오류] 배포 패키지에 문제가 있습니다!
    pause
    exit /b 1
)

echo [완료] 모든 파일이 정상적으로 준비되었습니다!
echo.

:: ========================================
:: 완료
:: ========================================
echo ============================================================
echo   빌드 완료!
echo ============================================================
echo.
echo   배포 폴더: %TARGET_DIR%
echo.
echo   이제 'CoupangWingCS_FullAutoInstaller' 폴더를
echo   다른 컴퓨터에 복사하여 START.bat을 실행하면 됩니다!
echo.
echo ============================================================
echo.

pause
