# 네이버페이 기반 반품 자동 처리 가이드

## 시스템 개요

쿠팡에서 반품이 들어오면 **상품명 + 수령인 정보**를 가져와서,
네이버페이 결제내역(https://pay.naver.com/pc/history)에서 동일한 주문을 찾아 반품 처리합니다.

```
[쿠팡 API] → 반품 정보 (상품명 + 수령인)
                ↓
          [DB 저장]
                ↓
          [시작 버튼]
                ↓
[네이버페이 결제내역] → 상품명 + 수령인 매칭
                ↓
          [반품 처리]
```

---

## 설치 및 설정

### 1. DB 마이그레이션

수령인 정보 필드를 추가합니다:

```bash
cd backend
venv/Scripts/python.exe migrate_naver_pay.py
```

**실행 결과:**
```
네이버페이 반품 처리 마이그레이션 시작...
✓ receiver_name 컬럼 추가 완료
✓ receiver_phone 컬럼 추가 완료
마이그레이션 완료!
```

### 2. 서버 재시작

```bash
venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

---

## 사용 방법

### 단계 1: 쿠팡에서 반품 조회

**API:** `GET /returns/fetch-from-coupang`

**파라미터:**
```json
{
  "start_date": "2025-11-01T00:00",
  "end_date": "2025-11-12T23:59",
  "cancel_type": "RETURN"
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "조회 및 저장 완료",
  "total_fetched": 15,
  "saved": 10,
  "updated": 5
}
```

**저장되는 정보:**
- ✅ 상품명 (`product_name`)
- ✅ 수령인 이름 (`receiver_name`)
- ✅ 수령인 전화번호 (`receiver_phone`)
- ✅ 쿠팡 주문번호 (`coupang_order_id`)
- ✅ 반품 사유 (`cancel_reason`)

---

### 단계 2: 반품 목록 확인

**API:** `GET /returns/list?status=pending`

**응답 예시:**
```json
{
  "success": true,
  "total": 10,
  "data": [
    {
      "id": 1,
      "product_name": "갤럭시 S24 케이스",
      "receiver_name": "홍길동",
      "receiver_phone": "010-1234-5678",
      "receipt_status": "RETURNS_UNCHECKED",
      "status": "pending"
    },
    {
      "id": 2,
      "product_name": "에어팟 프로 2세대",
      "receiver_name": "김철수",
      "receiver_phone": "010-9876-5432",
      "receipt_status": "RETURNS_UNCHECKED",
      "status": "pending"
    }
  ]
}
```

---

### 단계 3: 시작 버튼 클릭 (네이버페이 반품 처리)

**API:** `POST /returns/process-naver` 또는 `POST /returns/automation/run-processor`

**요청 예시:**
```json
{
  "return_log_ids": [1, 2, 3],
  "naver_credentials": {
    "username": "your_naver_id",
    "password": "your_password"
  },
  "headless": true
}
```

**처리 과정:**
1. 네이버 로그인
2. https://pay.naver.com/pc/history 접속
3. 각 반품 항목에 대해:
   - 상품명 + 수령인으로 주문 검색 (최대 10페이지)
   - 일치하는 주문 찾기
   - 반품 버튼 클릭
   - 반품 사유 선택
   - 반품 신청
4. 결과 DB에 저장

**응답 예시:**
```json
{
  "success": true,
  "message": "처리 완료: 2건 성공, 1건 실패",
  "processed": 2,
  "failed": 1,
  "errors": [
    "주문을 찾을 수 없음: 에어팟 프로 2세대..."
  ]
}
```

---

## 매칭 로직

### 상품명 매칭
```python
# 부분 일치로 검색
product_match = (
    coupang_product_name in naverpay_product_name or
    naverpay_product_name in coupang_product_name
)
```

**예시:**
- 쿠팡: "갤럭시 S24 투명 케이스"
- 네이버페이: "갤럭시 S24 케이스"
- → ✅ 매칭 성공

### 수령인 매칭
```python
# 부분 일치로 검색
receiver_match = (
    coupang_receiver_name in naverpay_receiver_name or
    naverpay_receiver_name in coupang_receiver_name
)
```

**예시:**
- 쿠팡: "홍길동"
- 네이버페이: "홍길동"
- → ✅ 매칭 성공

### 동시 만족 필요
```python
if product_match and receiver_match:
    # 반품 처리
```

---

## 네이버페이 페이지 구조

### 검색 대상

**URL:** https://pay.naver.com/pc/history?page=1

**HTML 구조 예시:**
```html
<div class="history_item">
  <div class="product_info">
    <span class="product_name">갤럭시 S24 케이스</span>
  </div>
  <div class="receiver_info">
    <dt>받는사람</dt>
    <dd class="receiver_name">홍길동</dd>
  </div>
  <button class="btn_return">반품</button>
</div>
```

### Selenium 선택자

```python
# 상품명 추출
product_elem = item.find_element(By.CLASS_NAME, "product_name")
product_name = product_elem.text.strip()

# 수령인 추출 (방법 1)
receiver_elem = item.find_element(By.CLASS_NAME, "receiver_name")
receiver_name = receiver_elem.text.strip()

# 수령인 추출 (방법 2 - XPath)
receiver_elem = item.find_element(
    By.XPATH,
    ".//dt[contains(text(),'받는사람')]/following-sibling::dd"
)
receiver_name = receiver_elem.text.strip()

# 반품 버튼 클릭
return_button = item.find_element(By.XPATH, ".//button[contains(text(), '반품')]")
return_button.click()
```

---

## 주의사항

### 1. 쿠팡 API 응답에 수령인 정보가 있어야 함

쿠팡 API 응답 구조에 따라 수령인 정보 필드가 다를 수 있습니다:

**가능한 필드 이름:**
```python
# shippingTo 객체
{
  "shippingTo": {
    "name": "홍길동",
    "phoneNumber": "010-1234-5678"
  }
}

# receiverInfo 객체
{
  "receiverInfo": {
    "receiverName": "홍길동",
    "receiverPhone": "010-1234-5678"
  }
}

# returnItems 내부
{
  "returnItems": [{
    "receiverName": "홍길동",
    "receiverPhone": "010-1234-5678"
  }]
}
```

**현재 코드는 모든 케이스를 처리합니다.**

### 2. 네이버페이 HTML 구조 변경 가능성

네이버페이가 페이지 구조를 변경하면 Selenium 선택자를 수정해야 할 수 있습니다.

**확인 방법:**
1. 실제 https://pay.naver.com/pc/history 페이지 접속
2. F12 (개발자 도구) 열기
3. 상품명/수령인 요소의 클래스명 확인
4. 필요 시 `naver_pay_automation.py`의 선택자 수정

### 3. 봇 감지 회피

**현재 구현된 회피 방법:**
```python
# User-Agent 설정
chrome_options.add_argument("user-agent=Mozilla/5.0 ...")

# 자동화 감지 비활성화
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

# webdriver 속성 숨기기
driver.execute_script(
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
)
```

**추가 권장사항:**
- 헤드리스 모드 사용 (`headless: true`)
- 처리 간 대기 시간 (`time.sleep(2)`)
- 과도한 요청 방지

### 4. 매칭 실패 케이스

**주문을 찾을 수 없는 경우:**
- 상품명이 완전히 다름
- 수령인 정보 불일치
- 네이버페이가 아닌 다른 결제수단 사용
- 주문이 10페이지 이후에 있음 (`max_pages` 조정 필요)

**해결 방법:**
1. 수동으로 확인
2. 상품명을 더 일반적인 키워드로 수정
3. `max_pages` 증가 (기본 10페이지)

---

## 자동화 설정

### 자동 반품 처리 활성화

```http
PUT /returns/automation/config
Content-Type: application/json

{
  "enabled": true,
  "fetch_enabled": true,
  "process_enabled": true
}
```

**스케줄:**
- **15분마다**: 쿠팡에서 반품 수집 (상품명 + 수령인)
- **20분마다**: 네이버페이에서 자동 반품 처리

---

## API 레퍼런스

### 1. 반품 조회 및 저장
```http
GET /returns/fetch-from-coupang?start_date=2025-11-01T00:00&end_date=2025-11-12T23:59
```

### 2. 반품 목록
```http
GET /returns/list?status=pending&limit=100
```

### 3. 네이버페이 반품 처리
```http
POST /returns/process-naver
{
  "return_log_ids": [1, 2, 3],
  "naver_credentials": {...}
}
```

### 4. 자동 처리 즉시 실행
```http
POST /returns/automation/run-processor
```

### 5. 통계 조회
```http
GET /returns/automation/statistics
```

---

## 트러블슈팅

### 문제: 수령인 정보가 null

**원인:**
- 쿠팡 API 응답에 배송지 정보가 없음

**해결:**
1. `raw_data` 필드 확인:
   ```sql
   SELECT raw_data FROM return_logs WHERE id = 1;
   ```
2. 실제 필드 이름 확인 후 `auto_return_collector.py` 수정

### 문제: 네이버페이에서 주문을 찾을 수 없음

**원인:**
- 상품명/수령인 불일치
- 결제수단이 네이버페이가 아님

**해결:**
1. 수동으로 확인
2. DB에서 실제 저장된 정보 확인:
   ```sql
   SELECT product_name, receiver_name FROM return_logs WHERE id = 1;
   ```
3. 네이버페이 결제내역에서 실제 표시되는 이름 확인

### 문제: 반품 버튼을 찾을 수 없음

**원인:**
- 네이버페이 HTML 구조 변경
- 이미 반품 처리된 주문

**해결:**
1. F12로 실제 버튼 클래스명 확인
2. `naver_pay_automation.py`의 선택자 수정:
   ```python
   button_selectors = [
       ".//button[contains(text(), '반품')]",
       ".//button[contains(@class, 'YOUR_NEW_CLASS')]",  # 추가
   ]
   ```

---

## 파일 구조

```
backend/
├── app/
│   ├── models/
│   │   └── return_log.py                 # receiver_name, receiver_phone 추가
│   ├── services/
│   │   ├── auto_return_collector.py      # 수령인 정보 추출
│   │   ├── auto_return_processor.py      # 네이버페이 사용
│   │   └── naver_pay_automation.py       # 네이버페이 자동화 (신규)
│   └── routers/
│       └── return_management.py          # API 응답에 수령인 정보 추가
└── migrate_naver_pay.py                  # DB 마이그레이션 스크립트
```

---

## 핵심 로직

### 1. 수령인 정보 추출 (auto_return_collector.py)
```python
def _create_return_log(self, return_request: Dict, item: Dict):
    # 배송지 정보 추출
    shipping_to = return_request.get("shippingTo") or return_request.get("receiverInfo")
    receiver_name = shipping_to.get("name") or shipping_to.get("receiverName")
    receiver_phone = shipping_to.get("phoneNumber") or shipping_to.get("phone")

    return_log = ReturnLog(
        product_name=item.get("vendorItemName"),
        receiver_name=receiver_name,
        receiver_phone=receiver_phone,
        ...
    )
```

### 2. 주문 검색 (naver_pay_automation.py)
```python
def search_order(self, product_name, receiver_name, max_pages=10):
    for page in range(1, max_pages + 1):
        order_items = driver.find_elements(By.CLASS_NAME, "history_item")

        for item in order_items:
            item_product_name = item.find_element(...).text
            item_receiver_name = item.find_element(...).text

            # 매칭 확인
            if (product_name in item_product_name and
                receiver_name in item_receiver_name):
                return item  # 찾음!
```

### 3. 반품 처리 (naver_pay_automation.py)
```python
def process_return(self, order_element):
    # 반품 버튼 클릭
    return_button = order_element.find_element(By.XPATH, ".//button[contains(text(), '반품')]")
    return_button.click()

    # 사유 선택
    reason_select = driver.find_element(By.CSS_SELECTOR, "select[name='returnReason']")
    reason_select.find_elements(By.TAG_NAME, "option")[1].click()

    # 신청
    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), '신청')]")
    submit_button.click()
