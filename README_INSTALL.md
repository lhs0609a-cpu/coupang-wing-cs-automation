# 📦 Coupang Wing CS 자동화 시스템 - 설치 가이드

> **초보자를 위한 상세한 설치 및 실행 가이드**

---

## 📋 목차

1. [시스템 요구사항](#-시스템-요구사항)
2. [설치 전 준비사항](#-설치-전-준비사항)
3. [빠른 시작 (원클릭 설치)](#-빠른-시작-원클릭-설치)
4. [수동 설치](#-수동-설치)
5. [환경 설정](#-환경-설정)
6. [서버 실행](#-서버-실행)
7. [문제 해결](#-문제-해결)
8. [업데이트 및 배포](#-업데이트-및-배포)
9. [FAQ (자주 묻는 질문)](#-faq-자주-묻는-질문)

---

## 📌 시스템 요구사항

### 필수 요구사항

| 항목 | 요구사항 |
|------|---------|
| **운영체제** | Windows 10+, macOS 10.14+, Ubuntu 18.04+ |
| **Python** | 3.8 이상 (권장: 3.11) |
| **메모리** | 최소 512MB RAM |
| **디스크 공간** | 최소 1GB 여유 공간 |
| **네트워크** | 인터넷 연결 (OpenAI API 사용) |

### 권장 사양

- **메모리**: 2GB 이상
- **CPU**: 2코어 이상
- **디스크**: SSD

---

## 🛠️ 설치 전 준비사항

### 1. Python 설치 확인

#### Windows
```cmd
python --version
```

출력 예시: `Python 3.11.0`

Python이 없다면 [공식 사이트](https://www.python.org/downloads/)에서 다운로드하세요.

#### Mac
```bash
python3 --version
```

Python이 없다면:
```bash
brew install python3
```

#### Linux (Ubuntu/Debian)
```bash
python3 --version
```

Python이 없다면:
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

### 2. OpenAI API 키 준비

이 시스템은 OpenAI GPT-4를 사용합니다.

1. [OpenAI 웹사이트](https://platform.openai.com/)에 가입
2. **API Keys** 메뉴에서 새 API 키 생성
3. 생성된 키를 안전한 곳에 복사 (한 번만 표시됨)

---

## 🚀 빠른 시작 (원클릭 설치)

가장 쉬운 방법입니다! 단 한 번의 클릭으로 모든 것이 설치됩니다.

### Windows

1. 프로젝트 폴더로 이동
2. `install.bat` 더블클릭 또는 다음 명령 실행:
   ```cmd
   install.bat
   ```

### Mac/Linux

1. 터미널을 열고 프로젝트 폴더로 이동
2. 스크립트에 실행 권한 부여:
   ```bash
   chmod +x install.sh
   ```
3. 설치 실행:
   ```bash
   ./install.sh
   ```

### 설치 과정

설치 스크립트는 다음을 자동으로 수행합니다:

1. ✅ Python 버전 확인 (3.8+)
2. ✅ pip 업그레이드
3. ✅ 가상환경 생성 (선택적)
4. ✅ 필요한 패키지 설치
5. ✅ 환경 설정 파일 (.env) 생성
6. ✅ 필수 폴더 생성
7. ✅ 데이터베이스 초기화
8. ✅ 시스템 자가 진단

**예상 소요 시간**: 3-5분

---

## 🔧 수동 설치

원클릭 설치가 실패하거나 세부 제어가 필요한 경우:

### 1단계: 가상환경 생성 (권장)

#### Windows
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
```

#### Mac/Linux
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2단계: 패키지 설치

```bash
pip install -r requirements.txt
```

### 3단계: 환경 설정 파일 생성

```bash
# .env.example을 .env로 복사
cp .env.example .env
```

### 4단계: 필수 폴더 생성

#### Windows
```cmd
mkdir logs data error_reports backend\logs
```

#### Mac/Linux
```bash
mkdir -p logs data error_reports backend/logs
```

### 5단계: 데이터베이스 초기화

```bash
python -c "import sys; sys.path.insert(0, 'backend'); from app.database import init_db; init_db()"
```

### 6단계: 자가 진단 실행

```bash
python health_check.py
```

---

## ⚙️ 환경 설정

### .env 파일 편집

설치 후 **반드시** `backend/.env` 파일을 편집해야 합니다.

#### Windows
```cmd
notepad backend\.env
```

#### Mac/Linux
```bash
nano backend/.env
# 또는
vim backend/.env
```

### 필수 설정 항목

```ini
# OpenAI API 설정 (필수)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 데이터베이스 설정
DATABASE_URL=sqlite:///./coupang_wing.db

# 서버 설정
HOST=0.0.0.0
PORT=8080
RELOAD=true

# 로그 설정
LOG_LEVEL=INFO

# 보안 설정 (운영 환경에서 변경 권장)
SECRET_KEY=your-secret-key-here-change-in-production
```

### 중요 설정 설명

| 설정 | 설명 | 예시 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API 키 (필수) | `sk-abc123...` |
| `DATABASE_URL` | 데이터베이스 경로 | `sqlite:///./coupang_wing.db` |
| `PORT` | 서버 포트 번호 | `8080` |
| `LOG_LEVEL` | 로그 레벨 | `INFO`, `DEBUG`, `WARNING` |
| `SECRET_KEY` | 암호화 키 (운영 시 변경 필수) | 랜덤 문자열 |

---

## 🏃 서버 실행

### 원클릭 실행

#### Windows
```cmd
run.bat
```
또는 더블클릭

#### Mac/Linux
```bash
chmod +x run.sh
./run.sh
```

### 수동 실행

가상환경을 활성화한 후:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 서버 접속

서버가 시작되면 다음 주소로 접속할 수 있습니다:

- **메인 페이지**: http://localhost:8080
- **API 문서 (Swagger)**: http://localhost:8080/docs
- **대체 API 문서 (ReDoc)**: http://localhost:8080/redoc

### 서버 중단

- **Windows/Mac/Linux**: `Ctrl + C`

---

## 🔍 문제 해결

### 일반적인 문제

#### 1. Python을 찾을 수 없음

**증상**:
```
'python'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다.
```

**해결 방법**:
1. Python 설치 확인: https://www.python.org/downloads/
2. 설치 시 "Add Python to PATH" 체크박스 선택
3. 설치 후 컴퓨터 재부팅

#### 2. 모듈을 찾을 수 없음 (ModuleNotFoundError)

**증상**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**해결 방법**:
```bash
# 패키지 재설치
pip install -r requirements.txt

# 또는 특정 패키지만 설치
pip install fastapi
```

#### 3. 포트가 이미 사용 중

**증상**:
```
Error: [Errno 48] Address already in use
```

**해결 방법**:

**Windows**:
```cmd
# 8080 포트를 사용하는 프로세스 찾기
netstat -ano | findstr :8080

# 프로세스 종료 (PID 확인 후)
taskkill /PID <PID> /F
```

**Mac/Linux**:
```bash
# 8080 포트를 사용하는 프로세스 찾기
lsof -i :8080

# 프로세스 종료
kill -9 <PID>
```

또는 `.env` 파일에서 다른 포트로 변경:
```ini
PORT=8081
```

#### 4. 데이터베이스 초기화 실패

**해결 방법**:
```bash
# 기존 데이터베이스 삭제 (백업 후 실행)
rm backend/coupang_wing.db

# 재초기화
python -c "import sys; sys.path.insert(0, 'backend'); from app.database import init_db; init_db()"
```

#### 5. OpenAI API 키 오류

**증상**:
```
AuthenticationError: Incorrect API key provided
```

**해결 방법**:
1. `backend/.env` 파일 열기
2. `OPENAI_API_KEY` 값 확인
3. OpenAI 대시보드에서 키 재생성
4. 서버 재시작

### 자동 진단 도구

시스템에 문제가 있을 때:

```bash
python health_check.py
```

이 도구는 다음을 확인합니다:
- ✅ Python 버전
- ✅ 필수 파일 존재 여부
- ✅ 환경 변수 설정
- ✅ 패키지 설치 상태
- ✅ 데이터베이스 연결
- ✅ 포트 사용 가능 여부
- ✅ 디스크 공간
- ✅ 메모리

자동으로 문제를 해결하려 시도하며, 실패 시 `health_check_report.txt`를 생성합니다.

### 에러 리포트

처리되지 않은 오류가 발생하면 자동으로 `error_reports/` 폴더에 상세한 리포트가 저장됩니다.

리포트 파일명 예시:
```
error_reports/error_report_20250115_143022.txt
```

이 파일에는 다음이 포함됩니다:
- 시스템 정보
- 오류 상세 내용
- 코드 컨텍스트
- 문제 원인 분석
- 단계별 해결 방법

---

## 🔄 업데이트 및 배포

### 버전 확인

현재 설치된 버전 확인:

```bash
cat version.txt
```

### 새 버전으로 업데이트

1. 최신 배포 패키지 다운로드
2. 기존 `.env` 파일과 데이터베이스 백업
3. 새 버전으로 덮어쓰기
4. 패키지 재설치:
   ```bash
   pip install -r requirements.txt --upgrade
   ```
5. 서버 재시작

### 배포 패키지 생성 (개발자용)

새 버전을 배포하려면:

```bash
python auto_deploy.py
```

대화형 프로세스가 시작됩니다:
1. 버전 증가 타입 선택 (MAJOR/MINOR/PATCH)
2. 변경사항 입력
3. 배포 패키지 자동 생성

---

## ❓ FAQ (자주 묻는 질문)

### Q1: 가상환경을 꼭 사용해야 하나요?

**A**: 필수는 아니지만 **강력히 권장**합니다. 가상환경을 사용하면:
- 프로젝트별로 패키지 격리
- 시스템 Python과 충돌 방지
- 의존성 관리 용이

### Q2: 어떤 Python 버전을 사용해야 하나요?

**A**:
- **최소**: Python 3.8
- **권장**: Python 3.11 (최적 성능)
- **지원**: Python 3.8 ~ 3.12

### Q3: 서버를 백그라운드에서 실행하려면?

**A**:

**Windows** (운영 환경 비권장):
```cmd
start /b python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**Mac/Linux**:
```bash
# nohup 사용
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &

# 또는 screen 사용
screen -S coupang-wing
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
# Ctrl+A, D로 분리
```

**권장**: 운영 환경에서는 systemd (Linux) 또는 Docker 사용

### Q4: 데이터베이스를 PostgreSQL로 변경할 수 있나요?

**A**: 네, 가능합니다.

1. PostgreSQL 설치
2. `.env` 파일 수정:
   ```ini
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```
3. psycopg2 설치:
   ```bash
   pip install psycopg2-binary
   ```

### Q5: Docker로 실행할 수 있나요?

**A**: 네, `docker-compose.dev.yml`이 포함되어 있습니다.

```bash
docker-compose -f docker-compose.dev.yml up
```

### Q6: API 키를 환경 변수로 설정하려면?

**A**: `.env` 파일 대신 시스템 환경 변수로 설정 가능합니다.

**Windows**:
```cmd
setx OPENAI_API_KEY "sk-xxxxxxxxxxxxxxxx"
```

**Mac/Linux**:
```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### Q7: 로그 파일은 어디에 저장되나요?

**A**:
- **애플리케이션 로그**: `backend/logs/`
- **시스템 로그**: `logs/`
- **에러 리포트**: `error_reports/`

### Q8: 보안 강화 방법은?

**A**:
1. `.env`의 `SECRET_KEY` 변경
2. HTTPS 사용 (운영 환경)
3. 방화벽 설정 (포트 8080 제한)
4. Rate Limiting 활성화
5. 정기적인 업데이트

### Q9: 성능을 개선하려면?

**A**:
1. 캐싱 활성화 (.env에서 설정)
2. 데이터베이스 최적화 (인덱스 추가)
3. 배치 작업 스케줄링
4. 멀티 워커 사용:
   ```bash
   uvicorn app.main:app --workers 4
   ```

### Q10: 문제를 해결할 수 없어요!

**A**: 다음 순서로 시도하세요:

1. **자가 진단 실행**:
   ```bash
   python health_check.py
   ```

2. **에러 리포트 확인**:
   ```bash
   # 가장 최근 에러 리포트 확인
   ls -lt error_reports/ | head -n 2
   ```

3. **로그 확인**:
   ```bash
   tail -n 50 backend/logs/app.log
   ```

4. **패키지 재설치**:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

5. **완전 재설치**:
   - 가상환경 삭제
   - `install.bat` 또는 `install.sh` 재실행

---

## 📞 지원 및 문의

### 문서

- **개발자 가이드**: `DEVELOPER_GUIDE.md`
- **변경 이력**: `CHANGELOG.md`
- **개선 사항**: `IMPROVEMENTS.md`
- **README**: `README.md`

### 문제 보고

버그나 문제를 발견하면:

1. `error_reports/` 폴더의 최신 리포트 확인
2. 문제 재현 단계 기록
3. 시스템 정보 수집 (`health_check.py` 실행)

---

## 🎉 설치 완료 후

설치가 완료되면:

1. ✅ 서버 실행: `run.bat` 또는 `./run.sh`
2. ✅ API 문서 확인: http://localhost:8080/docs
3. ✅ 첫 API 테스트: `/api/health` 엔드포인트 호출
4. ✅ 개발자 가이드 읽기: `DEVELOPER_GUIDE.md`

**즐거운 개발되세요! 🚀**

---

*마지막 업데이트: 2025-01-15*
*버전: 1.0.0*
