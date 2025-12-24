"""
쿠팡 윙 CS 자동화 시스템 - 스마트 자동 연결 런처
빈 포트를 찾아서 백엔드를 자동으로 시작하고 브라우저를 엽니다.
"""
import os
import sys
import time
import socket
import threading
import webbrowser
from pathlib import Path

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

# 백엔드 경로 추가
backend_path = os.path.join(application_path, 'backend')

if not os.path.exists(backend_path):
    print(f"❌ 오류: backend 폴더를 찾을 수 없습니다!")
    print(f"   예상 위치: {backend_path}")
    input("\n종료하려면 Enter 키를 누르세요...")
    sys.exit(1)

sys.path.insert(0, backend_path)

# 디렉토리 생성
logs_dir = os.path.join(os.getcwd(), 'logs')
db_dir = os.path.join(os.getcwd(), 'database')
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(db_dir, exist_ok=True)

# 환경변수 설정
os.environ.setdefault('DATABASE_URL', f'sqlite:///{os.path.join(db_dir, "coupang_cs.db")}')

# 포트 범위 설정
PORT_RANGE = range(8000, 8021)  # 8000-8020
MAX_RETRY_ATTEMPTS = 100
HEALTH_CHECK_TIMEOUT = 2
HEALTH_CHECK_MAX_ATTEMPTS = 30


