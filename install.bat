@echo off
chcp 65001 > nul
REM ====================================================================
REM Coupang Wing CS 자동화 시스템 - 자동 설치 스크립트 (Windows)
REM ====================================================================

echo.
echo ====================================================================
echo 🚀 Coupang Wing CS 자동화 시스템 설치
echo ====================================================================
echo.

REM 관리자 권한 확인 (선택적)
REM net session >nul 2>&1
REM if %errorLevel% neq 0 (
REM     echo ⚠️  관리자 권한이 필요할 수 있습니다.
REM )

REM ====================================================================
REM 1단계: Python 버전 확인
REM ====================================================================
echo [1/8] Python 버전 확인 중...

python --version > nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo.
    echo 💡 Python 3.8 이상을 설치해주세요:
    echo    https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Python 버전 출력
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% 발견

REM 버전 확인 (3.8 이상)
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo ❌ Python 3.8 이상이 필요합니다. 현재: %PYTHON_VERSION%
    pause
    exit /b 1
)

if %MAJOR% EQU 3 if %MINOR% LSS 8 (
    echo ❌ Python 3.8 이상이 필요합니다. 현재: %PYTHON_VERSION%
    pause
    exit /b 1
)

REM ====================================================================
REM 2단계: pip 업그레이드
REM ====================================================================
echo.
echo [2/8] pip 업그레이드 중...
python -m pip install --upgrade pip --quiet
if %errorLevel% neq 0 (
    echo ⚠️  pip 업그레이드 실패 (계속 진행)
) else (
    echo ✅ pip 업그레이드 완료
)

REM ====================================================================
REM 3단계: 가상환경 생성 (선택적)
REM ====================================================================
echo.
echo [3/8] 가상환경 확인 중...

if not exist "backend\venv" (
    echo 📦 가상환경 생성 중...
    python -m venv backend\venv
    if %errorLevel% neq 0 (
        echo ⚠️  가상환경 생성 실패 (전역 환경에 설치됩니다)
    ) else (
        echo ✅ 가상환경 생성 완료
    )
) else (
    echo ✅ 가상환경이 이미 존재합니다
)

REM 가상환경 활성화 (있는 경우)
if exist "backend\venv\Scripts\activate.bat" (
    echo 🔧 가상환경 활성화 중...
    call backend\venv\Scripts\activate.bat
)

REM ====================================================================
REM 4단계: 의존성 설치
REM ====================================================================
echo.
echo [4/8] 패키지 설치 중...
echo    (시간이 걸릴 수 있습니다...)

if not exist "backend\requirements.txt" (
    echo ❌ requirements.txt 파일이 없습니다.
    pause
    exit /b 1
)

python -m pip install -r backend\requirements.txt --quiet
if %errorLevel% neq 0 (
    echo ❌ 패키지 설치 실패
    echo.
    echo 💡 다시 시도하거나 수동으로 설치하세요:
    echo    pip install -r backend\requirements.txt
    echo.
    pause
    exit /b 1
)

echo ✅ 패키지 설치 완료

REM ====================================================================
REM 5단계: 환경 변수 파일 생성
REM ====================================================================
echo.
echo [5/8] 환경 설정 중...

if not exist "backend\.env" (
    if exist "backend\.env.example" (
        echo 📝 .env 파일 생성 중...
        copy "backend\.env.example" "backend\.env" > nul
        echo ✅ .env 파일 생성 완료
        echo.
        echo ⚠️  중요: backend\.env 파일을 열어 다음 항목을 설정하세요:
        echo    - OPENAI_API_KEY: OpenAI API 키
        echo    - 기타 필요한 설정
        echo.
    ) else (
        echo ⚠️  .env.example 파일이 없습니다.
        echo    수동으로 .env 파일을 생성해주세요.
    )
) else (
    echo ✅ .env 파일이 이미 존재합니다
)

REM ====================================================================
REM 6단계: 필수 폴더 생성
REM ====================================================================
echo.
echo [6/8] 필수 폴더 생성 중...

if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "error_reports" mkdir error_reports
if not exist "backend\logs" mkdir backend\logs

echo ✅ 폴더 생성 완료

REM ====================================================================
REM 7단계: 데이터베이스 초기화
REM ====================================================================
echo.
echo [7/8] 데이터베이스 초기화 중...

REM 데이터베이스가 없는 경우에만 초기화
if not exist "backend\coupang_wing.db" (
    python -c "import sys; sys.path.insert(0, 'backend'); from app.database import init_db; init_db()"
    if %errorLevel% neq 0 (
        echo ⚠️  데이터베이스 초기화 실패 (나중에 자동으로 생성됩니다)
    ) else (
        echo ✅ 데이터베이스 초기화 완료
    )
) else (
    echo ✅ 데이터베이스가 이미 존재합니다
)

REM ====================================================================
REM 8단계: 자가 진단 실행
REM ====================================================================
echo.
echo [8/8] 시스템 자가 진단 중...

if exist "health_check.py" (
    python health_check.py
    if %errorLevel% neq 0 (
        echo.
        echo ⚠️  자가 진단에서 일부 문제가 발견되었습니다.
        echo    health_check_report.txt를 확인하세요.
        echo.
    )
) else (
    echo ⚠️  health_check.py 파일이 없습니다. (건너뜀)
)

REM ====================================================================
REM 완료
REM ====================================================================
echo.
echo ====================================================================
echo ✅ 설치 완료!
echo ====================================================================
echo.
echo 다음 단계:
echo   1. backend\.env 파일을 열어 필요한 설정 입력
echo   2. run.bat 실행하여 서버 시작
echo.
echo 서버 실행 명령:
echo   run.bat
echo.
echo 또는 수동으로:
echo   cd backend
echo   python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
echo.
echo ====================================================================
echo.

pause
