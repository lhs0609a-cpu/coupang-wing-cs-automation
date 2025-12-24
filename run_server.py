# -*- coding: utf-8 -*-
"""
Coupang Wing CS - Server Launcher
Run this file to start both frontend and backend servers
"""
import socket
import subprocess
import time
import sys
import os
import webbrowser
import requests
from pathlib import Path
from datetime import datetime

# Windows console UTF-8 setup
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class ProgressBar:
    """Progress bar display"""
    @staticmethod
    def show(current, total, prefix='', suffix='', length=50):
        filled = int(length * current // total)
        bar = '█' * filled + '░' * (length - filled)
        percent = f'{100 * current / total:.1f}%'
        print(f'\r{prefix} |{bar}| {percent} {suffix}', end='', flush=True)
        if current == total:
            print()

class ServerLauncher:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / "backend"
        self.frontend_dir = self.base_dir / "frontend"
        self.venv_python = self.base_dir / "venv" / "Scripts" / "python.exe"

        self.backend_port = None
        self.frontend_port = None
        self.attempt_count = 0

    def print_header(self):
        print("\n" + "=" * 80)
        print("   Coupang Wing CS Automation - Server Launcher")
        print("=" * 80)
        print(f"   Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def print_step(self, step_num, title):
        print(f"\n{'─' * 80}")
        print(f"  STEP {step_num}: {title}")
        print(f"{'─' * 80}")

    def print_status(self, emoji, message, details=None):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {emoji} {message}")
        if details:
            print(f"           {details}")

    def find_free_port(self, start_port, end_port, port_type=""):
        total_ports = end_port - start_port
        checked = 0

        for port in range(start_port, end_port):
            checked += 1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    ProgressBar.show(checked, total_ports,
                                   prefix=f'  Scanning {port_type} ports',
                                   suffix=f'Found: {port}')
                    return port
            except OSError:
                if checked % 5 == 0:
                    ProgressBar.show(checked, total_ports,
                                   prefix=f'  Scanning {port_type} ports',
                                   suffix='Searching...')

        ProgressBar.show(total_ports, total_ports,
                        prefix=f'  Scanning {port_type} ports',
                        suffix='Not found')
        return None

    def update_vite_config(self, backend_port, frontend_port):
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

    def start_backend(self, port):
        cmd = f'start cmd /k "cd /d {self.backend_dir} && {self.venv_python} -m uvicorn app.main:app --host 0.0.0.0 --port {port} --reload"'
        subprocess.Popen(cmd, shell=True)

    def start_frontend(self, port):
        cmd = f'start cmd /k "cd /d {self.frontend_dir} && npm run dev"'
        subprocess.Popen(cmd, shell=True)

    def check_connection(self, url, service_name, max_retries=30):
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code in [200, 304]:
                    ProgressBar.show(attempt, max_retries,
                                   prefix=f'  Connecting to {service_name}',
                                   suffix='CONNECTED!')
                    return True
            except requests.exceptions.RequestException:
                pass

            ProgressBar.show(attempt, max_retries,
                           prefix=f'  Connecting to {service_name}',
                           suffix=f'Attempt {attempt}/{max_retries}...')
            time.sleep(2)

        print()
        return False

    def run_attempt(self):
        self.attempt_count += 1

        print(f"\n{'═' * 80}")
        print(f"  CONNECTION ATTEMPT #{self.attempt_count}")
        print(f"{'═' * 80}")

        # STEP 1: Find ports
        self.print_step(1, "Finding Available Ports")

        self.print_status("🔍", "Searching for backend port...")
        self.backend_port = self.find_free_port(8000, 8100, "Backend")
        if not self.backend_port:
            self.print_status("❌", "No free backend port found (8000-8100)")
            return False
        self.print_status("✅", f"Backend port selected: {self.backend_port}")

        self.print_status("🔍", "Searching for frontend port...")
        self.frontend_port = self.find_free_port(3000, 3100, "Frontend")
        if not self.frontend_port:
            self.print_status("❌", "No free frontend port found (3000-3100)")
            return False
        self.print_status("✅", f"Frontend port selected: {self.frontend_port}")

        # STEP 2: Update config
        self.print_step(2, "Updating Frontend Configuration")
        try:
            self.update_vite_config(self.backend_port, self.frontend_port)
            self.print_status("✅", "Vite config updated successfully",
                            f"Backend: {self.backend_port}, Frontend: {self.frontend_port}")
        except Exception as e:
            self.print_status("❌", f"Failed to update config: {e}")
            return False

        # STEP 3: Start backend
        self.print_step(3, "Starting Backend Server")
        self.print_status("🚀", f"Launching backend on port {self.backend_port}...")
        self.start_backend(self.backend_port)
        self.print_status("⏳", "Waiting 5 seconds for backend initialization...")
        time.sleep(5)

        # STEP 4: Check backend connection
        self.print_step(4, "Verifying Backend Connection")
        backend_url = f"http://localhost:{self.backend_port}/health"
        if not self.check_connection(backend_url, "Backend", max_retries=30):
            self.print_status("❌", "Backend connection failed")
            self.print_status("🔄", "Will retry with different port...")
            time.sleep(3)
            return False

        self.print_status("✅", "Backend is UP and running!")

        # STEP 5: Start frontend
        self.print_step(5, "Starting Frontend Server")
        self.print_status("🚀", f"Launching frontend on port {self.frontend_port}...")
        self.start_frontend(self.frontend_port)
        self.print_status("⏳", "Waiting 5 seconds for frontend initialization...")
        time.sleep(5)

        # STEP 6: Check frontend connection
        self.print_step(6, "Verifying Frontend Connection")
        frontend_url = f"http://localhost:{self.frontend_port}"
        if not self.check_connection(frontend_url, "Frontend", max_retries=20):
            self.print_status("❌", "Frontend connection failed")
            self.print_status("🔄", "Will retry with different port...")
            time.sleep(3)
            return False

        self.print_status("✅", "Frontend is UP and running!")

        # STEP 7: Open browser
        self.print_step(7, "Opening Web Browser")
        self.print_status("🌐", f"Opening {frontend_url} in browser...")
        try:
            webbrowser.open(frontend_url)
            self.print_status("✅", "Browser opened successfully!")
        except Exception as e:
            self.print_status("⚠️", f"Could not open browser: {e}")
            self.print_status("ℹ️", f"Please manually open: {frontend_url}")

        # SUCCESS!
        print(f"\n{'═' * 80}")
        print("  🎉 SUCCESS! ALL SYSTEMS OPERATIONAL!")
        print(f"{'═' * 80}")
        print(f"\n  📊 Server Information:")
        print(f"  ├─ Frontend:  http://localhost:{self.frontend_port}")
        print(f"  ├─ Backend:   http://localhost:{self.backend_port}")
        print(f"  └─ API Docs:  http://localhost:{self.backend_port}/docs")
        print(f"\n  📈 Statistics:")
        print(f"  ├─ Total Attempts: {self.attempt_count}")
        print(f"  └─ Success Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n{'═' * 80}")
        print("  ℹ️  Web browser has been opened automatically")
        print("  ℹ️  To stop servers, close the console windows")
        print(f"{'═' * 80}\n")

        return True

    def run(self):
        self.print_header()

        max_total_attempts = 10

        for attempt in range(max_total_attempts):
            if self.run_attempt():
                input("\nPress Enter to exit this launcher...")
                return True

            if attempt < max_total_attempts - 1:
                wait_time = 5
                self.print_status("⏳", f"Waiting {wait_time} seconds before next attempt...")
                for i in range(wait_time):
                    print(f"  {'.' * (i + 1)}", end='\r', flush=True)
                    time.sleep(1)
                print()

        # All attempts failed
        print(f"\n{'═' * 80}")
        print("  ❌ FAILED: Could not establish connections")
        print(f"{'═' * 80}")
        print(f"\n  Attempted {max_total_attempts} times without success")
        print("\n  Please check:")
        print("  • Backend and frontend directories exist")
        print("  • Python virtual environment (venv) is set up")
        print("  • Node.js and npm are installed")
        print("  • No other services are using ports 8000-8100 or 3000-3100")
        print(f"\n{'═' * 80}\n")

        input("\nPress Enter to exit...")
        return False

def main():
    try:
        launcher = ServerLauncher()
        success = launcher.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Program stopped by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
