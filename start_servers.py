# -*- coding: utf-8 -*-
"""
프론트엔드와 백엔드 서버를 자동으로 시작하는 간단한 스크립트
"""
import socket
import subprocess
import time
import sys
import os
from pathlib import Path

def find_free_port(start_port=8000, end_port=9000):
    """사용 가능한 빈 포트 찾기"""
    for port in range(start_port, end_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    return None

def update_vite_config(backend_port, frontend_port):
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

    print(f"[OK] Vite config updated: Frontend={frontend_port}, Backend={backend_port}")

def main():
    print("=" * 60)
    print("Coupang Wing CS - Auto Start System")
    print("=" * 60)

    # 1. Find free ports
    print("\n[1] Finding free ports...")
    backend_port = find_free_port(8000, 8100)
    if not backend_port:
        print("[ERROR] No free port for backend")
        return False
    print(f"[OK] Backend port: {backend_port}")

    frontend_port = find_free_port(3000, 3100)
    if not frontend_port:
        print("[ERROR] No free port for frontend")
        return False
    print(f"[OK] Frontend port: {frontend_port}")

    # 2. Update vite config
    print("\n[2] Updating vite config...")
    update_vite_config(backend_port, frontend_port)

    # 3. Start backend
    print(f"\n[3] Starting backend server on port {backend_port}...")
    backend_dir = Path(__file__).parent / "backend"
    venv_python = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
    backend_cmd = f'start cmd /k "cd /d {backend_dir} && {venv_python} -m uvicorn app.main:app --host 0.0.0.0 --port {backend_port} --reload"'
    subprocess.Popen(backend_cmd, shell=True)
    print("[OK] Backend server starting in new window...")

    # Wait for backend to start
    print("[WAIT] Waiting 10 seconds for backend to initialize...")
    time.sleep(10)

    # 4. Start frontend
    print(f"\n[4] Starting frontend server on port {frontend_port}...")
    frontend_dir = Path(__file__).parent / "frontend"
    frontend_cmd = f'start cmd /k "cd /d {frontend_dir} && npm run dev"'
    subprocess.Popen(frontend_cmd, shell=True)
    print("[OK] Frontend server starting in new window...")

    # 5. Show URLs
    print("\n" + "=" * 60)
    print("[SUCCESS] Servers are starting!")
    print("=" * 60)
    print(f"Backend:  http://localhost:{backend_port}")
    print(f"Frontend: http://localhost:{frontend_port}")
    print(f"API Docs: http://localhost:{backend_port}/docs")
    print("=" * 60)
    print("\nPlease check the new console windows for server output.")
    print("Press Ctrl+C in those windows to stop the servers.")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[DONE] Script completed. Servers are running in separate windows.")
    else:
        print("\n[FAILED] Could not start servers.")

    input("\nPress Enter to exit...")