```

---

## 마이그레이션 후 확인사항

```sql
-- 1. 컬럼 추가 확인
PRAGMA table_info(return_logs);

-- 2. 샘플 데이터 확인
SELECT
    product_name,
    receiver_name,
    receiver_phone,
    status
FROM return_logs
LIMIT 5;

-- 3. 수령인 정보 없는 레코드
SELECT COUNT(*)
FROM return_logs
WHERE receiver_name IS NULL;
```

---

## 성공 시나리오

```
1. 쿠팡 반품 조회
   → 상품: "갤럭시 S24 케이스"
   → 수령인: "홍길동"

2. 네이버페이 검색
   → 페이지 1: 일치하는 주문 찾음!
   → 상품: "갤럭시 S24 투명 케이스"
   → 수령인: "홍길동"

3. 반품 처리
   → 반품 버튼 클릭
   → 사유 선택: "단순 변심"
   → 신청 완료

4. DB 업데이트
   → status: "completed"
   → naver_processed: true
   → naver_process_type: "NAVERPAY_RETURN"
```

---

## 문의

문제 발생 시:
1. 서버 로그 확인 (`loguru` 로그)
2. DB에서 `raw_data` 확인
3. 네이버페이 페이지 HTML 구조 확인
4. GitHub 이슈 등록

---

**설계 완료!** 네이버페이 기반 반품 자동 처리 시스템이 준비되었습니다. 🎉