def print_progress_bar(current, total, prefix='', suffix='', length=50):
    """진행률 바 출력"""
    filled = int(length * current // total)
    bar = '█' * filled + '░' * (length - filled)
    percent = f'{100 * current / total:.0f}%'
    print(f'\r{prefix} |{bar}| {percent} {suffix}', end='', flush=True)
    if current == total:
        print()


def print_header():
    """헤더 출력"""
    print("\n" + "=" * 70)
    print("  🚀 쿠팡 윙 CS 자동화 시스템 v1.0.0")
    print("  💡 스마트 자동 연결 모드 - ChatGPT 연결 상태 모니터링 기능 탑재")
    print("=" * 70)
    print(f"작업 디렉토리: {os.getcwd()}")
    print(f"로그 디렉토리: {logs_dir}")
    print(f"데이터베이스: {db_dir}")
    print("=" * 70 + "\n")


def is_port_available(port):
    """포트가 사용 가능한지 확인"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except (OSError, socket.error):
        return False


def find_available_port():
    """사용 가능한 포트 찾기 (진행률 표시)"""
    print("🔍 사용 가능한 포트 검색 중...")

    ports = list(PORT_RANGE)
    total_ports = len(ports)

    for idx, port in enumerate(ports, 1):
        print_progress_bar(
            idx, total_ports,
            prefix='  검색 진행',
            suffix=f'포트 {port} 확인 중...'
        )

        if is_port_available(port):
            print(f"\n✓ 포트 {port} 사용 가능 발견!")
            return port

    print()
    return None


def check_backend_health(port, timeout=HEALTH_CHECK_TIMEOUT):
    """백엔드 헬스체크"""
    try:
        import requests
        response = requests.get(
            f"http://localhost:{port}/health",
            timeout=timeout
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('status') in ['healthy', 'degraded']
        return False
    except Exception:
        return False


def wait_for_backend_ready(port, max_attempts=HEALTH_CHECK_MAX_ATTEMPTS):
    """백엔드가 준비될 때까지 대기 (진행률 표시)"""
    print(f"\n⏳ 백엔드 서버 시작 대기 중... (포트: {port})")

    for attempt in range(1, max_attempts + 1):
        print_progress_bar(
            attempt, max_attempts,
            prefix='  헬스체크',
            suffix=f'시도 {attempt}/{max_attempts}'
        )

        if check_backend_health(port):
            print(f"\n✓ 백엔드 서버 준비 완료! ({attempt}번째 시도)")
            return True

        time.sleep(1)

    print(f"\n✗ 백엔드 서버가 {max_attempts}초 내에 준비되지 않았습니다.")
    return False


def start_backend_server(port):
    """백엔드 서버를 별도 스레드에서 시작"""
    def run_server():
        try:
            # uvicorn을 먼저 import해서 설치 여부 확인
            import uvicorn
            from app.main import app

            # 로그 레벨을 warning으로 설정하여 출력 감소
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=port,
                log_level="warning",
                access_log=False
            )
        except ImportError as e:
            print(f"\n❌ 필수 모듈 import 오류: {e}")
            print("   uvicorn이 설치되어 있는지 확인하세요.")
        except Exception as e:
            print(f"\n❌ 백엔드 서버 오류: {e}")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    return server_thread


def open_browser(port):
    """브라우저 열기"""
    print("\n🌐 브라우저를 열고 있습니다...")
    time.sleep(2)

    try:
        url = f"http://localhost:{port}/"
        webbrowser.open(url)
        print(f"✓ 브라우저가 자동으로 열렸습니다!")
        print(f"   URL: {url}")
        return True
    except Exception as e:
        print(f"⚠️  브라우저 자동 열기 실패: {e}")
        print(f"   수동으로 http://localhost:{port}/를 열어주세요.")
        return False


def main():
    """메인 실행 함수"""
    print_header()

    retry_count = 0

    while retry_count < MAX_RETRY_ATTEMPTS:
        retry_count += 1

        if retry_count > 1:
            print(f"\n{'='*70}")
            print(f"🔄 재시도 {retry_count}/{MAX_RETRY_ATTEMPTS}")
            print(f"{'='*70}\n")

        # 1단계: 사용 가능한 포트 찾기
        port = find_available_port()

        if port is None:
            print(f"\n❌ 사용 가능한 포트를 찾을 수 없습니다!")
            print(f"   포트 범위 {PORT_RANGE.start}-{PORT_RANGE.stop-1} 모두 사용 중입니다.")

            if retry_count < MAX_RETRY_ATTEMPTS:
                wait_time = 5
                print(f"\n⏳ {wait_time}초 후 재시도합니다...")
                for i in range(wait_time):
                    print_progress_bar(i+1, wait_time, prefix='  대기 중', suffix='')
                    time.sleep(1)
                print()
                continue
            else:
                print(f"\n❌ 최대 재시도 횟수 ({MAX_RETRY_ATTEMPTS})에 도달했습니다.")
                break

        # 2단계: 백엔드 서버 시작
        print(f"\n🚀 백엔드 서버 시작 중... (포트: {port})")
        server_thread = start_backend_server(port)

        # 3단계: 백엔드 준비 대기
        if not wait_for_backend_ready(port):
            print(f"\n⚠️  백엔드 서버 시작 실패. 다른 포트로 재시도합니다...")
            time.sleep(2)
            continue

        # 4단계: 성공!
        print("\n" + "=" * 70)
        print("  ✅ 서버 연결 성공!")
        print("=" * 70)
        print(f"\n📍 접속 정보:")
        print(f"  - 포트: {port}")
        print(f"  - 대시보드: http://localhost:{port}/")
        print(f"  - API 문서: http://localhost:{port}/docs")
        print(f"  - 헬스체크: http://localhost:{port}/health")
        print(f"\n✨ 새로운 기능:")
        print(f"  - ChatGPT 연결 상태 실시간 모니터링")
        print(f"  - 자동 연결 시도 기능")
        print(f"  - 상세한 연결 정보 표시")
        print(f"\n🛑 종료하려면 Ctrl+C를 누르세요.")
        print("=" * 70 + "\n")

        # 5단계: 브라우저 열기
        browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
        browser_thread.start()

        # 6단계: 서버 실행 유지
        try:
            print("💡 서버가 실행 중입니다. 종료하려면 Ctrl+C를 누르세요.\n")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 서버를 종료합니다...")
            print("잠시만 기다려주세요...\n")
            time.sleep(1)
            return True

    # 모든 재시도 실패
    print("\n" + "=" * 70)
    print("  ❌ 서버 시작 실패")
    print("=" * 70)
    print("\n다음 사항을 확인해주세요:")
    print("  1. 방화벽이 포트를 차단하고 있지 않은지 확인")
    print("  2. 다른 프로그램이 해당 포트를 사용 중인지 확인")
    print("  3. 프로그램을 관리자 권한으로 실행")
    print("  4. 컴퓨터를 재시작 후 다시 시도")
    print("\n" + "=" * 70)
    input("\n종료하려면 Enter 키를 누르세요...")
    return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 사용자에 의해 종료되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        input("\n종료하려면 Enter 키를 누르세요...")
        sys.exit(1)
