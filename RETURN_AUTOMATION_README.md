# 쿠팡 → 네이버 반품 자동 처리 시스템

쿠팡에서 반품 요청이 들어오면 자동으로 네이버 스마트스토어에서 반품 처리를 하는 자동화 시스템입니다.

## 시스템 개요

```
[쿠팡 API] ──(15분마다 폴링)──→ [자동 수집기] ──→ [DB 저장]
                                                    ↓
                                              [대기 상태]
                                                    ↓
[네이버 셀레니엄] ←──(20분마다 처리)── [자동 처리기] ←── [설정 필터링]
```

### 주요 기능

1. **자동 수집 (Auto Fetch)**
   - 15분마다 쿠팡 API에서 새로운 반품 요청 조회
   - RETURN/CANCEL 타입 모두 수집
   - 중복 검사 및 상태 업데이트

2. **자동 처리 (Auto Process)**
   - 20분마다 대기 중인 반품을 네이버에서 자동 처리
   - Selenium을 이용한 자동 클릭/입력
   - 최대 3회 재시도 로직 (1분 → 5분 → 15분 간격)

3. **스마트 필터링**
   - 처리 가능한 상태만 자동 처리
   - 수동 확인 필요 건은 제외
   - 배치 크기 제한 (기본 50건)

4. **모니터링 & 로깅**
   - 실행 로그 자동 기록
   - 성공/실패 통계
   - 에러 알림 기능

---

## 설치 및 설정

### 1. DB 마이그레이션

```bash
cd backend
python migrate_auto_return.py
```

실행 결과:
```
자동 반품 처리 기능 마이그레이션 시작...
테이블 생성 중...
테이블 생성 완료
기본 자동화 설정 생성 중...
기본 자동화 설정 생성 완료
현재 반품 로그 통계:
  - 전체: 0건
  - 대기: 0건
마이그레이션 완료!
```

### 2. 서버 재시작

스케줄러를 활성화하기 위해 서버를 재시작합니다:

```bash
# 기존 서버 종료
# Ctrl+C

# 서버 재시작
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

서버 로그에서 다음 메시지를 확인:
```
Starting automation scheduler...
Scheduler started successfully
```

### 3. 자동화 설정 활성화

#### API로 설정하기 (Swagger UI)

`http://localhost:8000/docs` 접속 후:

1. **GET /returns/automation/config** - 현재 설정 확인
2. **PUT /returns/automation/config** - 설정 업데이트

```json
{
  "enabled": true,
  "fetch_enabled": true,
  "process_enabled": true
}
```

---

## API 엔드포인트

### 자동화 설정 관리

#### 1. 설정 조회
```http
GET /returns/automation/config
```

응답:
```json
{
  "success": true,
  "config": {
    "enabled": false,
    "fetch_enabled": true,
    "fetch_interval_minutes": 15,
    "fetch_lookback_hours": 1,
    "process_enabled": true,
    "process_interval_minutes": 20,
    "process_batch_size": 50,
    "auto_process_statuses": [
      "RELEASE_STOP_UNCHECKED",
      "RETURNS_UNCHECKED",
      "VENDOR_WAREHOUSE_CONFIRM"
    ],
    "exclude_statuses": [
      "REQUEST_COUPANG_CHECK",
      "RETURNS_COMPLETED"
    ],
    "max_retry_count": 3,
    "retry_delay_seconds": [60, 300, 900],
    "use_headless": true
  }
}
```

#### 2. 설정 업데이트
```http
PUT /returns/automation/config
Content-Type: application/json

{
  "enabled": true,
  "fetch_interval_minutes": 10,
  "process_batch_size": 30
}
```

### 수동 실행 (테스트용)

#### 3. 수집 즉시 실행
```http
POST /returns/automation/run-collector
```

#### 4. 처리 즉시 실행
```http
POST /returns/automation/run-processor
```

#### 5. 실패 건 재처리
```http
POST /returns/automation/retry-failed?max_count=10
```

### 통계 조회

#### 6. 자동화 통계
```http
GET /returns/automation/statistics
```

응답:
```json
{
  "success": true,
  "statistics": {
    "total": 125,
    "pending": 15,
    "processed": 95,
    "failed": 5,
    "recent_24h": 25,
    "config": {
      "enabled": true,
      "last_fetch_at": "2025-11-12T10:30:00",
      "last_process_at": "2025-11-12T10:35:00",
      "last_fetch_count": 5,
      "last_process_count": 3
    }
  }
}
```

---

## 주요 설정 옵션

### 자동화 활성화
- **enabled**: 전체 자동화 On/Off
- **fetch_enabled**: 자동 수집 On/Off
- **process_enabled**: 자동 처리 On/Off

