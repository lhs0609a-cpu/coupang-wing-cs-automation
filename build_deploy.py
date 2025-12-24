#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
쿠팡 윙 CS 자동화 - 배포용 실행파일 빌드 스크립트
새로운 폴더에 완전한 배포 패키지를 생성합니다.
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
    print_step(1, 8, "이전 빌드 파일 정리")

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

    print("  ✓ 정리 완료!")


def check_requirements():
    """필수 요구사항 확인"""
    print_step(2, 8, "필수 요구사항 확인")

    # Python 버전 확인
    print(f"  Python 버전: {sys.version.split()[0]}")

    # backend 폴더 확인
    backend_path = Path('backend')
    if not backend_path.exists():
        print("\n  ❌ 오류: backend 폴더를 찾을 수 없습니다!")
        print("  backend 폴더가 이 스크립트와 같은 디렉토리에 있어야 합니다.")
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
            print("\n  ❌ 오류: PyInstaller 설치 실패")
            return False

    print("\n  ✓ 모든 요구사항 충족!")
    return True


def create_spec_file():
    """PyInstaller spec 파일 생성"""
    print_step(3, 8, "PyInstaller spec 파일 생성")

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Uvicorn (ASGI 서버)
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
        'fastapi.middleware.gzip',
        'fastapi.middleware.httpsredirect',
        'fastapi.middleware.trustedhost',
        'fastapi.responses',
        'fastapi.routing',
        'fastapi.encoders',
        'fastapi.exceptions',
        'fastapi.param_functions',
        'fastapi.utils',
        'fastapi.testclient',

        # Starlette
        'starlette',
        'starlette.middleware',
        'starlette.middleware.base',
        'starlette.middleware.cors',
        'starlette.middleware.gzip',
        'starlette.middleware.httpsredirect',
        'starlette.middleware.trustedhost',
        'starlette.routing',
        'starlette.responses',
        'starlette.exceptions',

        # SQLAlchemy
        'sqlalchemy',
        'sqlalchemy.ext',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.sql',
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.orm',
        'sqlalchemy.engine',
        'sqlalchemy.pool',

        # Pydantic v2
        'pydantic',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.types',
        'pydantic.networks',
        'pydantic.dataclasses',
        'pydantic.version',
        'pydantic.error_wrappers',
        'pydantic.json',
        'pydantic_core',
        'pydantic_settings',
        'annotated_types',

        # Logging
        'loguru',

        # APScheduler
        'apscheduler',
        'apscheduler.schedulers',
        'apscheduler.schedulers.background',
        'apscheduler.schedulers.base',
        'apscheduler.triggers',
        'apscheduler.triggers.cron',
        'apscheduler.triggers.interval',
        'apscheduler.triggers.date',
        'apscheduler.executors',
        'apscheduler.executors.pool',
        'apscheduler.jobstores',
        'apscheduler.jobstores.base',
        'apscheduler.jobstores.memory',
        'apscheduler.util',
        'apscheduler.events',
        'tzlocal',

        # Selenium
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common',
        'selenium.webdriver.common.by',
        'selenium.webdriver.common.keys',
        'selenium.webdriver.common.action_chains',
        'selenium.webdriver.support',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.wait',
        'selenium.webdriver.support.expected_conditions',
        'selenium.webdriver.support.select',
        'selenium.common',
        'selenium.common.exceptions',
        'selenium.types',

        # WebDriver Manager
        'webdriver_manager',
        'webdriver_manager.chrome',
        'webdriver_manager.core',

        # HTTP Clients
        'httpx',
        'httpx._client',
        'httpx._config',
        'httpx._models',

        # OpenAI
        'openai',
        'openai.types',
        'openai.resources',

        # Security
        'passlib',
        'passlib.context',
        'passlib.hash',

        # System monitoring
        'psutil',

        # Email
        'email',
        'email.mime',
        'email.mime.text',
        'email.mime.multipart',
        'smtplib',

        # Other
        'multipart',
        'email_validator',
        'pytest',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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

    print("  ✓ spec 파일 생성 완료: CoupangWingCS.spec")


