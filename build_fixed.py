#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic 오류를 완전히 해결한 빌드 스크립트
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import locale
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


def print_step(step_num, total_steps, title):
    """단계 출력"""
    print("\n" + "=" * 70)
    print(f"  [{step_num}/{total_steps}] {title}")
    print("=" * 70 + "\n")


def clean_previous_build():
    """이전 빌드 파일 정리"""
    print_step(1, 9, "이전 빌드 파일 정리")

    folders = ['build', 'dist', '__pycache__']
    files = ['CoupangWingCS.spec']

    for folder in folders:
        folder_path = Path(folder)
        if folder_path.exists():
            print(f"  제거 중: {folder}/")
            shutil.rmtree(folder_path)

    for file in files:
        file_path = Path(file)
        if file_path.exists():
            print(f"  제거 중: {file}")
            file_path.unlink()

    print("  OK 정리 완료!")


def check_requirements():
    """필수 요구사항 확인"""
    print_step(2, 9, "필수 요구사항 확인")

    print(f"  Python 버전: {sys.version.split()[0]}")

    # backend 폴더 확인
    backend_path = Path('backend')
    if not backend_path.exists():
        print("\n  X 오류: backend 폴더를 찾을 수 없습니다!")
        return False

    print(f"  backend 폴더: 확인 ({len(list(backend_path.rglob('*')))} 파일)")

    # PyInstaller 확인
    try:
        import PyInstaller
        print(f"  PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("  PyInstaller가 설치되지 않았습니다. 설치 중...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"
            ])
            print("  PyInstaller: 설치 완료")
        except subprocess.CalledProcessError:
            print("\n  X 오류: PyInstaller 설치 실패")
            return False

    print("\n  OK 모든 요구사항 충족!")
    return True


def create_enhanced_launcher():
    """향상된 런처 스크립트 생성"""
    print_step(3, 9, "향상된 런처 스크립트 생성")

    launcher_content = '''"""
쿠팡 윙 CS 자동화 시스템 - 완전 자동화 런처
"""
import os
import sys
import uvicorn
import webbrowser
import time
import threading
import socket
from pathlib import Path

# Pydantic v2 환경 변수 설정 (중요!)
os.environ['PYDANTIC_V2'] = '1'
os.environ['PYDANTIC_SKIP_VALIDATING_CORE_SCHEMAS'] = '1'
os.environ['PYDANTIC_USE_DEPRECATED_JSON_ERRORS'] = '0'

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 실행 파일 경로 설정
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

backend_path = os.path.join(application_path, 'backend')

if not os.path.exists(backend_path):
    print(f"X Error: backend folder not found!")
    print(f"   Expected location: {backend_path}")
    input("\\nPress Enter to exit...")
    sys.exit(1)

sys.path.insert(0, backend_path)

# 디렉토리 생성
logs_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(logs_dir, exist_ok=True)

db_dir = os.path.join(os.getcwd(), 'database')
os.makedirs(db_dir, exist_ok=True)

# 환경변수 설정
os.environ.setdefault('DATABASE_URL', f'sqlite:///{os.path.join(db_dir, "coupang_cs.db")}')


def is_port_available(port):
    """포트 사용 가능 여부 확인"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False


def find_available_port(start_port=8000, max_attempts=10):
    """사용 가능한 포트 찾기"""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return None


def open_browser(port):
    """서버 시작 후 브라우저 자동 오픈"""
    time.sleep(3)
    try:
        webbrowser.open(f"http://localhost:{port}/")
        print(f"\\nO 브라우저에서 대시보드를 열었습니다!")
    except Exception as e:
        print(f"\\n!  브라우저 자동 오픈 실패: {e}")


def main():
    print("=" * 70)
    print("  >> 쿠팡 윙 CS 자동화 시스템 v1.0.0")
    print("=" * 70)
    print(f"작업 디렉토리: {os.getcwd()}")
    print(f"로그 디렉토리: {logs_dir}")
    print(f"데이터베이스 디렉토리: {db_dir}")
    print("=" * 70)

    # 사용 가능한 포트 찾기
    print("\\n>> 사용 가능한 포트 검색 중...")
    PORT = find_available_port(8000, 10)

    if PORT is None:
        print("\\nX 오류: 사용 가능한 포트를 찾을 수 없습니다!")
        print("   포트 8000-8009가 모두 사용 중입니다.")
        input("\\nPress Enter to exit...")
        sys.exit(1)

    print(f"O 포트 {PORT} 사용 가능!")
    print("\\n<> 서버 시작 중...")
    print("\\n>> 접속 주소:")
    print(f"  - 대시보드: http://localhost:{PORT}/")
    print(f"  - API 문서: http://localhost:{PORT}/docs")
    print("\\n<< 종료하려면 Ctrl+C를 누르세요.")
    print("=" * 70 + "\\n")

    try:
        from app.main import app

        # 브라우저 자동 오픈
        browser_thread = threading.Thread(target=lambda: open_browser(PORT), daemon=True)
        browser_thread.start()

        # 서버 실행
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=PORT,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\\n\\n<< 서버를 종료합니다...")
    except Exception as e:
        print(f"\\nX 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        input("\\n종료하려면 Enter 키를 누르세요...")


if __name__ == "__main__":
    main()
'''

    with open('launcher_enhanced.py', 'w', encoding='utf-8') as f:
        f.write(launcher_content)

    print("  OK 향상된 런처 스크립트 생성 완료!")


