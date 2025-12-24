"""
쿠팡 윙 CS 자동화 시스템 - 간소화된 빌드 스크립트
버전: 2.0.0
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

def install_pyinstaller():
    """PyInstaller 설치"""
    print_step("1. PyInstaller 설치")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "--upgrade"])
        print("[OK] PyInstaller 설치 완료")
    except:
        print("[WARNING] PyInstaller 이미 설치됨")

def create_launcher_script():
    """실행 파일용 런처 스크립트 생성"""
    print_step("2. 런처 스크립트 생성")

    launcher_content = '''"""
쿠팡 윙 CS 자동화 시스템 런처 v2.0.0
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
print("  쿠팡 윙 CS 자동화 시스템 v2.0.0")
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
        import traceback
        traceback.print_exc()
        input("\\n종료하려면 Enter 키를 누르세요...")
'''

    with open("launcher_v2.py", "w", encoding="utf-8") as f:
        f.write(launcher_content)

    print("[OK] launcher_v2.py 생성 완료")

def build_backend():
    """백엔드 실행 파일 빌드"""
    print_step("3. 백엔드 실행 파일 빌드")

    # PyInstaller 명령 구성 (간소화)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"{APP_NAME}_Server",
        "--onedir",  # onefile 대신 onedir 사용
        "--clean",
        "--noconfirm",
        # 데이터 파일 포함
        "--add-data", "backend/app;app",
        # 주요 패키지만 수집
        "--collect-all", "uvicorn",
        "--collect-all", "fastapi",
        # 콘솔 창 표시
        "--console",
        "launcher_v2.py"
    ]

    print("PyInstaller 실행 중...")
    print(" ".join(cmd))
    try:
        subprocess.check_call(cmd)
        print("[OK] 실행 파일 빌드 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 빌드 실패: {e}")
        return False

def create_distribution_folder():
    """배포용 폴더 구조 생성"""
    print_step("4. 배포 폴더 구성")

    # 빌드 디렉토리 생성
    os.makedirs(BUILD_DIR, exist_ok=True)

    # dist 폴더에서 빌드된 폴더를 전체 복사
    source_dir = f"dist/{APP_NAME}_Server"
    if os.path.exists(source_dir):
        # 기존 파일 복사
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(BUILD_DIR, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        print(f"[OK] 실행 파일 복사: {source_dir} -> {BUILD_DIR}")

    # 필수 디렉토리 생성
    for dir_name in ["database", "logs"]:
        os.makedirs(os.path.join(BUILD_DIR, dir_name), exist_ok=True)
        print(f"[OK] 디렉토리 생성: {dir_name}")

    # .env.example 파일 복사
    if os.path.exists("backend/.env.example"):
        shutil.copy2("backend/.env.example", os.path.join(BUILD_DIR, ".env.example"))
        print("[OK] .env.example 복사")

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
   OPENAI_API_KEY=your_openai_api_key
   ```

### 2. 프로그램 실행

**방법 1: 배치 파일 사용 (권장)**
1. `서버시작.bat` 파일을 더블클릭

**방법 2: 직접 실행**
1. `{APP_NAME}_Server.exe` 파일을 더블클릭
2. 서버가 시작되면 브라우저에서 접속:
   - http://localhost:8001

### 3. 크롬 드라이버 (자동 설치)

- Selenium이 처음 실행될 때 자동으로 Chrome 드라이버를 다운로드합니다
- 인터넷 연결이 필요합니다

## 디렉토리 구조

```
{APP_NAME}_v{VERSION}/
├── {APP_NAME}_Server.exe    # 메인 실행 파일
├── 서버시작.bat              # 실행 배치 파일 (권장)
├── _internal/                # 필요한 라이브러리 및 파일들
├── .env                      # 환경 설정 (사용자가 생성)
├── .env.example              # 환경 설정 예제
├── database/                 # 데이터베이스 저장 폴더
├── logs/                     # 로그 파일 저장 폴더
└── 사용설명서.txt            # 이 파일
```

## API 엔드포인트

서버가 실행되면 다음 주소에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

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

### 크롬 자동화 오류

1. Chrome 브라우저가 설치되어 있는지 확인
2. 인터넷 연결 확인 (드라이버 다운로드용)
3. 백신 프로그램이 Chrome 드라이버를 차단하는지 확인

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
cd /d "%~dp0"
echo ==========================================
echo   쿠팡 윙 CS 자동화 시스템 v{VERSION}
echo ==========================================
echo.
echo 서버를 시작합니다...
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
    if os.path.exists("launcher_v2.py"):
        os.remove("launcher_v2.py")
        print("[OK] launcher_v2.py 삭제")

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
        install_pyinstaller()
        create_launcher_script()

        if not build_backend():
            print("\n[ERROR] 빌드 실패!")
            print("\n다음을 시도해보세요:")
            print("1. Python 버전 확인 (Python 3.9-3.11 권장)")
            print("2. pip install -r backend/requirements.txt")
            print("3. 백신 프로그램 일시 중지")
            return

        create_distribution_folder()
        create_batch_files()
        cleanup()

        print("\n")
        print("=" * 60)
        print("  [OK] 빌드 완료!")
        print("=" * 60)
        print(f"\n배포 폴더: {os.path.abspath(BUILD_DIR)}")
        print(f"\n실행 파일: {BUILD_DIR}\\{APP_NAME}_Server.exe")
        print(f"또는: {BUILD_DIR}\\서버시작.bat (권장)")
        print("\n[!] 배포 전 확인사항:")
        print("  1. .env 파일 설정")
        print("  2. 테스트 실행")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 빌드 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