### 수집 설정
- **fetch_interval_minutes**: 수집 주기 (기본: 15분)
- **fetch_lookback_hours**: 조회할 과거 시간 (기본: 1시간)

### 처리 설정
- **process_interval_minutes**: 처리 주기 (기본: 20분)
- **process_batch_size**: 한 번에 처리할 최대 개수 (기본: 50건)

### 상태 필터링
- **auto_process_statuses**: 자동 처리할 상태 목록
  - `RELEASE_STOP_UNCHECKED`: 출고중지(미확인)
  - `RETURNS_UNCHECKED`: 반품접수(미확인)
  - `VENDOR_WAREHOUSE_CONFIRM`: 판매자 창고 확인

- **exclude_statuses**: 제외할 상태 목록
  - `REQUEST_COUPANG_CHECK`: 쿠팡 확인 요청
  - `RETURNS_COMPLETED`: 반품 완료

### 재시도 설정
- **max_retry_count**: 최대 재시도 횟수 (기본: 3회)
- **retry_delay_seconds**: 재시도 간격 (기본: [60, 300, 900] - 1분, 5분, 15분)

### 셀레니엄 설정
- **use_headless**: 헤드리스 모드 사용 (기본: true)
- **selenium_timeout**: Selenium 타임아웃 (기본: 30초)

---

## 처리 흐름

### 1. 자동 수집 프로세스

```
1. 스케줄러 트리거 (15분마다)
   ↓
2. 쿠팡 API 호출 (최근 1시간 데이터)
   ↓
3. RETURN/CANCEL 타입 각각 조회
   ↓
4. 중복 검사 (receipt_id 기준)
   ↓
5. 신규: DB 저장 (status=pending)
   기존: 상태 업데이트
   ↓
6. 실행 로그 기록
```

### 2. 자동 처리 프로세스

```
1. 스케줄러 트리거 (20분마다)
   ↓
2. 대기 중인 반품 조회 (status=pending)
   ↓
3. 설정 필터 적용
   - auto_process_statuses에 포함된 것만
   - exclude_statuses 제외
   ↓
4. 배치 크기만큼 선택 (최대 50건)
   ↓
5. 네이버 로그인
   ↓
6. 각 반품 처리 (재시도 로직 포함)
   - RELEASE_STOP_UNCHECKED → 주문 취소
   - 기타 → 반품 요청
   ↓
7. 상태 업데이트
   - 성공: status=completed, naver_processed=true
   - 실패: status=failed, naver_error 기록
   ↓
8. 실행 로그 기록
```

### 3. 재시도 로직

```
시도 1: 즉시 처리
  ↓ (실패 시)
대기 1분
  ↓
시도 2: 재처리
  ↓ (실패 시)
대기 5분
  ↓
시도 3: 재처리
  ↓ (실패 시)
대기 15분
  ↓
최종 실패 처리
```

---

## 데이터베이스 스키마

### auto_return_configs (자동화 설정)
```sql
CREATE TABLE auto_return_configs (
    id INTEGER PRIMARY KEY,
    enabled BOOLEAN DEFAULT FALSE,
    fetch_enabled BOOLEAN DEFAULT TRUE,
    fetch_interval_minutes INTEGER DEFAULT 15,
    process_enabled BOOLEAN DEFAULT TRUE,
    process_batch_size INTEGER DEFAULT 50,
    auto_process_statuses JSON,
    exclude_statuses JSON,
    max_retry_count INTEGER DEFAULT 3,
    retry_delay_seconds JSON,
    last_fetch_at DATETIME,
    last_process_at DATETIME,
    last_error TEXT
);
```

### auto_return_execution_logs (실행 로그)
```sql
CREATE TABLE auto_return_execution_logs (
    id INTEGER PRIMARY KEY,
    execution_type VARCHAR(20),  -- 'FETCH' or 'PROCESS'
    status VARCHAR(20),           -- 'success', 'failed', 'partial'
    started_at DATETIME,
    completed_at DATETIME,
    duration_seconds INTEGER,
    total_items INTEGER,
    success_count INTEGER,
    failed_count INTEGER,
    details JSON,
    error_message TEXT,
    triggered_by VARCHAR(20)      -- 'scheduler', 'manual', 'api'
);
```

---

## 모니터링

### 로그 확인

서버 실행 시 다음과 같은 로그가 출력됩니다:

