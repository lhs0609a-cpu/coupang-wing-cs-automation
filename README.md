# 쿠팡 윙 CS 자동 응답 시스템

쿠팡 윙 고객 문의에 대한 정확하고 안전한 자동 응답 시스템입니다.

## 주요 기능

### 핵심 원칙: **정확성 > 자동화**

- ✅ 다단계 검증 시스템
- ✅ 사람의 최종 승인 필수
- ✅ 쿠팡 공식 API 사용
- ✅ 잘못된 답변 방지 시스템
- ✅ 실시간 모니터링 및 로깅

### 시스템 구성

```
쿠팡 윙 사이트
       ↓
[문의 수집 모듈] ← API 자동 수집
       ↓
[문의 분석 모듈] ← AI/규칙 기반 분류
       ↓
[답변 생성 모듈] ← 템플릿 + 정책 기반
       ↓
[검증 모듈] ← 4단계 검증
       ↓
[승인 인터페이스] ← 사람 최종 확인
       ↓
[자동 제출 모듈] ← 승인된 답변만 전송
```

## 설치 방법

### 1. 사전 요구사항

- Python 3.10+
- Node.js 18+
- SQLite (또는 PostgreSQL)

### 2. 백엔드 설정

```bash
cd backend

# 가상 환경 생성
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
copy .env.example .env
# .env 파일을 열어서 쿠팡 API 키 등을 입력하세요

# 데이터베이스 초기화
python -c "from app.database import init_db; init_db()"
```

### 3. 프론트엔드 설정

```bash
cd frontend

# 의존성 설치
npm install
```

## 실행 방법

### 백엔드 서버 실행

```bash
cd backend
venv\Scripts\activate  # Windows
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 실행

```bash
cd frontend
npm run dev
```

브라우저에서 http://localhost:5173 접속

## API 사용법

### 1. 문의 수집

```bash
curl -X POST http://localhost:8000/api/inquiries/collect \
  -H "Content-Type: application/json" \
  -d '{"inquiry_type": "online", "status_filter": "WAITING"}'
```

### 2. 자동 처리 파이프라인 실행

```bash
curl -X POST http://localhost:8000/api/system/process-pipeline?limit=10
```

### 3. 답변 승인

```bash
curl -X POST http://localhost:8000/api/responses/{response_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "admin"}'
```

### 4. 답변 제출

```bash
curl -X POST http://localhost:8000/api/responses/{response_id}/submit \
  -H "Content-Type: application/json" \
  -d '{"submitted_by": "admin"}'
```

## 환경 변수 설정

`.env` 파일에서 다음 항목을 설정하세요:

```env
# 쿠팡 API 설정 (필수)
COUPANG_ACCESS_KEY=your_access_key
COUPANG_SECRET_KEY=your_secret_key
COUPANG_VENDOR_ID=your_vendor_id
COUPANG_WING_ID=your_wing_id

# 보안 키 (필수)
SECRET_KEY=your_secret_key_here

# 데이터베이스
DATABASE_URL=sqlite:///./coupang_cs.db

# 검증 임계값
CONFIDENCE_THRESHOLD=80
AUTO_APPROVE_THRESHOLD=90
```

## 지식 베이스 구성

### 정책 파일 추가

`backend/knowledge_base/policies/` 디렉토리에 JSON 파일로 정책 추가:

- `shipping_policy.json` - 배송 정책
- `refund_policy.json` - 환불 정책
- `exchange_policy.json` - 교환 정책

### 템플릿 추가

`backend/knowledge_base/templates/` 디렉토리에 TXT 파일로 템플릿 추가:

템플릿 변수 사용 예시:
```
안녕하세요, {{customer_name}}님.

{{product_name}} 상품에 대한 문의를 확인했습니다.
```

### FAQ 추가

`backend/knowledge_base/faq/common_qa.json` 파일에 자주 묻는 질문 추가

## 검증 시스템

### 4단계 검증 프로세스

1. **형식 검증**
   - 길이 체크
   - 인사말/마무리 체크
   - 금지어 체크
   - JSON 인코딩 체크

2. **내용 검증**
   - 문의와의 관련성 체크
   - 정책 준수 여부
   - 플레이스홀더 체크

3. **위험 평가**
   - 법적 이슈 감지
   - 금액 언급 체크
   - 예외 처리 요청 감지

4. **신뢰도 계산**
   - 최종 신뢰도 점수 산정
   - 자동 승인 가능 여부 판단

### 자동 승인 조건

다음 조건을 **모두** 만족해야 자동 승인:

- ✅ 검증 통과
- ✅ 신뢰도 90% 이상
- ✅ 위험도 'low'
- ✅ 복잡도 낮음

그 외에는 **사람 승인 필수**

## 안전 장치

### 1. 화이트리스트 방식
- 확실한 것만 자동 처리
- 불확실하면 사람에게

### 2. 필수 인간 개입 케이스
- ❌ 법적 문제 관련
- ❌ 고액 환불/보상
- ❌ 감정적으로 격앙된 고객
- ❌ 복잡한 복합 문의
- ❌ 정책 예외 요청

### 3. 이중 체크
- 생성 시 검증
- 제출 전 재검증

### 4. 로깅 시스템
- 모든 활동 기록
- 오류 추적
- 성능 모니터링

## 통계 및 모니터링

### 대시보드에서 확인 가능한 지표

- 📊 문의 현황 (대기/처리/완료)
- 📊 답변 상태 (승인대기/승인/거부)
- 📊 제출 통계
- 📊 자동화율 및 정확도

### 로그 확인

```bash
# 백엔드 로그
tail -f backend/logs/app.log
```

## 운영 권장 사항

### Phase 1: 학습 기간 (1-2개월)
- ✅ 100% 수동 승인
- ✅ 답변 패턴 학습
- ✅ 템플릿 개선

### Phase 2: 부분 자동화 (3-4개월)
- ✅ 저위험 문의만 자동화 (30%)
- ✅ 지속적인 모니터링

### Phase 3: 확대 (6개월 이후)
- ✅ 점진적 자동화 확대 (최대 50%)
- ✅ 높은 리스크는 영구 수동

## 문제 해결

### 데이터베이스 초기화 오류

```bash
# 데이터베이스 파일 삭제 후 재생성
rm backend/coupang_cs.db
python -c "from app.database import init_db; init_db()"
```

### API 인증 오류

`.env` 파일의 쿠팡 API 키가 정확한지 확인:
- COUPANG_ACCESS_KEY
- COUPANG_SECRET_KEY
- COUPANG_VENDOR_ID

### 템플릿 로드 오류

템플릿 파일이 올바른 경로에 있는지 확인:
```
backend/knowledge_base/templates/
```

## 개발 로드맵

- [x] MVP 기능 구현
- [x] 다단계 검증 시스템
- [x] 웹 대시보드
- [ ] AI 답변 생성 (OpenAI 통합)
- [ ] 실시간 알림
- [ ] 통계 대시보드 고도화
- [ ] 자동 학습 시스템

## 라이선스

MIT License

## 지원

문제가 발생하면 Issues를 통해 제보해주세요.

---

**⚠️ 중요**: 이 시스템은 보조 도구입니다. 최종 답변은 반드시 사람이 검토하고 승인해야 합니다.