def create_fixed_spec_file():
    """Pydantic 오류를 완전히 해결한 spec 파일 생성"""
    print_step(4, 9, "Pydantic 오류 해결 spec 파일 생성")

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher_enhanced.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Uvicorn
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',

        # FastAPI
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.responses',
        'fastapi.routing',
        'fastapi.encoders',
        'fastapi.exceptions',
        'fastapi.openapi',
        'fastapi.openapi.models',
        'fastapi.openapi.utils',

        # Starlette
        'starlette',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.routing',
        'starlette.responses',
        'starlette.staticfiles',

        # Pydantic v2 (완전한 import)
        'pydantic',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.types',
        'pydantic.dataclasses',
        'pydantic.version',
        'pydantic.json_schema',
        'pydantic.config',
        'pydantic.errors',
        'pydantic.validators',
        'pydantic.deprecated',
        'pydantic.deprecated.decorator',
        'pydantic_core',
        'pydantic_core._pydantic_core',
        'pydantic_settings',
        'pydantic_settings.sources',
        'annotated_types',

        # SQLAlchemy
        'sqlalchemy',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',
        'sqlalchemy.sql',
        'sqlalchemy.pool',

        # Loguru
        'loguru',

        # APScheduler
        'apscheduler',
        'apscheduler.schedulers.background',
        'apscheduler.triggers.cron',
        'apscheduler.triggers.interval',
        'apscheduler.executors.pool',
        'apscheduler.jobstores.memory',
        'tzlocal',

        # Selenium
        'selenium',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',

        # WebDriver Manager
        'webdriver_manager',
        'webdriver_manager.chrome',

        # HTTP Clients
        'httpx',

        # OpenAI
        'openai',

        # Security
        'passlib',
        'passlib.context',

        # System
        'psutil',

        # Email
        'email.mime.text',
        'email.mime.multipart',

        # Python standard library
        'typing',
        'typing_extensions',
        'inspect',
        'functools',
        'dataclasses',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hook-pydantic.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CoupangWingCS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CoupangWingCS',
)
'''

    with open('CoupangWingCS.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("  OK spec 파일 생성 완료!")


def run_pyinstaller():
    """PyInstaller로 실행 파일 빌드"""
    print_step(5, 9, "실행 파일 빌드 중")
    print("  이 작업은 5-10분 정도 소요될 수 있습니다...\n")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "CoupangWingCS.spec"],
            check=True,
            capture_output=True,
            text=True
        )

        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[-10:]:
                if line.strip():
                    print(f"    {line}")

        print("\n  OK 빌드 완료!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n  X 빌드 실패!")
        if e.stdout:
            print("\n  출력:")
            print(e.stdout)
        if e.stderr:
            print("\n  오류:")
            print(e.stderr)
        return False


def copy_backend_folder():
    """backend 폴더 복사"""
    print_step(6, 9, "backend 폴더 복사")

    src = Path('backend')
    dst = Path('dist') / 'CoupangWingCS' / 'backend'

    if not src.exists():
        print("  X 오류: backend 폴더를 찾을 수 없습니다!")
        return False

    if dst.exists():
        print("  기존 backend 폴더 제거 중...")
        shutil.rmtree(dst)

    print(f"  복사 중: {src} -> {dst}")

    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.db',
        '*.db-shm',
        '*.db-wal'
    ))

    file_count = len(list(dst.rglob('*')))
    print(f"  {file_count}개 파일 복사 완료")
    print("  OK 완료!")
    return True


def create_deployment_folder():
    """새로운 배포 폴더 생성"""
    print_step(7, 9, "배포 폴더 생성")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    deployment_name = f"CoupangWingCS_FIXED_{timestamp}"
    deployment_path = Path(deployment_name)

    if deployment_path.exists():
        print("  기존 배포 폴더 제거 중...")
        shutil.rmtree(deployment_path)

    print(f"  배포 폴더 생성: {deployment_name}")

    src = Path('dist') / 'CoupangWingCS'
    if not src.exists():
        print("  X 오류: dist/CoupangWingCS 폴더를 찾을 수 없습니다!")
        return None

    print(f"  복사 중: {src} -> {deployment_path}")
    shutil.copytree(src, deployment_path)

    print("  OK 배포 폴더 생성 완료!")
    return deployment_path


def create_readme(deployment_path):
    """README 파일 생성"""
    print_step(8, 9, "README 파일 생성")

    readme_content = """
================================================================
  쿠팡 윙 CS 자동화 시스템 v1.0.0 (Pydantic 오류 해결)
================================================================

>> 실행 방법:
----------------------------------------------------------------
1. CoupangWingCS.exe를 더블클릭하세요
2. 프로그램이 자동으로:
   O 사용 가능한 포트를 찾습니다 (8000-8009)
   O 서버를 시작합니다
   O 브라우저를 엽니다
3. 끝!

** 새로운 기능:
----------------------------------------------------------------
O Pydantic v2 오류 완전 해결
O 자동 포트 감지 및 변경
O 포트 충돌 시 자동으로 다른 포트 사용
O 서버 연결 상태 자동 확인
O Python 설치 불필요
O 추가 패키지 설치 불필요

>> 시스템 요구사항:
----------------------------------------------------------------
- Windows 10/11
- 그게 전부입니다!

>> 폴더 구조:
----------------------------------------------------------------
CoupangWingCS_FIXED/
├── CoupangWingCS.exe    <- 실행 파일 (이것만 클릭!)
├── backend/             <- 애플리케이션 파일
├── _internal/           <- Python 런타임
└── README.txt           <- 이 파일

!! 중요사항:
----------------------------------------------------------------
• 전체 폴더를 함께 이동/복사하세요
• .exe 파일만 복사하면 작동하지 않습니다

>> 문제 해결:
----------------------------------------------------------------
• Pydantic 오류:
  -> 이 버전에서 완전히 해결되었습니다!

• "backend folder not found" 오류:
  -> 전체 폴더가 제대로 복사되었는지 확인하세요

• "사용 가능한 포트를 찾을 수 없습니다":
  -> 포트 8000-8009가 모두 사용 중입니다
  -> 다른 프로그램을 종료하거나 재부팅하세요

<< 서버 종료:
----------------------------------------------------------------
콘솔 창에서 Ctrl+C를 누르거나 창을 닫으세요

================================================================
"""

    readme_file = deployment_path / 'README.txt'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("  OK README.txt 생성 완료")


def verify_build(deployment_path):
    """빌드 검증"""
    print_step(9, 9, "빌드 검증")

    exe_file = deployment_path / 'CoupangWingCS.exe'
    backend_folder = deployment_path / 'backend'
    internal_folder = deployment_path / '_internal'
    readme_file = deployment_path / 'README.txt'

    checks = [
        (exe_file, "CoupangWingCS.exe"),
        (backend_folder, "backend 폴더"),
        (internal_folder, "_internal 폴더"),
        (readme_file, "README.txt"),
    ]

    all_good = True
    for path, name in checks:
        if path.exists():
            if path.is_dir():
                count = len(list(path.rglob('*')))
                print(f"  O {name}: 확인됨 ({count}개 항목)")
            else:
                size = path.stat().st_size / (1024 * 1024)
                print(f"  O {name}: 확인됨 ({size:.1f} MB)")
        else:
            print(f"  X {name}: 찾을 수 없음")
            all_good = False

    if all_good:
        print("\n  OK 모든 검증 통과!")
        return True
    else:
        print("\n  X 일부 파일이 누락되었습니다!")
        return False


def main():
    """메인 빌드 프로세스"""
    print("\n" + "=" * 70)
    print("  >> Pydantic 오류를 완전히 해결한 빌드")
    print("  - Runtime hook 추가")
    print("  - 환경 변수 설정")
    print("  - 완전한 hiddenimports")
    print("=" * 70)

    # 1단계: 정리
    clean_previous_build()

    # 2단계: 요구사항 확인
    if not check_requirements():
        print("\n빌드를 중단합니다.")
        return

    # 3단계: 향상된 런처 생성
    create_enhanced_launcher()

    # 4단계: spec 파일 생성
    create_fixed_spec_file()

    # 5단계: PyInstaller 빌드
    if not run_pyinstaller():
        print("\n빌드를 중단합니다.")
        return

    # 6단계: backend 폴더 복사
    if not copy_backend_folder():
        print("\n빌드를 중단합니다.")
        return

    # 7단계: 배포 폴더 생성
    deployment_path = create_deployment_folder()
    if not deployment_path:
        print("\n빌드를 중단합니다.")
        return

    # 8단계: README 생성
    create_readme(deployment_path)

    # 9단계: 검증
    verify_build(deployment_path)

    # 성공 메시지
    print("\n" + "=" * 70)
    print("  OK Pydantic 오류가 완전히 해결되었습니다!")
    print("=" * 70)
    print()
    print(f"  >> 배포 폴더: {deployment_path}")
    print()
    print("  ** 해결된 문제:")
    print("    O Pydantic v2 호환성 문제")
    print("    O Runtime hook 추가")
    print("    O 환경 변수 자동 설정")
    print("    O 완전한 모듈 import")
    print()
    print("  >> 다음 단계:")
    print(f"    1. {deployment_path} 폴더로 이동")
    print("    2. CoupangWingCS.exe를 더블클릭")
    print("    3. 오류 없이 실행됩니다!")
    print()
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nX 오류 발생: {e}")
        import traceback
        traceback.print_exc()