```
2025-11-12 10:15:00 | INFO | Starting scheduled return collection...
2025-11-12 10:15:01 | INFO | 쿠팡 반품 데이터 수집 시작: 2025-11-12 09:15 ~ 2025-11-12 10:15
2025-11-12 10:15:03 | INFO | RETURN 타입 5건의 반품 발견
2025-11-12 10:15:04 | SUCCESS | Collected 5 returns (New: 3, Updated: 2)

2025-11-12 10:20:00 | INFO | Starting scheduled return processing...
2025-11-12 10:20:01 | INFO | 3건의 반품 처리 시작
2025-11-12 10:20:45 | INFO | Receipt 123456 처리 성공
2025-11-12 10:21:12 | INFO | Receipt 123457 처리 성공
2025-11-12 10:21:38 | INFO | Receipt 123458 처리 성공
2025-11-12 10:21:39 | SUCCESS | Processed 3 returns, Failed: 0
```

### 실행 로그 DB 조회

```sql
-- 최근 10개 실행 로그
SELECT
    execution_type,
    status,
    started_at,
    duration_seconds,
    total_items,
    success_count,
    failed_count
FROM auto_return_execution_logs
ORDER BY started_at DESC
LIMIT 10;
```

### 통계 대시보드

API 엔드포인트 `/returns/automation/statistics`를 주기적으로 호출하여 프론트엔드 대시보드를 구현할 수 있습니다.

---

## 트러블슈팅

### 자동화가 실행되지 않음

1. **스케줄러 상태 확인**
   ```
   서버 로그에서 "Scheduler started successfully" 확인
   ```

2. **설정 확인**
   ```http
   GET /returns/automation/config
   ```
   - `enabled: true` 확인
   - `fetch_enabled: true` 확인
   - `process_enabled: true` 확인

3. **계정 정보 확인**
   - 쿠팡 계정 등록 확인
   - 네이버 계정 등록 확인

### 처리가 계속 실패함

1. **에러 로그 확인**
   ```http
   GET /returns/automation/config
   ```
   `last_error` 필드 확인

2. **수동 테스트**
   ```http
   POST /returns/automation/run-processor
   ```
   응답의 `errors` 배열 확인

3. **네이버 로그인 확인**
   - 네이버 계정 비밀번호 변경 여부
   - 2단계 인증 설정 여부
   - 보안 설정 확인

### 중복 처리 발생

- `receipt_id` 기준으로 중복 검사가 되므로 중복 처리는 발생하지 않습니다.
- 만약 의심되는 경우 DB에서 직접 확인:
  ```sql
  SELECT coupang_receipt_id, COUNT(*) as cnt
  FROM return_logs
  GROUP BY coupang_receipt_id
  HAVING cnt > 1;
  ```

---

## 성능 최적화

### 권장 설정값

**소량 처리 (하루 10~50건)**
```json
{
  "fetch_interval_minutes": 30,
  "process_interval_minutes": 30,
  "process_batch_size": 20
}
```

**중량 처리 (하루 50~200건)**
```json
{
  "fetch_interval_minutes": 15,
  "process_interval_minutes": 20,
  "process_batch_size": 50
}
```

**대량 처리 (하루 200건 이상)**
```json
{
  "fetch_interval_minutes": 10,
  "process_interval_minutes": 15,
  "process_batch_size": 100
}
```

### 주의사항

1. **너무 짧은 주기는 API 제한에 걸릴 수 있음**
   - 쿠팡 API: 분당 요청 제한 확인 필요
   - 네이버: Selenium 봇 감지 가능성

2. **배치 크기가 클수록 한 번에 오래 걸림**
   - Selenium 처리는 한 건당 약 20~30초 소요
   - 50건 처리 시 약 15~25분 소요

3. **헤드리스 모드 권장**
   - `use_headless: true` 설정 유지
   - 서버 리소스 절약

---

## 향후 개선 계획

- [ ] 웹훅 지원 (쿠팡에서 지원 시)
- [ ] 이메일 알림 기능
- [ ] 슬랙/텔레그램 연동
- [ ] 프론트엔드 대시보드
- [ ] 처리 성공률 통계 그래프
- [ ] 자동 학습 기반 재시도 간격 조정

---

## 파일 구조

```
backend/
├── app/
│   ├── models/
│   │   ├── auto_return_config.py          # 자동화 설정 모델
│   │   └── auto_return_log.py             # 실행 로그 모델
│   ├── services/
│   │   ├── auto_return_collector.py       # 자동 수집 서비스
│   │   └── auto_return_processor.py       # 자동 처리 서비스
│   ├── routers/
│   │   └── return_management.py           # API 엔드포인트 (확장)
│   └── scheduler.py                       # 스케줄러 (확장)
└── migrate_auto_return.py                 # 마이그레이션 스크립트
```

---

## 문의 및 지원

문제가 발생하거나 질문이 있으시면:

1. 서버 로그 확인
2. API 응답의 `error` 필드 확인
3. DB의 `auto_return_execution_logs` 테이블 확인
4. GitHub 이슈 등록

---

## 라이선스

이 프로젝트는 기존 Coupang Wing CS Automation 시스템의 일부입니다.
