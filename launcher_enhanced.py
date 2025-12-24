"""
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
    print("\n[포트 검색] 사용 가능한 포트를 찾는 중...")

    for port in range(start_port, end_port + 1):
        if check_port_available(port):
            print(f"[포트 발견] 포트 {port}를 사용합니다")
            return port

    return None

def wait_for_server(port, max_attempts=30):
    """서버가 완전히 시작될 때까지 대기"""
    print(f"\n[서버 확인] 포트 {port}에서 서버 시작을 기다리는 중...")

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
        print("\n[오류] backend 폴더를 찾을 수 없습니다!")
        print(f"경로: {backend_dir}")
        print("\n프로그램 폴더 전체를 복사했는지 확인하세요.")
        input("\nEnter를 눌러 종료하세요...")
        return 1

    # 2. 사용 가능한 포트 찾기
    port = find_available_port()

    if port is None:
        print("\n[오류] 사용 가능한 포트를 찾을 수 없습니다!")
        print("포트 8000-8009가 모두 사용 중입니다.")
        print("\n해결 방법:")
        print("  1. 다른 프로그램을 종료해보세요")
        print("  2. 컴퓨터를 재부팅해보세요")
        input("\nEnter를 눌러 종료하세요...")
        return 1

    # 3. 환경 변수 설정
    os.environ['PORT'] = str(port)
    os.environ['HOST'] = '127.0.0.1'

    # 4. 서버 시작
    print(f"\n[서버 시작] FastAPI 서버를 포트 {port}에서 시작합니다...")

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
            print(f"\n[브라우저 열기] {url}")
            time.sleep(2)  # 서버가 완전히 준비될 시간 추가
            webbrowser.open(url)

            print("\n" + "="*70)
            print("  서버가 성공적으로 시작되었습니다!")
            print(f"  URL: {url}")
            print("  Ctrl+C를 눌러 종료할 수 있습니다")
            print("="*70 + "\n")

            # 서버 계속 실행
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n[종료] 서버를 종료합니다...")
                return 0
        else:
            print("\n[오류] 서버 시작 시간 초과")
            print("서버가 시작되지 않았습니다.")
            input("\nEnter를 눌러 종료하세요...")
            return 1

    except Exception as e:
        print(f"\n[오류] 서버 시작 실패: {e}")
        print("\n오류 세부정보:")
        import traceback
        traceback.print_exc()
        input("\nEnter를 눌러 종료하세요...")
        return 1

if __name__ == '__main__':
    sys.exit(main())
