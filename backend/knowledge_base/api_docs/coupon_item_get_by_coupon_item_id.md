# [즉시할인쿠폰] 단건 조회 API (couponItemId)

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: 현재 적용된 쿠폰아이템을 쿠폰아이템ID로 조회하기 위한 API

## Path
```
GET /v2/providers/fms/apis/api/v1/vendors/{vendorId}/coupons/{couponId}/items/{couponItemId}
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/fms/apis/api/v1/vendors/A00012345/coupons/77/items/80984?type=couponItemId
```

---

## Request Parameters

### Path Segment Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| vendorId | O | String | 판매자ID - 쿠팡에서 업체에게 발급한 고유 코드 (예: A00012345) |
| couponId | O | Number | 쿠폰ID |
| couponItemId | O | Number | 쿠폰아이템ID |

### Query String Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| type | O | String | `couponItemId` (고정값) |

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
| httpStatus | Number | HTTP Status Code (서버 응답 코드와 동일한 값) |
| httpStatusMessage | String | HTTP Status Message (서버 응답 메세지와 동일한 값) |
| errorMessage | String | HTTP Status 200을 제외한 나머지 Status에서 서버 내 상세한 실패 이유 메세지 |
| data | Object | 쿠폰 아이템 정보 리스트 데이터 |
| data.success | Boolean | 성공 여부 (true or false) |
| data.content | Object | 쿠폰 아이템 리스트 |
| data.content.couponItemId | Number | 쿠폰아이템ID (예: 80984) |
| data.content.couponId | Number | 쿠폰ID (예: 75, 80) |
| data.content.vendorItemId | Number | 옵션ID (예: 3223826213) |
| data.content.startAt | String | 유효시작일 (예: 2017-08-04 01:00:00) |
| data.content.endAt | String | 유효종료일 (예: 2017-09-01 00:00:00) |
| data.content.status | String | 쿠폰상태 |
| data.pagination | Array | 단건 조회로 페이징 없음 |

### 쿠폰 상태 (status)

| 구분코드 | 설명 |
|---------|------|
| STANDBY | 대기중 |
| APPLIED | 사용중 |
| PAUSED | 발행중지 |
| EXPIRED | 사용종료 |

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
      "couponItemId": 80984,
      "couponId": 77,
      "vendorItemId": 3223826213,
      "startAt": "2017-08-04 01:00:00",
      "endAt": "2017-09-01 00:00:00",
      "status": "APPLIED"
    },
    "pagination": null
  }
}
```

---

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지 | 해결 방법 |
|---------------------------|------------|----------|
| 400 (요청변수확인) | 업체정보의 권한을 확인하세요 | 판매자ID(vendorId) 값을 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | 쿠폰아이디를 확인해주세요 208463**** | 쿠폰ID(couponId) 값을 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | couponId 1875***에서 아이템을 찾을 수 없습니다. | 쿠폰아이템ID(couponItemId) 값을 올바로 입력했는지 확인합니다. |
