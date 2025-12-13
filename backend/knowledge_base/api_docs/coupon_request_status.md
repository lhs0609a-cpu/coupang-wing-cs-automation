# [즉시할인쿠폰] 요청상태 확인 API

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: requestedId를 통해 즉시할인 쿠폰 API의 요청 결과를 확인
- **용도**: 쿠폰생성, 쿠폰파기, 쿠폰아이템 생성, 쿠폰아이템 파기 API 요청 시 반환되는 requestedId 값을 가지고 성공/실패(DONE/FAIL) 결과를 확인

## Path
```
GET /v2/providers/fms/apis/api/v1/vendors/{vendorId}/requested/{requestedId}
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/fms/apis/api/v1/vendors/A00000001/requested/649102321051192483
```

---

## Request Parameters

### Path Segment Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| vendorId | O | String | 판매자ID - 쿠팡에서 업체에게 발급한 고유 코드 (예: A00012345) |
| requestedId | O | Number | 결과를 조회할 ID (쿠폰 API 응답에서 받은 값) |

### Request Example
```
not require body
```

---

## Response Message

| Name | Type | Description |
|------|------|-------------|
| code | Number | 서버 응답 코드 |
| message | String | 서버 응답 메세지 |
| httpStatus | Number | HTTP Status Code |
| httpStatusMessage | String | HTTP Status Message |
| errorMessage | String | HTTP Status 200을 제외한 나머지 Status에서 상세 실패 이유 |
| data | Object | 수행 성공 여부 데이터 |
| data.success | Boolean | 성공 여부 (true or false) |
| data.content | Object | 처리 상태를 조회할 수 있는 요청ID 데이터 |
| data.pagination | null | 페이징 없음 |

### data.content 상세

| Name | Type | Description |
|------|------|-------------|
| couponId | Number | 쿠폰 ID (예: 70, 85, 778) |
| requestedId | String | 처리 상태 조회를 위한 요청ID |
| status | String | 처리 상태 |
| succeeded | Number | 성공 개수 |
| total | Number | 요청 건수 (쿠폰 아이템생성의 경우 vendorItemId의 전체 갯수) |
| type | String | 요청타입 |
| failed | Number | 실패 개수 |
| failedVendorItems | Array | 실패한 정보에 대한 상세 데이터 |

### 처리 상태 (status)

| 구분코드 | 설명 |
|---------|------|
| REQUESTED | 요청됨 (처리 중) |
| FAIL | 실패 |
| DONE | 성공 |

### 요청타입 (type)

| 구분코드 | 설명 |
|---------|------|
| COUPON_PUBLISH | 쿠폰생성 |
| COUPON_EXPIRE | 쿠폰파기 |
| COUPON_ITEM_PUBLISH | 쿠폰아이템생성 |
| COUPON_ITEM_EXPIRE | 쿠폰아이템 파기 |

### failedVendorItems 상세

| Name | Type | Description |
|------|------|-------------|
| reason | String | 실패 이유 |
| vendorItemId | Long | 실패한 vendorItemId |

### Response Example
```json
{
  "code": 200,
  "message": "OK",
  "httpStatus": 200,
  "httpStatusMessage": "OK",
  "errorMessage": "",
  "data": {
    "success": true,
    "content": {
      "couponId": 778,
      "requestedId": "4080133932843441",
      "type": "COUPON_PUBLISH",
      "status": "DONE",
      "total": 1,
      "succeeded": 1,
      "failed": 0,
      "failedVendorItems": []
    },
    "pagination": null
  }
}
```

---

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지 | 해결 방법 |
|---------------------------|------------|----------|
| 400 (요청변수확인) | 업체정보의 권한을 확인하세요. | 올바른 판매자ID(vendorId) 값을 입력했는지 확인합니다. |

### 실패 사유 예시 (failedVendorItems)

| 오류 코드 | 오류 메시지 | 해결 방법 |
|----------|------------|----------|
| CIE00 | 유효하지 않은 옵션아이디 입니다. | 올바른 옵션ID(vendorItemId)를 입력했는지 확인합니다. |
| CIR06 | 옵션 상품을 찾지 못했습니다. | 올바른 옵션ID(vendorItemId)를 입력했는지 확인합니다. |
| CIR08 | 해당 옵션은 이미 다른 쿠폰에 발행되어져 있습니다. | 다른 쿠폰이 이미 적용된 상품입니다. |

---

## 쿠폰 자동연동 활용

```python
# 비동기 처리 결과 확인 예시
import time

def wait_for_coupon_result(vendor_id, requested_id, max_retries=10):
    """쿠폰 처리 결과를 폴링하여 확인"""
    for i in range(max_retries):
        result = get_request_status(vendor_id, requested_id)
        status = result['data']['content']['status']

        if status == 'DONE':
            return {'success': True, 'data': result}
        elif status == 'FAIL':
            failed_items = result['data']['content']['failedVendorItems']
            return {'success': False, 'failed_items': failed_items}

        # REQUESTED 상태면 대기 후 재시도
        time.sleep(2)

    return {'success': False, 'error': 'Timeout'}
```
