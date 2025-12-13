# Coupang Return API Documentation

## 개요
쿠팡 Wing Open API를 사용한 반품/취소 요청 조회 API 문서

## Base URL
```
https://api-gateway.coupang.com
```

## 인증
- **Type**: HMAC SHA256
- **Required Headers**:
  - `Authorization`: HMAC 서명
  - `Content-Type`: application/json

## API Endpoints

### 1. 반품/취소 요청 목록 조회

#### Endpoint
```
GET /v2/providers/openapi/apis/api/v6/vendors/{vendorId}/returnRequests
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `searchType` | string | Yes | 조회 방식 (기본: "timeFrame") |
| `createdAtFrom` | string | Yes | 검색 시작일 (yyyy-MM-dd 또는 yyyy-MM-ddTHH:mm) |
| `createdAtTo` | string | Yes | 검색 종료일 (yyyy-MM-dd 또는 yyyy-MM-ddTHH:mm) |
| `cancelType` | string | No | RETURN(반품), CANCEL(취소), 미지정 시 전체 |
| `status` | string | No | 반품상태 (cancelType=CANCEL일 경우 사용 불가) |
| `orderId` | integer | No | 주문번호 (status 없이 조회 시 필수) |
| `maxPerPage` | integer | No | 페이지당 최대 조회 수 (timeFrame에서는 미지원, 기본: 50) |

#### Status Codes

반품 상태 (`status` 파라미터):
- `RU`: 출고중지요청 (RELEASE_STOP_UNCHECKED)
- `UC`: 반품접수 (RETURNS_UNCHECKED)
- `CC`: 반품완료 (CANCEL_COMPLETED)
- `PR`: 쿠팡확인요청 (PENDING_REVIEW)

#### Request Example
```bash
GET /v2/providers/openapi/apis/api/v6/vendors/A00492891/returnRequests?searchType=timeFrame&createdAtFrom=2024-11-01T00:00&createdAtTo=2024-11-16T23:59&cancelType=RETURN
```

#### Response Format
```json
{
  "code": "SUCCESS",
  "message": "OK",
  "data": [
    {
      "receiptId": 1538297475,
      "orderId": "25100152210611",
      "returnItems": [
        {
          "vendorItemId": "12345",
          "vendorItemPackageName": "상품명",
          "vendorItemName": "상품 상세명",
          "cancelCount": 1,
          "cancelReasonCategory1": "고객변심",
          "cancelReasonCategory2": "묶음 배송"
        }
      ],
      "receiptType": "RETURN",
      "receiptStatus": "RELEASE_STOP_UNCHECKED",
      "shippingTo": {
        "name": "홍길동",
        "phoneNumber": "010-1234-5678"
      }
    }
  ]
}
```

## 구현 코드

### Python Client Example
```python
from backend.app.services.coupang_api_client import CoupangAPIClient

# Initialize client
client = CoupangAPIClient(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    vendor_id="YOUR_VENDOR_ID"
)

# Fetch return requests
result = client.get_return_requests(
    start_date="2024-11-01T00:00",
    end_date="2024-11-16T23:59",
    cancel_type="RETURN",  # RETURN, CANCEL, or None
    status="RU"  # Optional: filter by status
)
```

### API Client Location
- **File**: `backend/app/services/coupang_api_client.py`
- **Class**: `CoupangAPIClient`
- **Method**: `get_return_requests()`

## 주의사항

1. **Timeout 이슈**
   - 장기간 조회 시 Gateway Timeout (504) 발생 가능
   - 권장: 7일 이하의 기간으로 분할 조회
   - 에러 메시지: "Request timed out, if the situation continues consider applying timeout extension."

2. **Date Format**
   - `searchType=timeFrame`일 경우: `yyyy-MM-ddTHH:mm` 형식 권장
   - 분 단위까지 지정 가능

3. **Parameters 조합**
   - `cancelType=CANCEL`일 경우 `status` 파라미터 사용 불가
   - `status` 없이 조회 시 `orderId` 필수

4. **Rate Limiting**
   - 쿠팡 API는 rate limit이 있을 수 있음
   - 과도한 요청 시 일시적으로 차단될 수 있음

## 데이터베이스 저장

조회된 반품 데이터는 다음 테이블에 저장됩니다:

### return_logs Table Schema
```sql
CREATE TABLE return_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coupang_receipt_id INTEGER,
    coupang_order_id VARCHAR(50),
    product_name TEXT,
    receiver_name VARCHAR(100),
    receiver_phone VARCHAR(20),
    receipt_type VARCHAR(20),
    receipt_status VARCHAR(50),
    cancel_count INTEGER,
    cancel_reason_category1 VARCHAR(100),
    cancel_reason_category2 VARCHAR(100),
    naver_processed BOOLEAN DEFAULT 0,
    naver_processed_at DATETIME,
    naver_process_type VARCHAR(20),
    status VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Backend API Endpoints

### 1. Fetch from Coupang
```
GET /api/returns/fetch-from-coupang?start_date=2024-11-01T00:00&end_date=2024-11-16T23:59
```

### 2. List Saved Returns
```
GET /api/returns/list?offset=0&limit=100
```

### 3. Statistics
```
GET /api/returns/statistics
```

## Troubleshooting

### 504 Gateway Timeout
**문제**: 쿠팡 API에서 504 에러 발생
**해결책**:
- 조회 기간을 7일 이하로 단축
- 여러 번으로 나눠서 조회
- 배치 크기 조정

### 400 Bad Request
**문제**: 잘못된 파라미터
**해결책**:
- 날짜 형식 확인 (yyyy-MM-ddTHH:mm)
- cancelType과 status 조합 확인

### 401 Unauthorized
**문제**: 인증 실패
**해결책**:
- Access Key, Secret Key, Vendor ID 확인
- HMAC 서명 생성 로직 확인

## 변경 이력

- 2024-11-16: 초기 문서 작성
- API 구현 위치: `backend/app/services/coupang_api_client.py`
- Router 구현: `backend/app/routers/return_management.py`
