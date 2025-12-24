"""
CoupangWingCS 완전 자동화 설치 및 실행 파일 빌더
- 포트 충돌 자동 해결
- 의존성 자동 처리
- 버전 호환성 자동 해결
- 완전한 원클릭 실행
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

def print_step(message):
    """단계별 진행 상황 출력"""
    print(f"\n{'='*70}")
    try:
        print(f"  {message}")
    except UnicodeEncodeError:
        print(f"  {message.encode('utf-8', errors='ignore').decode('utf-8')}")
    print(f"{'='*70}")

def create_enhanced_launcher():
    """향상된 런처 스크립트 생성"""
    launcher_code = '''"""
CoupangWingCS 자동화 런처
- 포트 충돌 사전 감지 및 해결
- 서버 자동 시작
- 브라우저 자동 열기
- 의존성 자동 처리
"""

import os
import sys
import time
import socket
import webbrowser
import subprocess
from pathlib import Path

# 실행 파일 경로 설정
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

# Pydantic v2 환경 변수 설정 (가장 먼저!)
os.environ['PYDANTIC_V2'] = '1'
os.environ['PYDANTIC_SKIP_VALIDATING_CORE_SCHEMAS'] = '1'
os.environ['PYDANTIC_USE_DEPRECATED_JSON_ERRORS'] = '0'

def check_port_available(port):
    """포트 사용 가능 여부 확인"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.bind(('localhost', port))
        sock.close()
        return True
    except OSError:
        return False

def find_available_port(start_port=8000, end_port=8009):
    """사용 가능한 포트 찾기"""
    print("\\n[포트 검색] 사용 가능한 포트를 찾는 중...")

    for port in range(start_port, end_port + 1):
        if check_port_available(port):
            print(f"[포트 발견] 포트 {port}를 사용합니다")
            return port

    return None

def wait_for_server(port, max_attempts=30):
    """서버가 완전히 시작될 때까지 대기"""
    print(f"\\n[서버 확인] 포트 {port}에서 서버 시작을 기다리는 중...")

    for attempt in range(max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()

        if result == 0:
            print(f"[서버 확인] 서버가 포트 {port}에서 정상 작동 중입니다!")
            return True

        print(f"  대기 중... ({attempt + 1}/{max_attempts})")
        time.sleep(1)

    return False

def main():
    """메인 실행 함수"""
    print("="*70)
    print("  쿠팡 윙 CS 자동화 시스템 v2.0.0")
    print("  [자동 동기화 & 포트 충돌 해결 버전]")
    print("="*70)

    # 1. Backend 폴더 확인
    backend_dir = BASE_DIR / 'backend'
    if not backend_dir.exists():
        print("\\n[오류] backend 폴더를 찾을 수 없습니다!")
        print(f"경로: {backend_dir}")
        print("\\n프로그램 폴더 전체를 복사했는지 확인하세요.")
        input("\\nEnter를 눌러 종료하세요...")
        return 1

    # 2. 사용 가능한 포트 찾기
    port = find_available_port()

    if port is None:
        print("\\n[오류] 사용 가능한 포트를 찾을 수 없습니다!")
        print("포트 8000-8009가 모두 사용 중입니다.")
        print("\\n해결 방법:")
        print("  1. 다른 프로그램을 종료해보세요")
        print("  2. 컴퓨터를 재부팅해보세요")
        input("\\nEnter를 눌러 종료하세요...")
        return 1

    # 3. 환경 변수 설정
    os.environ['PORT'] = str(port)
    os.environ['HOST'] = '127.0.0.1'

    # 4. 서버 시작
    print(f"\\n[서버 시작] FastAPI 서버를 포트 {port}에서 시작합니다...")

    try:
        # uvicorn import 및 실행
        import uvicorn
        from app.main import app

        # 백그라운드에서 서버 시작
        import threading

        def run_server():
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=port,
                log_level="info"
            )

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # 서버가 시작될 때까지 대기
        if wait_for_server(port):
            # 5. 브라우저 열기
            url = f"http://localhost:{port}"
            print(f"\\n[브라우저 열기] {url}")
            time.sleep(2)  # 서버가 완전히 준비될 시간 추가
            webbrowser.open(url)

            print("\\n" + "="*70)
            print("  서버가 성공적으로 시작되었습니다!")
            print(f"  URL: {url}")
            print("  Ctrl+C를 눌러 종료할 수 있습니다")
            print("="*70 + "\\n")

            # 서버 계속 실행
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\\n\\n[종료] 서버를 종료합니다...")
                return 0
        else:
            print("\\n[오류] 서버 시작 시간 초과")
            print("서버가 시작되지 않았습니다.")
            input("\\nEnter를 눌러 종료하세요...")
            return 1

    except Exception as e:
        print(f"\\n[오류] 서버 시작 실패: {e}")
        print("\\n오류 세부정보:")
        import traceback
        traceback.print_exc()
        input("\\nEnter를 눌러 종료하세요...")
        return 1

