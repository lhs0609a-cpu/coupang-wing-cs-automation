"""
쿠팡 윙 CS 자동화 시스템 런처 v2.0.0
"""
import os
import sys
import uvicorn
from pathlib import Path

# 실행 파일 경로 설정
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 실행 파일
    application_path = sys._MEIPASS
else:
    # 일반 Python 스크립트
    application_path = os.path.dirname(os.path.abspath(__file__))

# 백엔드 경로 추가
backend_path = os.path.join(application_path, 'backend')
sys.path.insert(0, backend_path)

# 로그 디렉토리 생성
logs_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# 데이터베이스 디렉토리 생성
db_dir = os.path.join(os.getcwd(), 'database')
os.makedirs(db_dir, exist_ok=True)

print("="*60)
print("  쿠팡 윙 CS 자동화 시스템 v2.0.0")
print("="*60)
print(f"작업 디렉토리: {os.getcwd()}")
print(f"로그 디렉토리: {logs_dir}")
print(f"데이터베이스 디렉토리: {db_dir}")
print("="*60)
print("\n서버 시작 중...")
print("\n접속 주소:")
print("  - http://localhost:8001")
print("  - http://0.0.0.0:8001")
print("\n종료하려면 Ctrl+C를 누르세요.")
print("="*60 + "\n")

# 환경변수 설정
os.environ.setdefault('DATABASE_URL', f'sqlite:///{os.path.join(db_dir, "coupang_cs.db")}')

# 메인 앱 실행
if __name__ == "__main__":
    try:
        from app.main import app
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            reload=False
        )
    except KeyboardInterrupt:
        print("\n\n서버를 종료합니다...")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        input("\n종료하려면 Enter 키를 누르세요...")
