# [다운로드쿠폰] 아이템 생성 API

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: 옵션상품(vendorItemId)에 생성된 다운로드 쿠폰을 적용하기 위한 API
- **URL API Name**: Add_VENDOR_ITEMS_TO_COUPON

## 중요 주의사항
> **상품 추가에 실패하면 해당 쿠폰은 파기됩니다.**
>
> 쿠폰 적용 전 vendorItemId가 유효한지 반드시 확인하세요!

## Path
```
PUT /v2/providers/marketplace_openapi/apis/api/v1/coupon-items
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/marketplace_openapi/apis/api/v1/coupon-items
```

---

## Request Parameters

### Body Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| couponItems | O | Array | 상품 쿠폰적용을 위한 데이터 |

### couponItems 상세

| Name | Required | Type | Description |
|------|----------|------|-------------|
| couponId | - | Number | 쿠폰ID (쿠폰생성 Response에서 확인 가능) |
| userId | - | String | 사용자 계정 (WING 로그인 ID) |
| vendorItemIds | - | Array | 쿠폰 적용하고자 하는 옵션ID(s) - **한 번에 100개 초과 불가** |

### Request Example
```json
{
  "couponItems": [
    {
      "couponId": "15350660",
      "userId": "testaccount1",
      "vendorItemIds": [
        2306264997,
        4802314648,
        4230264914
      ]
    }
  ]
}
```

---

## Response Message

| Name | Type | Description |
|------|------|-------------|
| requestResultStatus | String | 호출 결과 (SUCCESS / FAIL) |
| body | Object | 응답 본문 |
| body.couponId | Integer | 해당 쿠폰 ID |
| errorCode | String | 에러발생 시 분류 |
| errorMessage | String | 에러 상세내용 |

### Response Example
```json
{
  "requestResultStatus": "SUCCESS",
  "body": {
    "couponId": 15350660
  },
  "errorCode": null,
  "errorMessage": null
}
```

---

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지 | 해결 방법 |
|---------------------------|------------|----------|
| 400 (요청변수확인) | 삭제된 프로모션 입니다. | 쿠폰ID(couponId) 값을 올바로 입력했는지 확인합니다. 옵션에 쿠폰 적용이 실패하여 쿠폰ID가 삭제되었는지 확인합니다. |

---

## 즉시할인쿠폰 아이템 생성과의 차이점

| 항목 | 즉시할인쿠폰 | 다운로드쿠폰 |
|-----|------------|------------|
| HTTP Method | POST | PUT |
| 최대 적용 개수 | 10,000개 | 100개 |
| 처리 방식 | 비동기 (requestedId로 확인) | 동기 (즉시 결과 반환) |
| 실패 시 | 부분 성공 가능 | **쿠폰 파기** |
| API 경로 | /fms/apis/api/v1/ | /marketplace_openapi/apis/api/v1/ |

---

## 쿠폰 자동연동 활용

```python
# 다운로드쿠폰에 상품 적용 예시
payload = {
    "couponItems": [
        {
            "couponId": "15350660",
            "userId": "wing_login_id",
            "vendorItemIds": [
                4279191312,  # 상품1의 vendorItemId
                4279191317   # 상품2의 vendorItemId
            ]
        }
    ]
}
```

**주의**: 한 번에 최대 100개의 옵션ID만 적용 가능합니다. 100개 초과 시 여러 번 나눠서 호출해야 합니다.
