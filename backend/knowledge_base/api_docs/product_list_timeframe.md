# 상품 목록 구간 조회 API

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: 등록된 상품 목록을 생성일시 기준으로 조회
- **제한사항**: 최대 조회 범위는 **10분**
- **URL API Name**: GET_PRODUCTS_BY_TIME_FRAME

## Path
```
GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/time-frame
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/time-frame?vendorId=A00012345&createdAtFrom=2020-02-19T10:43:30&createdAtTo=2020-02-19T10:50:30
```

---

## Request Parameters

### Query String Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| vendorId | O | String | 판매자 ID - 쿠팡에서 업체에게 발급한 고유 코드 (예: A00012345) |
| createdAtFrom | O | String | 생성 시작일시 (yyyy-MM-ddTHH:mm:ss 형식) |
| createdAtTo | O | String | 생성 종료일시 (yyyy-MM-ddTHH:mm:ss 형식) |

### Request Example
```
not require body
```

---

## Response Message

| Name | Type | Description |
|------|------|-------------|
| code | String | 결과코드 (SUCCESS/ERROR) |
| message | String | 결과 메세지 |
| data | Array | 등록상품목록 (조회된 업체상품 개수만큼 N번 반복) |

### data 상세

| Name | Type | Description |
|------|------|-------------|
| sellerProductId | Number | 등록상품ID |
| sellerProductName | String | 등록상품명 (20자 이하) |
| displayCategoryCode | Number | 노출카테고리코드 |
| vendorId | String | 판매자 ID |
| saleStartedAt | String | 판매시작일시 (yyyy-MM-ddTHH:mm:ss) |
| saleEndedAt | String | 판매종료일시 (yyyy-MM-ddTHH:mm:ss) |
| brand | String | 브랜드 |
| statusName | String | 등록상품 상태명 |
| createdAt | String | 판매등록일시 (yyyy-MM-ddTHH:mm:ss) |

### 등록상품 상태 (statusName)

| Parameter Name | Status |
|---------------|--------|
| IN_REVIEW | 심사중 |
| SAVED | 임시저장 |
| APPROVING | 승인대기중 |
| APPROVED | 승인완료 |
| PARTIAL_APPROVED | 부분승인완료 |
| DENIED | 승인반려 |
| DELETED | 상품삭제 |

### Response Example
```json
{
  "code": "SUCCESS",
  "message": "",
  "data": [
    {
      "sellerProductId": 123,
      "sellerProductName": "[인xx] 컴퓨터잡지",
      "displayCategoryCode": null,
      "categoryId": 5555,
      "productId": 3333,
      "vendorId": "A0xxxxx",
      "mdId": "jxxx@",
      "mdName": "박xxx",
      "saleStartedAt": "2015-12-28T06:00:00",
      "saleEndedAt": "2099-01-01T00:00:00",
      "brand": null,
      "statusName": "승인완료",
      "createdAt": "2015-12-28T18:57:34"
    }
  ]
}
```

---

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지 | 해결 방법 |
|---------------------------|------------|----------|
| 400 (요청변수확인) | 업체[A0012345]는 다른 업체[skma***]의 상품목록을 조회할 수 없습니다. | 판매자ID(vendorId)를 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | 검색 허용 범위를 초과했습니다. 최대 허용 범위는 10분입니다. | 조회 시작일(createdAtFrom)과 종료일(createdAtTo)을 올바로 입력했는지 확인합니다. 최대 10분 이내만 조회가 가능합니다. |

---

## 주의사항

> **최대 조회 범위: 10분**
>
> 이 API는 실시간 모니터링 용도로 설계되어 있어, 한 번에 최대 10분 범위만 조회 가능합니다.
>
> 쿠폰 자동연동 기능에는 **상품 목록 페이징 조회 API**가 더 적합합니다.

## 활용 예시

### 10분 간격 실시간 모니터링
```
GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/time-frame
  ?vendorId=A00012345
  &createdAtFrom=2024-01-01T10:00:00
  &createdAtTo=2024-01-01T10:10:00
```
