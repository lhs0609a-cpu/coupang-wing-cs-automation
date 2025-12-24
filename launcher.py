"""
쿠팡 윙 CS 자동화 시스템 런처
"""
import os
import sys
import uvicorn
import webbrowser
import time
import threading
from pathlib import Path

# Windows 콘솔 인코딩 설정 (이모지 출력을 위해)
if sys.platform == 'win32':
    try:
        import io
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        # 인코딩 설정 실패 시 무시
        pass

# 실행 파일 경로 설정
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 실행 파일
    # sys.executable의 디렉토리를 사용 (exe 파일이 있는 폴더)
    application_path = os.path.dirname(sys.executable)
else:
    # 일반 Python 스크립트
    application_path = os.path.dirname(os.path.abspath(__file__))

# 백엔드 경로 추가
backend_path = os.path.join(application_path, 'backend')

# backend 폴더가 없으면 에러 메시지 출력
if not os.path.exists(backend_path):
    print(f"❌ Error: backend folder not found!")
    print(f"   Expected location: {backend_path}")
    print(f"   Application path: {application_path}")
    print(f"   Current directory: {os.getcwd()}")
    input("\nPress Enter to exit...")
    sys.exit(1)

sys.path.insert(0, backend_path)

# 로그 디렉토리 생성
logs_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# 데이터베이스 디렉토리 생성
db_dir = os.path.join(os.getcwd(), 'database')
os.makedirs(db_dir, exist_ok=True)

PORT = 8000

print("="*60)
print("  🚀 쿠팡 윙 CS 자동화 시스템 v1.0.0")
print("="*60)
print(f"작업 디렉토리: {os.getcwd()}")
print(f"로그 디렉토리: {logs_dir}")
print(f"데이터베이스 디렉토리: {db_dir}")
print("="*60)
print("\n⏳ 서버 시작 중...")
print("\n📍 접속 주소:")
print(f"  - 대시보드: http://localhost:{PORT}/")
print(f"  - API 문서: http://localhost:{PORT}/docs")
print(f"  - API 가이드: http://localhost:{PORT}/redoc")
print("\n🛑 종료하려면 Ctrl+C를 누르세요.")
print("="*60 + "\n")

# 환경변수 설정
os.environ.setdefault('DATABASE_URL', f'sqlite:///{os.path.join(db_dir, "coupang_cs.db")}')

# 브라우저 자동 오픈 함수
def open_browser():
    """서버 시작 후 브라우저 자동 오픈"""
    time.sleep(3)  # 서버 시작 대기
    try:
        webbrowser.open(f"http://localhost:{PORT}/")
        print("\n🌐 브라우저에서 대시보드를 열었습니다!")
    except Exception as e:
        print(f"\n⚠️  브라우저 자동 오픈 실패: {e}")
        print(f"   수동으로 http://localhost:{PORT}/를 열어주세요.")

# 메인 앱 실행
if __name__ == "__main__":
    try:
        from app.main import app

        # 백그라운드에서 브라우저 오픈
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

        # 서버 실행
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=PORT,
            reload=False
        )
    except KeyboardInterrupt:
        print("\n\n🛑 서버를 종료합니다...")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        input("\n종료하려면 Enter 키를 누르세요...")
