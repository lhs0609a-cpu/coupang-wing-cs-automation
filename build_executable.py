"""
쿠팡 윙 CS 자동화 시스템 - 실행 파일 빌드 스크립트
버전: 1.0.0
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime

VERSION = "2.0.0"
APP_NAME = "CoupangWingCS"
BUILD_DIR = f"Release/{APP_NAME}_v{VERSION}"

def print_step(step_name):
    """단계별 진행 상황 출력"""
    print("\n" + "="*60)
    print(f"  {step_name}")
    print("="*60)

def install_dependencies():
    """필요한 패키지 설치"""
    print_step("1. 필요한 패키지 설치")

    # PyInstaller 설치
    print("PyInstaller 설치 중...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 백엔드 의존성 설치
    print("백엔드 의존성 설치 중...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])

def create_launcher_script():
    """실행 파일용 런처 스크립트 생성"""
    print_step("2. 런처 스크립트 생성")

    launcher_content = '''"""
쿠팡 윙 CS 자동화 시스템 런처
"""
import os
import sys
import uvicorn
from pathlib import Path

# 실행 파일 경로 설정
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 실행 파일
    application_path = sys._MEIPASS
else:
    # 일반 Python 스크립트
    application_path = os.path.dirname(os.path.abspath(__file__))

# 백엔드 경로 추가
backend_path = os.path.join(application_path, 'backend')
sys.path.insert(0, backend_path)

# 로그 디렉토리 생성
logs_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# 데이터베이스 디렉토리 생성
db_dir = os.path.join(os.getcwd(), 'database')
os.makedirs(db_dir, exist_ok=True)

print("="*60)
print("  쿠팡 윙 CS 자동화 시스템 v''' + VERSION + '''")
print("="*60)
print(f"작업 디렉토리: {os.getcwd()}")
print(f"로그 디렉토리: {logs_dir}")
print(f"데이터베이스 디렉토리: {db_dir}")
print("="*60)
print("\\n서버 시작 중...")
print("\\n접속 주소:")
print("  - http://localhost:8001")
print("  - http://0.0.0.0:8001")
print("\\n종료하려면 Ctrl+C를 누르세요.")
print("="*60 + "\\n")

# 환경변수 설정
os.environ.setdefault('DATABASE_URL', f'sqlite:///{os.path.join(db_dir, "coupang_cs.db")}')

# 메인 앱 실행
if __name__ == "__main__":
    try:
        from app.main import app
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            reload=False
        )
    except KeyboardInterrupt:
        print("\\n\\n서버를 종료합니다...")
    except Exception as e:
        print(f"\\n오류 발생: {e}")
        input("\\n종료하려면 Enter 키를 누르세요...")
'''

    with open("launcher.py", "w", encoding="utf-8") as f:
        f.write(launcher_content)

    print("[OK] launcher.py 생성 완료")

def build_backend():
    """백엔드 실행 파일 빌드"""
    print_step("3. 백엔드 실행 파일 빌드")

    # PyInstaller 명령 구성
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"{APP_NAME}_Server",
        "--onefile",
        "--clean",
        "--noconfirm",
        # 데이터 파일 포함
        "--add-data", "backend/app;app",
        # 전체 패키지 수집
        "--collect-all", "fastapi",
        "--collect-all", "uvicorn",
        "--collect-all", "starlette",
        "--collect-all", "pydantic",
        "--collect-all", "sqlalchemy",
        # 숨겨진 import 포함
        "--hidden-import", "fastapi",
        "--hidden-import", "fastapi.routing",
        "--hidden-import", "fastapi.middleware",
        "--hidden-import", "fastapi.middleware.cors",
        "--hidden-import", "starlette",
        "--hidden-import", "starlette.routing",
        "--hidden-import", "starlette.middleware",
        "--hidden-import", "starlette.responses",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "pydantic",
        "--hidden-import", "pydantic_settings",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        "--hidden-import", "sqlalchemy.ext.declarative",
        "--hidden-import", "loguru",
        "--hidden-import", "python-multipart",
        "--hidden-import", "selenium",
        "--hidden-import", "selenium.webdriver",
        "--hidden-import", "selenium.webdriver.chrome",
        "--hidden-import", "selenium.webdriver.chrome.service",
        "--hidden-import", "selenium.webdriver.common",
        "--hidden-import", "selenium.webdriver.support",
        "--hidden-import", "webdriver_manager",
        "--hidden-import", "webdriver_manager.chrome",
        "--hidden-import", "openai",
        "--hidden-import", "cryptography",
        "--hidden-import", "jose",
        "--hidden-import", "passlib",
        # 콘솔 창 표시
        "--console",
        "launcher.py"
    ]

    print("PyInstaller 실행 중...")
    print(" ".join(cmd))
    subprocess.check_call(cmd)
    print("[OK] 실행 파일 빌드 완료")

def create_distribution_folder():
    """배포용 폴더 구조 생성"""
    print_step("4. 배포 폴더 구성")

    # 빌드 디렉토리 생성
    os.makedirs(BUILD_DIR, exist_ok=True)

    # 실행 파일 복사
    exe_file = f"dist/{APP_NAME}_Server.exe"
    if os.path.exists(exe_file):
        shutil.copy2(exe_file, BUILD_DIR)
        print(f"[OK] 실행 파일 복사: {exe_file}")

    # 필수 디렉토리 생성
    for dir_name in ["database", "logs", "frontend_build"]:
        os.makedirs(os.path.join(BUILD_DIR, dir_name), exist_ok=True)
        print(f"[OK] 디렉토리 생성: {dir_name}")

    # .env.example 파일 복사
    if os.path.exists("backend/.env.example"):
        shutil.copy2("backend/.env.example", os.path.join(BUILD_DIR, ".env.example"))
        print("[OK] .env.example 복사")

    # README 복사
    if os.path.exists("README.md"):
        shutil.copy2("README.md", os.path.join(BUILD_DIR, "README.md"))
        print("[OK] README.md 복사")

    # 사용 설명서 생성
    create_user_manual()

def create_user_manual():
    """사용자 매뉴얼 생성"""
    manual_content = f"""# 쿠팡 윙 CS 자동화 시스템 v{VERSION}

