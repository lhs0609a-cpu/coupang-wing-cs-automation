"""
백엔드 서버 시작 스크립트 (올바른 경로로)
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

print(f"Python path: {backend_dir}")
print(f"Current directory: {os.getcwd()}")

# uvicorn 실행
import uvicorn

if __name__ == "__main__":
    os.chdir(backend_dir)
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