def run_pyinstaller():
    """PyInstaller로 실행 파일 빌드"""
    print_step(4, 8, "실행 파일 빌드 중")
    print("  이 작업은 5-10분 정도 소요될 수 있습니다...\n")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "CoupangWingCS.spec"],
            check=True,
            capture_output=True,
            text=True
        )

        # 출력 마지막 몇 줄 표시
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[-10:]:
                if line.strip():
                    print(f"    {line}")

        print("\n  ✓ 빌드 완료!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n  ❌ 빌드 실패!")
        if e.stdout:
            print("\n  출력:")
            print(e.stdout)
        if e.stderr:
            print("\n  오류:")
            print(e.stderr)
        return False


def copy_backend_folder():
    """backend 폴더 복사"""
    print_step(5, 8, "backend 폴더 복사")

    src = Path('backend')
    dst = Path('dist') / 'CoupangWingCS' / 'backend'

    if not src.exists():
        print("  ❌ 오류: backend 폴더를 찾을 수 없습니다!")
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
    print("  ✓ 완료!")
    return True


def create_deployment_folder():
    """새로운 배포 폴더 생성"""
    print_step(6, 8, "배포 폴더 생성")

    # 타임스탬프로 폴더 이름 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    deployment_name = f"CoupangWingCS_Deployment_{timestamp}"
    deployment_path = Path(deployment_name)

    # 배포 폴더 생성
    if deployment_path.exists():
        print("  기존 배포 폴더 제거 중...")
        shutil.rmtree(deployment_path)

    print(f"  배포 폴더 생성: {deployment_name}")

    # dist의 CoupangWingCS 폴더를 새 배포 폴더로 복사
    src = Path('dist') / 'CoupangWingCS'
    if not src.exists():
        print("  ❌ 오류: dist/CoupangWingCS 폴더를 찾을 수 없습니다!")
        return None

    print(f"  복사 중: {src} -> {deployment_path}")
    shutil.copytree(src, deployment_path)

    print("  ✓ 배포 폴더 생성 완료!")
    return deployment_path


def create_readme(deployment_path):
    """README 파일 생성"""
    print_step(7, 8, "README 파일 생성")

    readme_content = """
═══════════════════════════════════════════════════════════════
  쿠팡 윙 CS 자동화 시스템 v1.0.0
═══════════════════════════════════════════════════════════════

🚀 실행 방법:
────────────────────────────────────────────────────────────
1. CoupangWingCS.exe를 더블클릭하세요
2. 서버가 시작되고 자동으로 브라우저가 열립니다
3. API 문서: http://localhost:8080/docs

⚙️ 설정:
────────────────────────────────────────────────────────────
- 첫 실행 시 .env 파일이 자동으로 생성됩니다
- .env 파일을 열어 API 키를 입력하세요

📋 시스템 요구사항:
────────────────────────────────────────────────────────────
- Windows 10/11
- Python 설치 불필요! (실행 파일에 포함됨)

📁 폴더 구조:
────────────────────────────────────────────────────────────
CoupangWingCS_Deployment/
├── CoupangWingCS.exe    ← 실행 파일
├── backend/             ← 애플리케이션 파일 (삭제 금지)
├── _internal/           ← Python 런타임 (삭제 금지)
└── README.txt           ← 이 파일

⚠️ 중요사항:
────────────────────────────────────────────────────────────
• 공유 시 전체 폴더를 압축하여 전달하세요
• .exe 파일만 복사하면 작동하지 않습니다
• backend 폴더는 반드시 .exe와 같은 위치에 있어야 합니다

🔧 문제 해결:
────────────────────────────────────────────────────────────
• "backend folder not found" 오류:
  → 전체 폴더가 제대로 복사되었는지 확인하세요

• "Port 8080 in use" 오류:
  → 다른 프로그램이 8080 포트를 사용 중입니다
  → 해당 프로그램을 종료하거나 재시작하세요

• 안티바이러스 차단:
  → 이는 오탐지입니다 (False Positive)
  → 백신 프로그램의 예외 목록에 추가하세요

• 모듈 import 오류:
  → 이 빌드는 모든 필요한 모듈을 포함하고 있습니다
  → 전체 폴더를 다시 압축 해제해보세요

🛑 서버 종료:
────────────────────────────────────────────────────────────
콘솔 창에서 Ctrl+C를 누르세요

📞 지원:
────────────────────────────────────────────────────────────
문제가 계속되면 프로젝트 저장소를 방문하세요.

═══════════════════════════════════════════════════════════════
"""

    readme_file = deployment_path / 'README.txt'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("  ✓ README.txt 생성 완료")

    # 실행 가이드 파일 생성 (간단 버전)
    guide_content = """빠른 시작 가이드
=================

1. CoupangWingCS.exe 더블클릭
2. 브라우저에서 http://localhost:8080/docs 접속
3. 사용 시작!

자세한 내용은 README.txt를 참고하세요.
"""

    guide_file = deployment_path / '실행방법.txt'
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)

    print("  ✓ 실행방법.txt 생성 완료")


