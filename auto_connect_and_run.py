"""
자동 포트 찾기 및 프론트엔드-백엔드 연결 스크립트
빈 포트를 찾아서 자동으로 연결하고 서버를 실행합니다.
"""
import socket
import subprocess
import time
import sys
import os
import json
import requests
from pathlib import Path

# Windows에서 UTF-8 출력 설정
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def find_free_port(start_port=8000, end_port=9000):
    """사용 가능한 빈 포트 찾기"""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                s.close()
                return port
            except OSError:
                continue
    raise RuntimeError(f"포트 {start_port}-{end_port} 범위에서 사용 가능한 포트를 찾을 수 없습니다.")

def check_port_in_use(port):
    """특정 포트가 사용 중인지 확인"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True

def update_vite_config(backend_port, frontend_port=3030):
    """Vite 설정 파일 업데이트"""
    vite_config_path = Path(__file__).parent / "frontend" / "vite.config.js"

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

    print(f"✅ Vite 설정 업데이트 완료: 프론트엔드 포트={frontend_port}, 백엔드 포트={backend_port}")

def check_backend_health(port, max_retries=30, delay=2):
    """백엔드 서버 연결 확인 (최대 30번 재시도)"""
    health_url = f"http://localhost:{port}/health"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ 백엔드 서버 연결 성공! (시도 {attempt}/{max_retries})")
                return True
        except requests.exceptions.RequestException:
            pass

        print(f"⏳ 백엔드 서버 연결 대기 중... ({attempt}/{max_retries})")
        time.sleep(delay)

    print(f"❌ 백엔드 서버 연결 실패 (최대 재시도 횟수 초과)")
    return False

def check_frontend_health(port, max_retries=20, delay=2):
    """프론트엔드 서버 연결 확인"""
    frontend_url = f"http://localhost:{port}"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(frontend_url, timeout=5)
            if response.status_code in [200, 304]:
                print(f"✅ 프론트엔드 서버 연결 성공! (시도 {attempt}/{max_retries})")
                return True
        except requests.exceptions.RequestException:
            pass

        print(f"⏳ 프론트엔드 서버 연결 대기 중... ({attempt}/{max_retries})")
        time.sleep(delay)

    print(f"❌ 프론트엔드 서버 연결 실패 (최대 재시도 횟수 초과)")
    return False

def start_backend(port):
    """백엔드 서버 시작"""
    backend_dir = Path(__file__).parent / "backend"

    # Python 경로 확인
    python_exe = sys.executable

    print(f"🚀 백엔드 서버 시작 중 (포트: {port})...")

    # uvicorn으로 백엔드 시작
    cmd = [
        python_exe, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ]

    process = subprocess.Popen(
        cmd,
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )

    return process

def start_frontend(port):
    """프론트엔드 서버 시작"""
    frontend_dir = Path(__file__).parent / "frontend"

    print(f"🚀 프론트엔드 서버 시작 중 (포트: {port})...")

    # npm run dev로 프론트엔드 시작
    cmd = ["npm.cmd" if sys.platform == "win32" else "npm", "run", "dev"]

    process = subprocess.Popen(
        cmd,
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )

    return process

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🔧 Coupang Wing CS 자동 연결 및 실행 시스템")
    print("=" * 60)

    try:
        # 1. 빈 포트 찾기
        print("\n📡 1단계: 사용 가능한 포트 찾기...")
        backend_port = find_free_port(8000, 8100)
        print(f"✅ 백엔드 포트: {backend_port}")

        frontend_port = find_free_port(3000, 3100)
        print(f"✅ 프론트엔드 포트: {frontend_port}")

        # 2. Vite 설정 업데이트
        print("\n⚙️  2단계: 프론트엔드 설정 업데이트...")
        update_vite_config(backend_port, frontend_port)

        # 3. 백엔드 서버 시작
        print("\n🚀 3단계: 백엔드 서버 시작...")
        backend_process = start_backend(backend_port)
        time.sleep(3)  # 초기 시작 대기

        # 4. 백엔드 연결 확인 (자동 재시도)
        print("\n🔍 4단계: 백엔드 서버 연결 확인...")
        if not check_backend_health(backend_port):
            print("❌ 백엔드 서버 연결 실패. 프로세스를 종료합니다.")
            backend_process.terminate()
            return False

        # 5. 프론트엔드 서버 시작
        print("\n🚀 5단계: 프론트엔드 서버 시작...")
        frontend_process = start_frontend(frontend_port)
        time.sleep(3)  # 초기 시작 대기

        # 6. 프론트엔드 연결 확인
        print("\n🔍 6단계: 프론트엔드 서버 연결 확인...")
        if not check_frontend_health(frontend_port):
            print("⚠️  프론트엔드 서버 연결 실패했지만 백엔드는 정상 작동 중입니다.")

        # 7. 성공 메시지 출력
        print("\n" + "=" * 60)
        print("✅ 서버 실행 완료!")
        print("=" * 60)
        print(f"🌐 백엔드: http://localhost:{backend_port}")
        print(f"🌐 프론트엔드: http://localhost:{frontend_port}")
        print(f"📚 API 문서: http://localhost:{backend_port}/docs")
        print("=" * 60)
        print("\n⏸️  서버를 종료하려면 Ctrl+C를 누르세요...")

        # 서버 프로세스가 종료될 때까지 대기
        try:
            backend_process.wait()
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\n\n🛑 서버 종료 중...")
            backend_process.terminate()
            frontend_process.terminate()
            print("✅ 서버가 종료되었습니다.")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