## 설치 및 실행 방법

### 1. 초기 설정

1. `.env.example` 파일을 `.env`로 복사
2. `.env` 파일을 열어 필수 정보 입력:
   ```
   COUPANG_ACCESS_KEY=your_access_key
   COUPANG_SECRET_KEY=your_secret_key
   COUPANG_VENDOR_ID=your_vendor_id
   COUPANG_WING_ID=your_wing_id
   SECRET_KEY=your_secret_key_here
   ```

### 2. 프로그램 실행

1. `{APP_NAME}_Server.exe` 파일을 더블클릭
2. 서버가 시작되면 브라우저에서 접속:
   - http://localhost:8001

### 3. 프론트엔드 (선택사항)

프론트엔드가 별도로 빌드되어 있다면:
1. `frontend_build` 폴더에 빌드된 파일 복사
2. 웹 서버로 실행하거나 브라우저로 index.html 직접 열기

## 디렉토리 구조

```
{APP_NAME}_v{VERSION}/
├── {APP_NAME}_Server.exe    # 메인 실행 파일
├── .env                      # 환경 설정 (사용자가 생성)
├── .env.example              # 환경 설정 예제
├── database/                 # 데이터베이스 저장 폴더
├── logs/                     # 로그 파일 저장 폴더
├── frontend_build/           # 프론트엔드 빌드 파일 (선택)
└── README.md                 # 상세 설명서
```

## 문제 해결

### 실행 파일이 실행되지 않을 때

1. Windows Defender나 백신 프로그램에서 차단하는지 확인
2. 관리자 권한으로 실행 시도
3. logs 폴더의 로그 파일 확인

### 데이터베이스 오류

1. database 폴더의 파일 삭제 후 재실행
2. 프로그램이 자동으로 데이터베이스를 재생성합니다

### API 연결 오류

1. `.env` 파일의 API 키 확인
2. 인터넷 연결 확인
3. 쿠팡 API 서버 상태 확인

## 지원

문제가 발생하면:
1. logs 폴더의 로그 파일 확인
2. 개발자에게 로그 파일과 함께 문의

---

빌드 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
버전: {VERSION}
"""

    with open(os.path.join(BUILD_DIR, "사용설명서.txt"), "w", encoding="utf-8") as f:
        f.write(manual_content)

    print("[OK] 사용설명서.txt 생성")

def create_batch_files():
    """편의용 배치 파일 생성"""
    print_step("5. 편의 스크립트 생성")

    # 실행 배치 파일
    start_bat = f"""@echo off
chcp 65001 > nul
echo ==========================================
echo   쿠팡 윙 CS 자동화 시스템 v{VERSION}
echo ==========================================
echo.
{APP_NAME}_Server.exe
pause
"""

    with open(os.path.join(BUILD_DIR, "서버시작.bat"), "w", encoding="utf-8") as f:
        f.write(start_bat)

    print("[OK] 서버시작.bat 생성")

def cleanup():
    """빌드 임시 파일 정리"""
    print_step("6. 임시 파일 정리")

    # 임시 파일 삭제
    if os.path.exists("launcher.py"):
        os.remove("launcher.py")
        print("[OK] launcher.py 삭제")

    if os.path.exists("build"):
        shutil.rmtree("build")
        print("[OK] build 폴더 삭제")

    if os.path.exists(f"{APP_NAME}_Server.spec"):
        os.remove(f"{APP_NAME}_Server.spec")
        print("[OK] .spec 파일 삭제")

def main():
    """메인 빌드 프로세스"""
    print("\n")
    print("*" * 60)
    print(f"  쿠팡 윙 CS 자동화 시스템 빌드 스크립트 v{VERSION}")
    print("*" * 60)

    try:
        install_dependencies()
        create_launcher_script()
        build_backend()
        create_distribution_folder()
        create_batch_files()
        cleanup()

        print("\n")
        print("=" * 60)
        print("  [OK] 빌드 완료!")
        print("=" * 60)
        print(f"\n배포 폴더: {os.path.abspath(BUILD_DIR)}")
        print(f"\n실행 파일: {BUILD_DIR}\\{APP_NAME}_Server.exe")
        print(f"또는: {BUILD_DIR}\\서버시작.bat")
        print("\n[!] 배포 전 확인사항:")
        print("  1. .env 파일 설정")
        print("  2. 프론트엔드 빌드 파일 복사 (선택)")
        print("  3. 테스트 실행")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 빌드 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