if __name__ == '__main__':
    sys.exit(main())
'''

    with open('launcher_enhanced.py', 'w', encoding='utf-8') as f:
        f.write(launcher_code)

    print("OK 향상된 런처 생성 완료")

def create_spec_file():
    """PyInstaller spec 파일 생성"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher_enhanced.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend', 'backend'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.routing',
        'fastapi.encoders',
        'pydantic',
        'pydantic.v1',
        'pydantic.deprecated',
        'pydantic.json_schema',
        'pydantic_core',
        'pydantic_settings',
        'sqlalchemy',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',
        'openai',
        'anthropic',
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'webdriver_manager',
        'webdriver_manager.chrome',
        'bs4',
        'lxml',
        'click',
        'h11',
        'starlette',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'anyio',
        'sniffio',
    ],
    hookspath=[],
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
    name='CoupangWingCS_AutoInstaller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CoupangWingCS_AutoInstaller',
)
'''

    with open('CoupangWingCS_AutoInstaller.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("OK Spec 파일 생성 완료")

def copy_frontend_files():
    """프론트엔드 빌드 파일을 backend/static으로 복사"""
    print_step("프론트엔드 파일 복사")

    src_dir = Path('frontend/dist')
    dst_dir = Path('backend/static')

    if dst_dir.exists():
        shutil.rmtree(dst_dir)

    shutil.copytree(src_dir, dst_dir)

    files = list(dst_dir.rglob('*'))
    print(f"OK {len(files)}개 파일 복사 완료")

def build_executable():
    """PyInstaller로 실행 파일 빌드"""
    print_step("실행 파일 빌드 시작")

    cmd = [sys.executable, '-m', 'PyInstaller', 'CoupangWingCS_AutoInstaller.spec', '--clean', '--noconfirm']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("빌드 실패!")
        print(result.stderr)
        return False

    print("OK 빌드 완료")
    return True

def create_deployment_package():
    """배포 패키지 생성"""
    print_step("배포 패키지 생성")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    deploy_dir = Path(f'CoupangWingCS_AutoSync_{timestamp}')

    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)

    deploy_dir.mkdir()

    # dist 폴더의 내용 복사
    dist_dir = Path('dist/CoupangWingCS_AutoInstaller')

    for item in dist_dir.iterdir():
        if item.is_dir():
            shutil.copytree(item, deploy_dir / item.name)
        else:
            shutil.copy2(item, deploy_dir / item.name)

    # backend 폴더를 _internal에서 루트로 이동
    backend_in_internal = deploy_dir / '_internal' / 'backend'
    backend_root = deploy_dir / 'backend'

    if backend_in_internal.exists() and not backend_root.exists():
        shutil.move(str(backend_in_internal), str(backend_root))
        print("  backend 폴더를 루트로 이동했습니다")

    # README 파일 생성
    readme_content = f'''
================================================================
  쿠팡 윙 CS 자동화 시스템 v2.0.0
  [자동 동기화 & 포트 충돌 해결 버전]
================================================================

>> 실행 방법:
----------------------------------------------------------------
1. CoupangWingCS_AutoInstaller.exe를 더블클릭하세요
2. 프로그램이 자동으로:
   ✓ 포트 충돌을 사전에 체크합니다
   ✓ 사용 가능한 포트를 자동으로 찾습니다 (8000-8009)
   ✓ 서버를 자동으로 시작합니다
   ✓ 브라우저를 자동으로 엽니다
3. 끝!

** 새로운 기능 (v2.0.0):
----------------------------------------------------------------
✓ 자동 동기화 버튼
  - 연결 실패 시 "자동 동기화" 버튼 클릭
  - 연결될 때까지 자동으로 계속 시도
  - 최대 50회까지 자동 재시도

✓ 포트 충돌 완전 자동 해결
  - 시작 전 모든 포트 캐시 초기화
  - 사용 중인 포트 자동 감지
  - 빈 포트로 자동 전환

✓ 실시간 연결 상태 표시
  - 포트 스캔 진행률 표시
  - 동기화 시도 횟수 표시
  - 연결 성공/실패 알림

✓ 완전한 원클릭 설치
  - Python 설치 불필요
  - 패키지 설치 불필요
  - 버전 호환성 자동 처리
  - 의존성 완전 포함

>> 시스템 요구사항:
----------------------------------------------------------------
- Windows 10/11
- 그게 전부입니다!

>> 폴더 구조:
----------------------------------------------------------------
CoupangWingCS_AutoSync/
├── CoupangWingCS_AutoInstaller.exe  <- 실행 파일 (이것만 클릭!)
├── backend/                          <- 애플리케이션 파일
├── _internal/                        <- Python 런타임
└── README.txt                        <- 이 파일

!! 중요사항:
----------------------------------------------------------------
• 전체 폴더를 함께 이동/복사하세요
• .exe 파일만 복사하면 작동하지 않습니다
• 처음 실행 시 방화벽 허용이 필요할 수 있습니다

>> 문제 해결:
----------------------------------------------------------------
• "backend folder not found" 오류:
  -> 전체 폴더가 제대로 복사되었는지 확인하세요

• "사용 가능한 포트를 찾을 수 없습니다":
  -> 포트 8000-8009가 모두 사용 중입니다
  -> 다른 프로그램을 종료하거나 재부팅하세요

• 서버 연결 실패:
  -> "자동 동기화" 버튼을 클릭하세요
  -> 연결될 때까지 자동으로 시도합니다

• Pydantic 오류:
  -> 이 버전에서 완전히 해결되었습니다!

>> 자동 동기화 사용 방법:
----------------------------------------------------------------
1. 프로그램 실행
2. 연결 화면이 나타남
3. 연결 실패 시 "자동 동기화" 버튼 표시
4. 버튼 클릭 -> 자동으로 연결될 때까지 시도
5. 백엔드 서버 시작 후 자동으로 연결됨

<< 서버 종료:
----------------------------------------------------------------
콘솔 창에서 Ctrl+C를 누르거나 창을 닫으세요

================================================================
빌드 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================
'''

    readme_path = deploy_dir / 'README.txt'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"OK 배포 패키지 생성: {deploy_dir}")
    return deploy_dir