def verify_build(deployment_path):
    """빌드 검증"""
    print_step(8, 8, "빌드 검증")

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
                print(f"  ✓ {name}: 확인됨 ({count}개 항목)")
            else:
                size = path.stat().st_size / (1024 * 1024)
                print(f"  ✓ {name}: 확인됨 ({size:.1f} MB)")
        else:
            print(f"  ✗ {name}: 찾을 수 없음")
            all_good = False

    if all_good:
        print("\n  ✓ 모든 검증 통과!")
        return True
    else:
        print("\n  ✗ 일부 파일이 누락되었습니다!")
        return False


def main():
    """메인 빌드 프로세스"""
    print("\n" + "=" * 70)
    print("  쿠팡 윙 CS 자동화 - 배포 빌드 스크립트")
    print("  새로운 폴더에 완전한 배포 패키지를 생성합니다")
    print("=" * 70)

    # 1단계: 정리
    clean_previous_build()

    # 2단계: 요구사항 확인
    if not check_requirements():
        input("\n계속하려면 Enter 키를 누르세요...")
        return

    # 3단계: spec 파일 생성
    create_spec_file()

    # 4단계: PyInstaller 빌드
    if not run_pyinstaller():
        input("\n계속하려면 Enter 키를 누르세요...")
        return

    # 5단계: backend 폴더 복사
    if not copy_backend_folder():
        input("\n계속하려면 Enter 키를 누르세요...")
        return

    # 6단계: 배포 폴더 생성
    deployment_path = create_deployment_folder()
    if not deployment_path:
        input("\n계속하려면 Enter 키를 누르세요...")
        return

    # 7단계: README 생성
    create_readme(deployment_path)

    # 8단계: 검증
    verify_build(deployment_path)

    # 성공 메시지
    print("\n" + "=" * 70)
    print("  ✅ 빌드가 성공적으로 완료되었습니다!")
    print("=" * 70)
    print()
    print(f"  📁 배포 폴더: {deployment_path}")
    print()
    print("  ✓ 포함된 항목:")
    print("    - CoupangWingCS.exe (실행 파일)")
    print("    - backend 폴더 (애플리케이션 코드)")
    print("    - _internal 폴더 (Python 런타임)")
    print("    - README.txt (사용 설명서)")
    print("    - 실행방법.txt (빠른 시작 가이드)")
    print()
    print("  📝 다음 단계:")
    print(f"    1. {deployment_path} 폴더로 이동")
    print("    2. CoupangWingCS.exe를 실행하여 테스트")
    print("    3. 작동하면 전체 폴더를 ZIP으로 압축")
    print("    4. ZIP 파일을 공유")
    print()
    print("  ⚠️  중요: 전체 폴더를 공유하세요, .exe 파일만 공유하지 마세요!")
    print()
    print("=" * 70)
    input("\n계속하려면 Enter 키를 누르세요...")


if __name__ == "__main__":
    main()
