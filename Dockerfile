# 백엔드 FastAPI Dockerfile for Fly.io (Playwright 지원)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 Playwright 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    gnupg \
    # Playwright Chromium 의존성
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저 설치
RUN playwright install chromium

# 애플리케이션 코드 복사
COPY backend/ ./backend/
# .env는 Fly.io secrets로 관리

# 데이터베이스 디렉토리 생성
RUN mkdir -p /app/database

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 8080

# startup.sh 복사
COPY backend/startup.sh ./
RUN chmod +x startup.sh

# 애플리케이션 실행 (마이그레이션 포함)
CMD ["sh", "-c", "python backend/migrate_account_sets_table.py && python backend/migrate_naverpay_schedule_history.py && uvicorn backend.app.main:app --host 0.0.0.0 --port 8080"]
