# -*- coding: utf-8 -*-
"""
Coupang Wing CS 자동화 시스템 - 최종 실행 파일
빈 포트 자동 탐색, 자동 연결 재시도, 웹 브라우저 자동 실행
"""
import socket
import subprocess
import time
import sys
import os
import webbrowser
import requests
from pathlib import Path

# Windows 콘솔 UTF-8 설정
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class ServerManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / "backend"
        self.frontend_dir = self.base_dir / "frontend"
        self.venv_python = self.base_dir / "venv" / "Scripts" / "python.exe"

        self.backend_port = None
        self.frontend_port = None
        self.backend_process = None
        self.frontend_process = None

    def find_free_port(self, start_port=8000, end_port=9000):
        """사용 가능한 빈 포트 찾기"""
        for port in range(start_port, end_port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
        return None

    def update_vite_config(self, backend_port, frontend_port):
        """Vite 설정 파일 업데이트"""
        vite_config_path = self.frontend_dir / "vite.config.js"

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

        print(f"[OK] Vite config updated: Frontend={frontend_port}, Backend={backend_port}")

    def start_backend(self, port):
        """백엔드 서버 시작"""
        print(f"\n[START] Starting backend on port {port}...")

        cmd = f'start cmd /k "cd /d {self.backend_dir} && {self.venv_python} -m uvicorn app.main:app --host 0.0.0.0 --port {port} --reload"'
        subprocess.Popen(cmd, shell=True)

        print(f"[OK] Backend server starting...")
        return True

    def start_frontend(self, port):
        """프론트엔드 서버 시작"""
        print(f"\n[START] Starting frontend on port {port}...")

        cmd = f'start cmd /k "cd /d {self.frontend_dir} && npm run dev"'
        subprocess.Popen(cmd, shell=True)

        print(f"[OK] Frontend server starting...")
        return True

    def check_backend_connection(self, port, max_retries=30, delay=2):
        """백엔드 연결 확인 (자동 재시도)"""
        print(f"\n[CHECK] Checking backend connection on port {port}...")
        health_url = f"http://localhost:{port}/health"

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    print(f"[SUCCESS] Backend connected! (attempt {attempt}/{max_retries})")
                    return True
            except requests.exceptions.RequestException:
                pass

            print(f"[RETRY] Waiting for backend... ({attempt}/{max_retries})")
            time.sleep(delay)

        print(f"[FAIL] Backend connection failed after {max_retries} attempts")
        return False

    def check_frontend_connection(self, port, max_retries=20, delay=2):
        """프론트엔드 연결 확인 (자동 재시도)"""
        print(f"\n[CHECK] Checking frontend connection on port {port}...")
        frontend_url = f"http://localhost:{port}"

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(frontend_url, timeout=5)
                if response.status_code in [200, 304]:
                    print(f"[SUCCESS] Frontend connected! (attempt {attempt}/{max_retries})")
                    return True
            except requests.exceptions.RequestException:
                pass

            print(f"[RETRY] Waiting for frontend... ({attempt}/{max_retries})")
            time.sleep(delay)

        print(f"[FAIL] Frontend connection failed after {max_retries} attempts")
        return False

    def open_browser(self, url):
        """웹 브라우저 자동 열기"""
        print(f"\n[BROWSER] Opening {url} in web browser...")
        try:
            webbrowser.open(url)
            print(f"[OK] Browser opened successfully!")
            return True
        except Exception as e:
            print(f"[WARNING] Could not open browser: {e}")
            print(f"[INFO] Please manually open: {url}")
            return False

    def run(self):
        """메인 실행 함수"""
        print("=" * 70)
        print("Coupang Wing CS Automation System - FINAL LAUNCHER")
        print("=" * 70)

        max_attempts = 3  # 최대 3번까지 다른 포트로 재시도

        for main_attempt in range(1, max_attempts + 1):
            print(f"\n{'='*70}")
            print(f"ATTEMPT {main_attempt}/{max_attempts}")
            print(f"{'='*70}")

            # 1. Find free ports
            print(f"\n[1] Finding free ports...")
            self.backend_port = self.find_free_port(8000, 8100)
            if not self.backend_port:
                print("[ERROR] No free port for backend (8000-8100)")
                continue
            print(f"[OK] Backend port: {self.backend_port}")

            self.frontend_port = self.find_free_port(3000, 3100)
            if not self.frontend_port:
                print("[ERROR] No free port for frontend (3000-3100)")
                continue
            print(f"[OK] Frontend port: {self.frontend_port}")

            # 2. Update vite config
            print(f"\n[2] Updating frontend configuration...")
            try:
                self.update_vite_config(self.backend_port, self.frontend_port)
            except Exception as e:
                print(f"[ERROR] Failed to update vite config: {e}")
                continue

            # 3. Start backend
            print(f"\n[3] Starting backend server...")
            if not self.start_backend(self.backend_port):
                continue

            time.sleep(5)  # 백엔드 초기화 대기

            # 4. Check backend connection
            print(f"\n[4] Verifying backend connection...")
            if not self.check_backend_connection(self.backend_port):
                print(f"[WARNING] Backend connection failed on port {self.backend_port}")
                print(f"[INFO] Will retry with different port...")
                time.sleep(2)
                continue

            # 5. Start frontend
            print(f"\n[5] Starting frontend server...")
            if not self.start_frontend(self.frontend_port):
                continue

            time.sleep(5)  # 프론트엔드 초기화 대기

            # 6. Check frontend connection
            print(f"\n[6] Verifying frontend connection...")
            if not self.check_frontend_connection(self.frontend_port):
                print(f"[WARNING] Frontend connection failed on port {self.frontend_port}")
                print(f"[INFO] Will retry with different port...")
                time.sleep(2)
                continue

            # 7. Open browser automatically
            print(f"\n[7] Opening web browser...")
            frontend_url = f"http://localhost:{self.frontend_port}"
            self.open_browser(frontend_url)

            # SUCCESS!
            print(f"\n{'='*70}")
            print("SUCCESS! ALL SERVERS ARE RUNNING!")
            print(f"{'='*70}")
            print(f"\nServer Information:")
            print(f"  Frontend:  http://localhost:{self.frontend_port}")
            print(f"  Backend:   http://localhost:{self.backend_port}")
            print(f"  API Docs:  http://localhost:{self.backend_port}/docs")
            print(f"\n{'='*70}")
            print("Web browser has been opened automatically!")
            print("To stop the servers, close the console windows.")
            print(f"{'='*70}")

            input("\nPress Enter to exit this launcher...")
            return True

        # All attempts failed
        print(f"\n{'='*70}")
        print("FAILED!")
        print(f"{'='*70}")
        print(f"Could not start servers after {max_attempts} attempts.")
        print("Please check:")
        print("  1. Backend directory exists and has correct structure")
        print("  2. Frontend directory exists and has correct structure")
        print("  3. Python virtual environment (venv) is set up")
        print("  4. Node.js and npm are installed")
        print(f"{'='*70}")

        input("\nPress Enter to exit...")
        return False

def main():
    try:
        manager = ServerManager()
        success = manager.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Program interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
