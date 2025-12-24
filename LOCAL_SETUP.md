# 로컬 환경에서 브라우저 보면서 실행하기

이 가이드는 **로컬 컴퓨터에서 브라우저를 띄워서 자동화 과정을 직접 보면서** 실행하는 방법을 안내합니다.

## 🚨 중요사항

- **Fly.io 서버**에서는 GUI가 없어서 브라우저를 볼 수 없습니다 (headless만 가능)
- **로컬 컴퓨터**에서만 브라우저를 띄워서 볼 수 있습니다

## 📋 사전 준비

1. **Python 3.11** 설치
2. **Node.js** 설치
3. **Chrome 브라우저** 설치

## 🛠️ 설정 방법

### 1단계: 백엔드 환경 설정

```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경 생성 (처음 한 번만)
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2단계: 환경변수 설정

`backend/.env` 파일을 생성하고 다음 내용을 입력:

```env
# 쿠팡 윙 로그인 정보
COUPANG_WING_USERNAME=your_username_here
COUPANG_WING_PASSWORD=your_password_here

# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# 데이터베이스
DATABASE_URL=sqlite:///./database/coupang_cs.db

# 서버 설정
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=True
```

### 3단계: 백엔드 서버 실행

```bash
# backend 디렉토리에서
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

백엔드 서버가 `http://localhost:8000`에서 실행됩니다.

### 4단계: 프론트엔드 설정 및 실행

새 터미널을 열고:

```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 패키지 설치 (처음 한 번만)
npm install

# 로컬 백엔드 연결을 위한 환경변수 설정
# frontend/.env 파일 생성 또는 수정:
echo "" > .env

# 개발 서버 실행
npm run dev
```

프론트엔드가 `http://localhost:3000` (또는 5173)에서 실행됩니다.

## 🚀 사용 방법

### 1. 웹 브라우저에서 접속

```
http://localhost:3000
```

### 2. 로그인 테스트

1. **쿠팡 윙 아이디/비밀번호** 입력
2. **Headless 모드 체크박스 해제** (브라우저를 보려면 꺼야 함)
3. **"로그인 테스트"** 버튼 클릭
4. 🎉 Chrome 브라우저가 자동으로 열리면서 로그인 과정을 볼 수 있습니다!

### 3. 로그인 성공 확인

- ✅ "로그인 성공!" 메시지가 표시되면 OK
- ❌ "로그인 실패" 메시지가 나오면 아이디/비밀번호 확인

### 4. 자동화 실행

1. 로그인 성공 후 **"자동화 실행"** 버튼 클릭
2. 브라우저에서 자동화 과정을 실시간으로 볼 수 있습니다:
   - 쿠팡 윙 사이트 접속
   - 3개 시간대 탭 순회
   - 문의 읽기
   - ChatGPT 답변 생성
   - 답변 입력 및 저장

### 5. 결과 확인

- 처리 완료 후 통계 표시
- 총 문의 수
- 답변 완료 수
- 실패/건너뜀 수

## 🎥 브라우저 화면 보는 방법

### Headless 모드 OFF (브라우저 보임)
```
✅ Headless 모드 체크박스 해제
→ Chrome 브라우저가 열리면서 자동화 과정을 직접 볼 수 있음
```

### Headless 모드 ON (백그라운드 실행)
```
☑️ Headless 모드 체크박스 선택
→ 브라우저가 보이지 않고 백그라운드에서 실행
```

## 🔧 문제 해결

### 브라우저가 안 열려요
- Headless 모드가 **꺼져 있는지** 확인
- Chrome이 설치되어 있는지 확인
- ChromeDriver가 자동으로 다운로드되었는지 확인

### "연결 오류" 메시지가 나와요
- 백엔드 서버가 실행 중인지 확인 (`http://localhost:8000`)
- 프론트엔드 `.env` 파일이 올바른지 확인

### 로그인이 실패해요
- 쿠팡 윙 아이디/비밀번호가 정확한지 확인
- 백엔드 `.env` 파일에 올바른 정보가 있는지 확인
- 쿠팡 윙 사이트가 정상인지 확인

## 📊 실행 로그 확인

백엔드 터미널에서 실시간 로그를 볼 수 있습니다:

```
✅ 웹드라이버 설정 완료
🔐 쿠팡윙 로그인 시작...
  ✅ 아이디 입력 완료
  ✅ 비밀번호 입력 완료
  ✅ 로그인 버튼 클릭 완료
✅ 로그인 성공!
📋 고객문의 페이지로 이동...
🔍 '72시간~30일' 탭 확인 중...
✅ 총 3개 유효한 문의 수집 완료
💬 답변 작성 시작...
🤖 ChatGPT 답변 생성 중...
✅ 답변 저장 완료!
```

## 🎯 권장 워크플로우

### 개발/테스트 시
1. **로컬 환경** 사용
2. **Headless OFF** (브라우저 보면서 확인)
3. 문제 발생 시 즉시 확인 가능

### 실제 운영 시
1. **Fly.io 서버** 사용
2. **Headless ON** (서버에서는 필수)
3. 로그로 결과 확인

## 📞 추가 지원

문제가 계속되면:
1. 백엔드 로그 확인 (`backend` 터미널)
2. 브라우저 개발자 도구 확인 (F12)
3. `logs/app.log` 파일 확인