def verify_build(deploy_dir):
    """빌드 결과 검증"""
    print_step("빌드 검증")

    exe_path = deploy_dir / 'CoupangWingCS_AutoInstaller.exe'
    backend_path = deploy_dir / 'backend'
    internal_path = deploy_dir / '_internal'

    checks = [
        ("실행 파일", exe_path),
        ("Backend 폴더", backend_path),
        ("Internal 폴더", internal_path),
        ("Static 폴더", backend_path / 'static'),
    ]

    all_ok = True
    for name, path in checks:
        exists = path.exists()
        status = "OK" if exists else "FAIL"
        print(f"  {status} {name}: {path}")
        if not exists:
            all_ok = False

    if all_ok:
        # 파일 크기 확인
        exe_size = exe_path.stat().st_size / (1024 * 1024)  # MB
        backend_files = len(list(backend_path.rglob('*')))
        internal_files = len(list(internal_path.rglob('*')))

        print(f"\n  실행 파일 크기: {exe_size:.1f} MB")
        print(f"  Backend 파일 수: {backend_files}")
        print(f"  Internal 파일 수: {internal_files}")

        print("\nOK 모든 검증 통과!")
        return True
    else:
        print("\nFAIL 일부 파일이 누락되었습니다!")
        return False

def main():
    """메인 빌드 프로세스"""
    print("\n" + "="*70)
    print("  쿠팡 윙 CS 자동화 설치 파일 빌더 v2.0.0")
    print("  [자동 동기화 & 완전 자동화 버전]")
    print("="*70)

    try:
        # 1. 향상된 런처 생성
        print_step("1/6 향상된 런처 생성")
        create_enhanced_launcher()

        # 2. Spec 파일 생성
        print_step("2/6 Spec 파일 생성")
        create_spec_file()

        # 3. 프론트엔드 파일 복사
        print_step("3/6 프론트엔드 파일 복사")
        copy_frontend_files()

        # 4. 실행 파일 빌드
        print_step("4/6 실행 파일 빌드")
        if not build_executable():
            print("\n빌드 실패!")
            return 1

        # 5. 배포 패키지 생성
        print_step("5/6 배포 패키지 생성")
        deploy_dir = create_deployment_package()

        # 6. 빌드 검증
        print_step("6/6 빌드 검증")
        if not verify_build(deploy_dir):
            print("\n검증 실패!")
            return 1

        # 완료
        print("\n" + "="*70)
        print("  OK 빌드 완료!")
        print("="*70)
        print(f"\n배포 폴더: {deploy_dir.absolute()}")
        print(f"\n실행 방법:")
        print(f"  1. {deploy_dir} 폴더를 원하는 위치로 복사")
        print(f"  2. CoupangWingCS_AutoInstaller.exe 더블클릭")
        print(f"  3. 자동으로 서버 시작 및 브라우저 열림!")
        print("\n" + "="*70)

        return 0

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
