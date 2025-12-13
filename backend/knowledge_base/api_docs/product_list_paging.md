# 상품 목록 페이징 조회 API

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: 등록상품 목록을 페이징 조회
- **URL API Name**: GET_PRODUCTS_BY_QUERY

## Path
```
GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/seller_api/apis/api/v1/marketplace/seller-products?vendorId={vendorId}&nextToken={nextToken}&maxPerPage={maxPerSize}&sellerProductId={sellerProductId}&sellerProductName={sellerProductName}&status={status}&manufacture={manufacture}&createdAt={createdAt}
```

---

## Request Parameters

### Query String Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| vendorId | O | String | 판매자 ID - 쿠팡에서 업체에게 발급한 고유 코드 (예: A00012345) |
| nextToken | - | Number | 페이지 - 다음 페이지를 호출하기 위한 키값. 첫 페이지 호출시에는 넣지 않거나 1 입력 |
| maxPerPage | - | Number | 페이지당 건수 (기본값: 10, 최대값: 100) |
| sellerProductId | - | Number | 등록상품ID |
| sellerProductName | - | String | 등록상품명 검색 (20자 이하) |
| status | - | String | 업체상품상태 |
| manufacture | - | String | 제조사 |
| createdAt | - | String | 상품등록일시 (yyyy-MM-dd 형식) |

### 업체상품상태 (status) 옵션

| Parameter Name | Status |
|---------------|--------|
| IN_REVIEW | 심사중 |
| SAVED | 임시저장 |
| APPROVING | 승인대기중 |
| APPROVED | 승인완료 |
| PARTIAL_APPROVED | 부분승인완료 |
| DENIED | 승인반려 |
| DELETED | 상품삭제 |

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
| nextToken | String | 다음페이지 (다음 페이지가 없을 경우 빈문자열) |
| data | Array | 상품 목록 |

### data 상세

| Name | Type | Description |
|------|------|-------------|
| sellerProductId | Number | 등록상품ID |
| sellerProductName | String | 등록상품명 |
| displayCategoryCode | Number | 노출카테고리코드 |
| categoryId | Number | 카테고리아이디 |
| productId | Number | ProductID |
| vendorId | String | 판매자ID |
| saleStartedAt | String | 판매시작일시 (yyyy-MM-ddTHH:mm:ss) |
| saleEndedAt | String | 판매종료일시 (yyyy-MM-ddTHH:mm:ss) |
| brand | String | 브랜드 |
| statusName | String | 등록상품상태 |
| createdAt | String | 판매등록일시 (yyyy-MM-ddTHH:mm:ss) |

### Response Example
```json
{
  "code": "SUCCESS",
  "message": "",
  "nextToken": "2",
  "data": [
    {
      "sellerProductId": 239092172,
      "sellerProductName": "R07 헬로키티 미니낚시놀이",
      "displayCategoryCode": 77413,
      "categoryId": 2102,
      "productId": 14784194,
      "vendorId": "XXXXXXXX",
      "mdId": "harry867@",
      "mdName": null,
      "saleStartedAt": "2017-02-14T06:00:00",
      "saleEndedAt": "2099-12-31T00:00:00",
      "brand": "상세설명별도참조",
      "statusName": "승인완료",
      "createdAt": "2017-02-13T02:09:47"
    },
    {
      "sellerProductId": 239092161,
      "sellerProductName": "R07 러닝리소스 손가락 지시봉 (10개 세트)",
      "displayCategoryCode": 77413,
      "categoryId": 2102,
      "productId": 14784126,
      "vendorId": "XXXXXXXX",
      "mdId": "harry867@",
      "mdName": null,
      "saleStartedAt": "2017-02-14T06:00:00",
      "saleEndedAt": "2099-12-31T00:00:00",
      "brand": "상세설명별도참조",
      "statusName": "승인완료",
      "createdAt": "2017-02-13T02:09:46"
    }
  ]
}
```

---

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지 | 해결 방법 |
|---------------------------|------------|----------|
| 400 (요청변수확인) | 업체코드는 반드시 입력되어야 합니다. | 판매자 ID(vendorId) 값을 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | Format of createdAt is `yyyy-MM-dd` | 상품등록일시(createdAt) 값을 올바른 형식으로 입력했는지 확인합니다. |

---

## 쿠폰 자동연동 활용 방법

### 1. 특정 날짜 등록 상품 조회 (1일 전 등록 상품)
```
GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products
  ?vendorId=A00012345
  &status=APPROVED
  &createdAt=2024-01-01
  &maxPerPage=100
```

### 2. 승인완료 상품만 필터링
- `status=APPROVED` 파라미터 사용
- 승인완료된 상품만 `vendorItemId`가 존재함

### 3. 페이징 처리
- `nextToken`으로 다음 페이지 호출
- 빈 문자열이면 마지막 페이지
