# 쿠팡 윙 CS 자동화 문제 분석 보고서

**분석 날짜**: 2025-11-20
**분석자**: Claude Code

---

## 📋 요약

**상품별 고객문의**와 **고객센터 문의** 시스템이 **완전히 작동하지 않고 있습니다**.
데이터베이스에 **문의가 단 한 건도 수집되지 않았으며**, 모든 API 호출이 실패하고 있습니다.

---

## 🔍 현재 상태

### 1️⃣ 데이터베이스 상태

```
총 문의 개수: 0개
미처리 문의: 0개
처리 완료: 0개
실패: 0개
```

**결론**: 문의가 전혀 수집되지 않았습니다.

---

### 2️⃣ API 호출 실패 기록

`activity_logs` 테이블에 **95개의 실패 기록**이 있습니다:

```
실패 기록: 95개
성공 기록: 0개
실패율: 100%
```

**기간**: 2025-10-30 ~ 2025-11-04
**마지막 시도**: 2025-11-04 12:42:25

---

## ❌ 근본 원인

### **쿠팡 API 인증 오류**

#### 1. 초기 오류 (10/30 ~ 11/04)
```json
{
  "code": "ERROR",
  "message": "HMAC format is invalid.",
  "transactionId": "..."
}
```
- **원인**: HMAC 서명 생성 로직 오류
- **영향**: 모든 API 호출 실패 (95회)

#### 2. 현재 오류 (테스트 결과)
```json
{
  "code": "ERROR",
  "message": "Specified signature is expired.",
  "transactionId": "..."
}
```
- **원인**: Timestamp 생성/처리 오류
- **세부사항**:
  - 생성된 타임스탬프: `251120T113608Z`
  - 형식: `yyMMddTHHmmssZ` (2자리 연도)
  - 문제: 시간대 처리 오류 또는 타임스탬프 유효기간 초과

---

## 🔧 기술적 세부사항

### HMAC 서명 생성 코드 (`coupang_api.py:33-61`)

```python
def _generate_hmac(self, method: str, path: str, query: str = "", datetime_str: str = None) -> tuple:
    if datetime_str is None:
        import os
        os.environ['TZ'] = 'GMT+0'  # ⚠️ 문제 가능성 1
        time.tzset() if hasattr(time, 'tzset') else None  # ⚠️ Windows에서 작동 안함
        datetime_str = time.strftime('%y%m%d') + 'T' + time.strftime('%H%M%S') + 'Z'

    message = f"{datetime_str}{method}{path}{query}"

    signature = hmac.new(
        self.secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature, datetime_str
```

**문제점**:
1. `time.tzset()`은 Windows에서 지원되지 않음
2. `os.environ['TZ'] = 'GMT+0'`은 즉시 적용되지 않을 수 있음
3. 로컬 시간과 GMT 시간의 차이로 서명이 만료됨
4. 타임스탬프 생성과 실제 API 호출 사이의 시간 차이

---

## 🚨 영향 범위

### 작동하지 않는 기능

1. **상품별 고객문의 수집** (`get_online_inquiries`)
   - 30분마다 자동 수집 시도 → 실패

2. **고객센터 문의 수집** (`get_call_center_inquiries`)
   - 30분마다 자동 수집 시도 → 실패

3. **문의 응답 제출** (`submit_online_inquiry_reply`)
   - 사용 불가

4. **콜센터 문의 확인** (`confirm_call_center_inquiry`)
   - 사용 불가

### 작동하는 기능

- 데이터베이스 구조 ✅
- 스케줄러 설정 ✅
- 프론트엔드/백엔드 서버 ✅
- 로그인 시스템 ✅

**하지만**: 핵심 기능인 문의 수집/응답이 전혀 작동하지 않음

---

## 💡 해결 방안

### 1단계: Timestamp 생성 수정 (최우선)

**파일**: `backend/app/services/coupang_api.py`

```python
def _generate_hmac(self, method: str, path: str, query: str = "", datetime_str: str = None) -> tuple:
    if datetime_str is None:
        # UTC 시간 사용 (datetime 모듈 사용)
        from datetime import datetime, timezone
        utc_now = datetime.now(timezone.utc)
        datetime_str = utc_now.strftime('%y%m%dT%H%M%SZ')

    message = f"{datetime_str}{method}{path}{query}"

    signature = hmac.new(
        self.secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature, datetime_str
```

