# 🚀 빠른 시작 가이드

## 1단계: 서버 시작

### 방법 1: 터미널에서 직접 시작 (권장)

```bash
cd E:\u\coupang-wing-cs-automation\backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

**성공 시 출력:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 방법 2: 백그라운드 실행

```bash
cd backend
start "쿠팡윙 서버" cmd /k "..\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
```

---

## 2단계: Swagger UI 접속

브라우저에서 접속:
```
http://localhost:8000/docs
```

**확인사항:**
- API 문서가 보이면 성공 ✅
- 연결 실패하면 서버 재시작

---

## 3단계: 쿠팡 계정 등록

### 이미 등록되어 있는지 확인

**API:** `GET /coupang-accounts`

**응답 예시 (등록됨):**
```json
[
  {
    "id": 1,
    "vendor_id": "A00492891",
    "wing_username": "lhs0609",
    "is_active": true
  }
]
```

**응답 예시 (미등록):**
```json
[]
```

### 쿠팡 계정 등록 (미등록 시)

**API:** `POST /coupang-accounts`

**요청 본문:**
```json
{
  "name": "메인 계정",
  "vendor_id": "A00492891",
  "access_key": "your_access_key_here",
  "secret_key": "your_secret_key_here",
  "wing_username": "lhs0609",
  "wing_password": "your_password_here"
}
```

**성공 응답:**
```json
{
  "id": 1,
  "name": "메인 계정",
  "vendor_id": "A00492891",
  "is_active": true,
  "created_at": "2025-11-12T13:30:00"
}
```

---

## 4단계: 반품 데이터 조회

**API:** `GET /returns/fetch-from-coupang`

**파라미터:**
```
start_date: 2025-11-01T00:00
end_date: 2025-11-12T23:59
cancel_type: RETURN
```

**Swagger UI에서:**
1. `GET /returns/fetch-from-coupang` 클릭
2. "Try it out" 버튼 클릭
3. 파라미터 입력:
   - `start_date`: `2025-11-01T00:00`
   - `end_date`: `2025-11-12T23:59`
   - `cancel_type`: `RETURN`
4. "Execute" 버튼 클릭

**예상 응답:**
```json
{
  "success": true,
  "message": "조회 및 저장 완료",
  "total_fetched": 15,
  "saved": 10,
  "updated": 5
}
```

---

## 5단계: 수령인 정보 확인

### DB에서 직접 확인

```bash
cd backend
..\venv\Scripts\python.exe -c "
from app.database import SessionLocal
from app.models.return_log import ReturnLog
import json

db = SessionLocal()
logs = db.query(ReturnLog).limit(3).all()

print('반품 목록 (상위 3건):')
print('=' * 60)
for log in logs:
    print(f'ID: {log.id}')
    print(f'상품명: {log.product_name}')
    print(f'수령인: {log.receiver_name}')
    print(f'전화: {log.receiver_phone}')
    print(f'상태: {log.status}')
    print('-' * 60)

db.close()
"
```

### API로 확인

**API:** `GET /returns/list?status=pending&limit=10`

**응답 예시:**
```json
{
  "success": true,
  "total": 15,
  "data": [
    {
      "id": 1,
      "product_name": "갤럭시 S24 케이스",
      "receiver_name": "홍길동",
      "receiver_phone": "010-1234-5678",
      "status": "pending",
      "receipt_status": "RETURNS_UNCHECKED"
    }
  ]
}
```

---

## 6단계: 네이버 계정 등록 (선택)

**API:** `POST /naver-accounts`

**요청 본문:**
```json
{
  "name": "메인 네이버 계정",
  "naver_username": "your_naver_id",
  "naver_password": "your_naver_password",
  "client_id": "optional",
  "client_secret": "optional"
}
```

---

## 7단계: 네이버페이 반품 처리 (테스트)

### 수동 실행

**API:** `POST /returns/process-naver`

**요청 본문:**
```json
{
  "return_log_ids": [1, 2, 3],
  "naver_credentials": {
    "username": "your_naver_id",
    "password": "your_naver_password"
  },
  "headless": false
}
```

**주의:**
- `headless: false`로 설정하면 브라우저가 보입니다 (처음 테스트 시 권장)
- 실제 반품이 처리되므로 주의!

**예상 응답:**
```json
{
  "success": true,
  "message": "처리 완료: 2건 성공, 1건 실패",
  "processed": 2,
  "failed": 1,
  "errors": [
    "주문을 찾을 수 없음: 상품명..."
  ]
}
```

---

## 8단계: 결과 확인

**API:** `GET /returns/list?status=completed`

또는

**API:** `GET /returns/automation/statistics`

```json
{
  "success": true,
  "statistics": {
    "total": 15,
    "pending": 3,
    "processed": 10,
    "failed": 2
  }
}
```

---

## 트러블슈팅

### 문제: 수령인 정보가 null

**원인:** 쿠팡 API 응답에 수령인 정보가 없음

**해결:**
```bash
# raw_data 확인
cd backend
..\venv\Scripts\python.exe -c "
from app.database import SessionLocal
from app.models.return_log import ReturnLog
import json

db = SessionLocal()
log = db.query(ReturnLog).first()
if log and log.raw_data:
    print(json.dumps(log.raw_data, indent=2, ensure_ascii=False))
db.close()
"
```

→ 수령인 필드명 확인 후 `backend/app/services/auto_return_collector.py` 수정

### 문제: 네이버페이에서 주문을 찾을 수 없음

**원인:**
1. 상품명이 다름
2. 수령인 이름이 다름
3. 네이버페이가 아닌 다른 결제수단

**해결:**
1. 실제 네이버페이 결제내역 확인
2. 상품명과 수령인이 정확히 일치하는지 확인
3. 필요 시 매칭 로직 수정

### 문제: 반품 버튼을 찾을 수 없음

**원인:** 네이버페이 HTML 구조 변경

**해결:**
1. https://pay.naver.com/pc/history 접속
2. F12 개발자 도구
3. 반품 버튼의 실제 클래스명/텍스트 확인
4. `backend/app/services/naver_pay_automation.py` 수정

---

## 자동화 설정 (선택)

### 자동화 활성화

**API:** `PUT /returns/automation/config`

**요청 본문:**
```json
{
  "enabled": true,
  "fetch_enabled": true,
  "process_enabled": true
}
```

### 자동화 즉시 실행 (테스트)

**API:** `POST /returns/automation/run-collector`

수집 즉시 실행

**API:** `POST /returns/automation/run-processor`

처리 즉시 실행

---

## 체크리스트

- [ ] 서버 시작 확인 (http://localhost:8000/docs 접속)
- [ ] 쿠팡 계정 등록
- [ ] 반품 데이터 조회 (fetch-from-coupang)
- [ ] 수령인 정보 확인 (receiver_name, receiver_phone)
- [ ] 네이버 계정 등록
- [ ] 네이버페이 반품 처리 테스트 (headless: false)
- [ ] 결과 확인
- [ ] 쿠팡 API 응답 구조 확인 (필요 시)
- [ ] 네이버페이 HTML 구조 확인 (필요 시)
- [ ] 자동화 설정 (선택)

---

## 다음 문서

- 상세 가이드: `NAVERPAY_RETURN_GUIDE.md`
- 자동화 설정: `RETURN_AUTOMATION_README.md`

---

**모든 준비가 완료되었습니다!** 🎉

질문이 있으시면 언제든지 문의하세요!
