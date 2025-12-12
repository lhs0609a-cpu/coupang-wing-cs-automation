# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# Chrome 및 Selenium 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc g++ curl wget gnupg unzip \
    libnss3 libfontconfig1 libxss1 libasound2 libxtst6 libgtk-3-0 libgbm1 xvfb \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치 (최신 방식)
RUN wget -q -O /tmp/google-chrome-stable.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y /tmp/google-chrome-stable.deb \
    && rm /tmp/google-chrome-stable.deb \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver 설치 (Chrome for Testing 사용)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1-3) \
    && wget -q "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION}" -O /tmp/chromedriver_version.txt \
    && CHROMEDRIVER_VERSION=$(cat /tmp/chromedriver_version.txt) \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64 /tmp/chromedriver_version.txt

# Python 의존성 파일 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저 설치
RUN playwright install chromium --with-deps

# 애플리케이션 코드 복사
COPY . .

# 로그 및 데이터베이스 디렉토리 생성
RUN mkdir -p /app/logs /app/database /data

# startup.sh 실행 권한 부여
RUN chmod +x /app/startup.sh

# 포트 노출
EXPOSE 8080

# 환경변수 설정
ENV PYTHONUNBUFFERED=1 PORT=8080 DISPLAY=:99

# startup.sh로 서버 실행 (마이그레이션 포함)
CMD ["/app/startup.sh"]