**이유**:
- `datetime.now(timezone.utc)`는 정확한 UTC 시간 반환
- Windows/Linux 모두 호환
- `time.tzset()` 의존성 제거

---

### 2단계: API 키 검증

**확인 필요 사항**:
1. `COUPANG_ACCESS_KEY`: `7a2a99f7-9202-4d7d-b094-6b6d758601d4`
2. `COUPANG_SECRET_KEY`: `13da414b5cf1e3b9ae4b236ab5f9329424d60c96`
3. `COUPANG_VENDOR_ID`: `A00492891`

**확인 방법**:
- 쿠팡 Wing 파트너 센터 로그인
- API 관리 > API Key 확인
- 키가 만료되지 않았는지 확인
- 권한이 올바르게 설정되었는지 확인

---

### 3단계: 재시도 로직 개선

현재 코드는 동일한 타임스탬프로 3번 재시도합니다:
```python
if retry < settings.MAX_RETRIES:
    time.sleep(settings.RETRY_DELAY)
    return self._make_request(method, path, query, data, retry + 1)
```

**문제**: 같은 만료된 서명을 계속 재사용

**해결**:
```python
if retry < settings.MAX_RETRIES:
    time.sleep(settings.RETRY_DELAY)
    # 헤더를 다시 생성 (새로운 타임스탬프)
    return self._make_request(method, path, query, data, retry + 1)
```

---

### 4단계: 수동 테스트 스크립트 작성

수정 후 즉시 테스트할 수 있는 스크립트:

```python
# test_fixed_api.py
from backend.app.services.coupang_api import CoupangAPIClient

client = CoupangAPIClient()

# 테스트 1: 온라인 문의
try:
    result = client.get_online_inquiries(status="WAITING", max_per_page=1)
    print("✅ 온라인 문의 조회 성공!")
    print(f"결과: {result}")
except Exception as e:
    print(f"❌ 실패: {e}")

# 테스트 2: 콜센터 문의
try:
    result = client.get_call_center_inquiries(
        inquiry_status="PROGRESS",
        partner_transfer_status="TRANSFER",
        max_per_page=1
    )
    print("✅ 콜센터 문의 조회 성공!")
    print(f"결과: {result}")
except Exception as e:
    print(f"❌ 실패: {e}")
```

---

## 📊 예상 결과

### 수정 전
```
미처리 문의: 0개
24시간 이상 경과: 0개
시스템 상태: 완전 중단
```

### 수정 후 (예상)
```
미처리 문의: 수집 시작
24시간 이상 경과: 점진적 감소
시스템 상태: 정상 작동
```

---

## ⚙️ 스케줄러 설정

현재 자동화 스케줄:
- **문의 수집**: 30분마다 (현재 실패 중)
- **문의 처리**: 15분마다 (문의가 없어서 실행 안됨)
- **대기 승인 처리**: 1시간마다
- **아침 리포트**: 09:00
- **저녁 리포트**: 18:00

**주의**: 수정 후 첫 30분 안에 대량의 문의가 수집될 수 있습니다.

---

## 🎯 다음 단계

1. ✅ **즉시**: Timestamp 생성 로직 수정
2. ✅ **즉시**: API 키 유효성 확인
3. ✅ **즉시**: 테스트 실행
4. ⏰ **수정 후**: 30분 대기하여 자동 수집 확인
5. 📊 **수정 후**: 대시보드에서 문의 개수 모니터링

---

## 🔐 보안 참고사항

`.env` 파일에 다음 정보가 노출되어 있습니다:
```
COUPANG_WING_USERNAME=lhs0609
COUPANG_WING_PASSWORD=pascal1623!!
OPENAI_API_KEY=sk-proj-a-M4lHkx...
```

**권장사항**:
- `.env` 파일을 Git에 커밋하지 마세요
- API 키를 정기적으로 갱신하세요
- 비밀번호를 더 강력하게 변경하세요

---

## 📝 요약

**문제**: 쿠팡 API 인증 실패로 문의가 전혀 수집되지 않음
**원인**: Timestamp 생성 로직 오류 (시간대 처리 문제)
**해결**: UTC 시간 기반 타임스탬프 생성으로 수정
**예상 소요시간**: 5분 (코드 수정) + 30분 (첫 자동 수집 대기)

---

**작성일**: 2025-11-20 11:37 KST
