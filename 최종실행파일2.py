"""
쿠팡 윙 CS 자동화 시스템 - 프론트엔드/백엔드 분리 실행 런처
프론트엔드와 백엔드를 각각 별도 포트에서 실행하고 자동으로 연결합니다.
"""
import os
import sys
import time
import socket
import subprocess
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

# 경로 설정
BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / 'backend'
FRONTEND_DIR = BASE_DIR / 'frontend'

# 디렉토리 생성
LOGS_DIR = BASE_DIR / 'logs'
DB_DIR = BASE_DIR / 'database'
LOGS_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# 포트 범위 설정
BACKEND_PORT_RANGE = range(8000, 8021)
FRONTEND_PORT_RANGE = range(3000, 3021)
MAX_RETRY_ATTEMPTS = 50
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
    print("  💡 프론트엔드/백엔드 분리 실행 모드")
    print("=" * 70)
    print(f"작업 디렉토리: {BASE_DIR}")
    print(f"백엔드 디렉토리: {BACKEND_DIR}")
    print(f"프론트엔드 디렉토리: {FRONTEND_DIR}")
    print(f"로그 디렉토리: {LOGS_DIR}")
    print(f"데이터베이스: {DB_DIR}")
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


def find_available_port(port_range, service_name=""):
    """사용 가능한 포트 찾기 (진행률 표시)"""
    print(f"🔍 {service_name} 포트 검색 중...")

    ports = list(port_range)
    total_ports = len(ports)

    for idx, port in enumerate(ports, 1):
        print_progress_bar(
            idx, total_ports,
            prefix=f'  {service_name} 검색',
            suffix=f'포트 {port} 확인 중...'
        )

        if is_port_available(port):
            print(f"\n✓ {service_name} 포트 {port} 사용 가능 발견!")
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


def check_frontend_ready(port, timeout=HEALTH_CHECK_TIMEOUT):
    """프론트엔드 준비 확인"""
    try:
        import requests
        response = requests.get(
            f"http://localhost:{port}/",
            timeout=timeout
        )
        return response.status_code in [200, 304]
    except Exception:
        return False


def wait_for_service_ready(port, service_name, check_function, max_attempts=HEALTH_CHECK_MAX_ATTEMPTS):
    """서비스가 준비될 때까지 대기 (진행률 표시)"""
    print(f"\n⏳ {service_name} 시작 대기 중... (포트: {port})")

    for attempt in range(1, max_attempts + 1):
        print_progress_bar(
            attempt, max_attempts,
            prefix=f'  {service_name} 확인',
            suffix=f'시도 {attempt}/{max_attempts}'
        )

        if check_function(port):
            print(f"\n✓ {service_name} 준비 완료! ({attempt}번째 시도)")
            return True

        time.sleep(1)

    print(f"\n✗ {service_name}가 {max_attempts}초 내에 준비되지 않았습니다.")
    return False


def update_vite_config(backend_port, frontend_port):
    """Vite 설정 파일 업데이트 (백엔드 프록시 설정)"""
    vite_config_path = FRONTEND_DIR / "vite.config.js"

    config_content = f"""import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({{
  plugins: [react()],
  base: './',
  server: {{
    port: {frontend_port},
    proxy: {{
      '/api': {{
        target: 'http://localhost:{backend_port}',
        changeOrigin: true
      }}
    }}
  }}
}})
"""

    with open(vite_config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print(f"✓ Vite 설정 업데이트 완료 (Backend: {backend_port}, Frontend: {frontend_port})")


def start_backend_server(port):
    """백엔드 서버 시작 (별도 프로세스)"""
    print(f"\n🚀 백엔드 서버 시작 중... (포트: {port})")

    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--log-level", "warning"
    ]

    # 백엔드 디렉토리에서 실행
    process = subprocess.Popen(
        cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )

    return process


def start_frontend_server(port):
    """프론트엔드 서버 시작 (별도 프로세스)"""
    print(f"\n🚀 프론트엔드 서버 시작 중... (포트: {port})")

    # npm run dev 실행
    cmd = ["npm", "run", "dev"]

    # 환경변수로 포트 설정
    env = os.environ.copy()
    env['PORT'] = str(port)

    # 프론트엔드 디렉토리에서 실행
    process = subprocess.Popen(
        cmd,
        cwd=FRONTEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )

    return process


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


def cleanup_processes(*processes):
    """프로세스 종료"""
    for process in processes:
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass


def main():
    """메인 실행 함수"""
    print_header()

    backend_process = None
    frontend_process = None
    retry_count = 0

    try:
        while retry_count < MAX_RETRY_ATTEMPTS:
            retry_count += 1

            if retry_count > 1:
                print(f"\n{'='*70}")
                print(f"🔄 재시도 {retry_count}/{MAX_RETRY_ATTEMPTS}")
                print(f"{'='*70}\n")

            # 이전 프로세스 정리
            cleanup_processes(backend_process, frontend_process)
            backend_process = None
            frontend_process = None

            # 1단계: 백엔드 포트 찾기
            backend_port = find_available_port(BACKEND_PORT_RANGE, "백엔드")
            if backend_port is None:
                print(f"\n❌ 사용 가능한 백엔드 포트를 찾을 수 없습니다!")
                if retry_count < MAX_RETRY_ATTEMPTS:
                    print(f"⏳ 5초 후 재시도합니다...")
                    time.sleep(5)
                    continue
                else:
                    break

            # 2단계: 프론트엔드 포트 찾기
            frontend_port = find_available_port(FRONTEND_PORT_RANGE, "프론트엔드")
            if frontend_port is None:
                print(f"\n❌ 사용 가능한 프론트엔드 포트를 찾을 수 없습니다!")
                if retry_count < MAX_RETRY_ATTEMPTS:
                    print(f"⏳ 5초 후 재시도합니다...")
                    time.sleep(5)
                    continue
                else:
                    break

            # 3단계: Vite 설정 업데이트
            print(f"\n⚙️  설정 파일 업데이트 중...")
            try:
                update_vite_config(backend_port, frontend_port)
            except Exception as e:
                print(f"❌ 설정 파일 업데이트 실패: {e}")
                continue

            # 4단계: 백엔드 서버 시작
            try:
                backend_process = start_backend_server(backend_port)
                time.sleep(2)  # 초기화 시간
            except Exception as e:
                print(f"❌ 백엔드 서버 시작 실패: {e}")
                continue

            # 5단계: 백엔드 준비 대기
            if not wait_for_service_ready(backend_port, "백엔드", check_backend_health):
                print(f"\n⚠️  백엔드 서버 시작 실패. 재시도합니다...")
                time.sleep(2)
                continue

            # 6단계: 프론트엔드 서버 시작
            try:
                frontend_process = start_frontend_server(frontend_port)
                time.sleep(3)  # 초기화 시간
            except Exception as e:
                print(f"❌ 프론트엔드 서버 시작 실패: {e}")
                continue

            # 7단계: 프론트엔드 준비 대기
            if not wait_for_service_ready(frontend_port, "프론트엔드", check_frontend_ready, max_attempts=40):
                print(f"\n⚠️  프론트엔드 서버 시작 실패. 재시도합니다...")
                time.sleep(2)
                continue

            # 8단계: 성공!
            print("\n" + "=" * 70)
            print("  ✅ 프론트엔드 & 백엔드 연결 성공!")
            print("=" * 70)
            print(f"\n📍 접속 정보:")
            print(f"  - 프론트엔드: http://localhost:{frontend_port}/")
            print(f"  - 백엔드: http://localhost:{backend_port}/")
            print(f"  - API 문서: http://localhost:{backend_port}/docs")
            print(f"  - 헬스체크: http://localhost:{backend_port}/health")
            print(f"\n✨ 기능:")
            print(f"  - 프론트엔드 Hot Reload (Vite Dev Server)")
            print(f"  - 백엔드 API 자동 프록시")
            print(f"  - ChatGPT 연결 상태 모니터링")
            print(f"\n🛑 종료하려면 Ctrl+C를 누르세요.")
            print("=" * 70 + "\n")

            # 9단계: 브라우저 열기
            browser_thread = threading.Thread(
                target=open_browser,
                args=(frontend_port,),
                daemon=True
            )
            browser_thread.start()

            # 10단계: 서버 실행 유지
            print("💡 서버가 실행 중입니다. 종료하려면 Ctrl+C를 누르세요.\n")
            while True:
                # 프로세스가 살아있는지 확인
                if backend_process and backend_process.poll() is not None:
                    print("\n⚠️  백엔드 프로세스가 종료되었습니다.")
                    break
                if frontend_process and frontend_process.poll() is not None:
                    print("\n⚠️  프론트엔드 프로세스가 종료되었습니다.")
                    break
                time.sleep(1)

            # 프로세스가 종료되면 재시도
            print("\n🔄 프로세스 재시작을 시도합니다...")
            time.sleep(3)

    except KeyboardInterrupt:
        print("\n\n🛑 서버를 종료합니다...")
        cleanup_processes(backend_process, frontend_process)
        print("잠시만 기다려주세요...\n")
        time.sleep(1)
        return True

    finally:
        cleanup_processes(backend_process, frontend_process)

    # 모든 재시도 실패
    print("\n" + "=" * 70)
    print("  ❌ 서버 시작 실패")
    print("=" * 70)
    print("\n다음 사항을 확인해주세요:")
    print("  1. Node.js와 npm이 설치되어 있는지 확인")
    print("  2. frontend 폴더에 node_modules가 있는지 확인 (npm install)")
    print("  3. Python 가상환경이 활성화되어 있는지 확인")
    print("  4. 방화벽이 포트를 차단하고 있지 않은지 확인")
    print("  5. 다른 프로그램이 해당 포트를 사용 중인지 확인")
    print("\n" + "=" * 70)
    input("\n종료하려면 Enter 키를 누르세요...")
    return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        input("\n종료하려면 Enter 키를 누르세요...")
        sys.exit(1)
