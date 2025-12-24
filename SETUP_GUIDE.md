# 쿠팡 윙 CS 자동 응답 시스템 설치 가이드

## 초기 설정 체크리스트

### 1. 쿠팡 API 준비
- [ ] 쿠팡 윙 계정 확인
- [ ] API 액세스 키 발급
- [ ] API 시크릿 키 발급
- [ ] 벤더 ID 확인
- [ ] 윙 사용자 ID 확인

### 2. 시스템 환경
- [ ] Python 3.10 이상 설치 확인
- [ ] Node.js 18 이상 설치 확인
- [ ] Git 설치 확인

### 3. 프로젝트 다운로드

```bash
# 프로젝트 클론 (또는 압축 해제)
cd coupang-wing-cs-automation
```

## 단계별 설치

### Step 1: 백엔드 환경 설정

```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### Step 2: 환경 변수 설정

```bash
# .env 파일 생성 (Windows)
copy .env.example .env

# .env 파일 생성 (Mac/Linux)
cp .env.example .env
```

`.env` 파일을 텍스트 에디터로 열고 다음 항목을 입력:

```env
# 쿠팡 API 정보 (필수!)
COUPANG_ACCESS_KEY=실제_액세스_키
COUPANG_SECRET_KEY=실제_시크릿_키
COUPANG_VENDOR_ID=실제_벤더_ID
COUPANG_WING_ID=실제_윙_ID

# 보안 키 (임의의 랜덤 문자열)
SECRET_KEY=랜덤_시크릿_키_생성_필요

# 나머지는 기본값 사용 가능
```

### Step 3: 데이터베이스 초기화

```bash
# 백엔드 디렉토리에서 실행
python -c "from app.database import init_db; init_db()"
```

성공 시 `coupang_cs.db` 파일이 생성됩니다.

### Step 4: 프론트엔드 설정

```bash
# 프론트엔드 디렉토리로 이동
cd ../frontend

# 패키지 설치
npm install
```

### Step 5: 지식 베이스 검토

`backend/knowledge_base/` 디렉토리의 파일들을 검토하고 필요 시 수정:

- `policies/` - 정책 파일들
- `templates/` - 답변 템플릿들
- `faq/` - 자주 묻는 질문들

## 실행

### 백엔드 서버 시작

터미널 1:
```bash
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 서버 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 시작되면 http://localhost:8000 에서 API 사용 가능

### 프론트엔드 서버 시작

터미널 2:
```bash
cd frontend
npm run dev
```

프론트엔드는 http://localhost:5173 에서 접속

## 테스트

### 1. API 헬스 체크

브라우저에서 http://localhost:8000/health 접속
또는:
```bash
curl http://localhost:8000/health
```

### 2. 대시보드 접속

브라우저에서 http://localhost:5173 접속

### 3. 시스템 통계 확인

```bash
curl http://localhost:8000/api/system/stats
```

### 4. 테스트 문의 수집 (실제 쿠팡 API 호출)

대시보드에서 "문의 수집" 버튼 클릭
또는:
```bash
curl -X POST http://localhost:8000/api/inquiries/collect \
  -H "Content-Type: application/json" \
  -d '{"inquiry_type": "online", "status_filter": "WAITING"}'
```

## 문제 해결

### 문제 1: 패키지 설치 오류

**증상**: `pip install` 실패

**해결**:
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 다시 설치
pip install -r requirements.txt
```

### 문제 2: 데이터베이스 오류

**증상**: `no such table` 오류

**해결**:
```bash
# 데이터베이스 파일 삭제
rm coupang_cs.db  # Mac/Linux
del coupang_cs.db  # Windows

# 재생성
python -c "from app.database import init_db; init_db()"
```

### 문제 3: CORS 오류

**증상**: 프론트엔드에서 API 호출 실패

**해결**:
- 백엔드가 8000 포트에서 실행 중인지 확인
- 프론트엔드가 5173 포트에서 실행 중인지 확인

### 문제 4: 쿠팡 API 인증 오류

**증상**: 401 Unauthorized 또는 403 Forbidden

**해결**:
- `.env` 파일의 API 키가 정확한지 확인
- 쿠팡 개발자 센터에서 API 키 상태 확인
- HMAC 서명이 올바른지 확인

## 다음 단계

1. **템플릿 커스터마이징**
   - `backend/knowledge_base/templates/` 파일들을 상황에 맞게 수정

2. **정책 업데이트**
   - `backend/knowledge_base/policies/` 에서 실제 쿠팡 정책 반영

3. **모니터링 설정**
   - 로그 파일 위치: `backend/logs/app.log`
   - 정기적으로 확인 권장

4. **첫 실행**
   - 대시보드에서 "문의 수집" 클릭
   - "자동 처리 실행" 클릭
   - 생성된 답변 검토
   - 테스트용으로 몇 개 승인해보기

5. **학습 기간**
   - 처음 1-2개월은 모든 답변을 수동으로 검토
   - 답변 품질 확인
   - 필요 시 템플릿 개선

## 운영 체크리스트

### 매일
- [ ] 새 문의 확인
- [ ] 대기 중인 답변 승인
- [ ] 오류 로그 확인

### 매주
- [ ] 통계 리뷰
- [ ] 자동화율 확인
- [ ] 고객 만족도 체크

### 매월
- [ ] 템플릿 개선
- [ ] 정책 업데이트
- [ ] 시스템 성능 분석

## 지원

문제가 계속되면:
1. `backend/logs/app.log` 파일 확인
2. 오류 메시지 복사
3. 이슈 등록 또는 개발자 문의
