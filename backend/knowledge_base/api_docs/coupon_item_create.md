# [즉시할인쿠폰] 아이템 생성 API

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: 생성된 쿠폰을 개별 아이템에 적용하기 위한 API
- **처리 방식**: 비동기방식 (요청만 수행, 실제 결과는 `requestedId`로 요청상태 확인 API를 통해 확인)

## Path
```
POST /v2/providers/fms/apis/api/v1/vendors/{vendorId}/coupons/{couponId}/items
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/fms/apis/api/v1/vendors/A00012345/coupons/68/items
```

---

## Request Parameters

### Path Segment Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| vendorId | O | String | 판매자ID - 쿠팡에서 업체에게 발급한 고유 코드 (예: A00012345) |
| couponId | O | Number | 적용할 쿠폰ID |

### Body Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| vendorItems | O | Array | 쿠폰을 적용할 옵션ID - 한 번에 적용할 옵션ID 수는 **10,000개를 초과할 수 없음** |

### Request Example
```json
{
  "vendorItems": [
    3226138951,
    3226138847
  ]
}
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
| data | Object | 수행 성공 여부 데이터 |
| data.success | Boolean | 성공 여부 (true or false) |
| data.content | Object | 처리 상태를 조회할 수 있는 요청아이디 데이터 |
| data.content.requestedId | String | 처리 상태 조회를 위한 요청아이디 (예: 1542675975663862164) |
| data.content.success | Boolean | 성공 여부 (true or false) |
| data.pagination | Array | 페이징 없음 (null) |

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
      "requestedId": "17258005702255081464",
      "success": true
    },
    "pagination": null
  }
}
```

---

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지 | 해결 방법 |
|---------------------------|------------|----------|
| 400 (요청변수확인) | vendorItems may not be empty, vendorItems size must be between 1 and 10000 | 쿠폰을 적용할 옵션ID(vendorItems)를 올바로 입력했는지 확인합니다. 한 번에 적용할 옵션ID 수는 10,000개를 초과할 수 없습니다. |
| 400 (요청변수확인) | 업체정보의 권한을 확인하세요 | 판매자ID(vendorId) 값을 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | 쿠폰아이디를 확인해주세요 208463**** | 쿠폰ID(couponId) 값을 올바로 입력했는지 확인합니다. |

---

## 참고사항
- 비동기 API이므로 응답의 `requestedId`를 사용하여 별도의 요청상태 확인 API를 호출해야 실제 처리 결과를 확인할 수 있습니다.
- 한 번에 최대 10,000개의 옵션ID를 처리할 수 있습니다.
