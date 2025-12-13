# 상품 조회 API

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: 등록상품 ID(sellerProductId)로 등록된 상품의 정보를 조회
- **용도**:
  - 상품 가격/재고/판매상태 수정 시 필요한 옵션ID(vendorItemId) 확인
  - 상품 정보를 조회하여 상품 수정 시 활용할 수 있는 전문 획득
- **URL API Name**: GET_PRODUCT_BY_PRODUCT_ID

## Path
```
GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{sellerProductId}
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{sellerProductId}
```

---

## Request Parameters

### Path Segment Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| sellerProductId | O | Number | 등록상품ID - 상품 생성 시 결과 값으로 획득한 ID |

### Request Example
```
not require body
```

---

## Response Message (주요 필드)

| Name | Type | Description |
|------|------|-------------|
| code | String | 결과코드 (SUCCESS/ERROR) |
| message | String | 메시지 |
| data | Object | 상품 데이터 |

### data 상세

| Name | Type | Description |
|------|------|-------------|
| sellerProductId | Number | 등록상품ID |
| statusName | String | 등록상품상태 (심사중/임시저장/승인대기중/승인완료/부분승인완료/승인반려/상품삭제) |
| displayCategoryCode | Number | 노출카테고리코드 |
| sellerProductName | String | 등록상품명 (발주서에 사용되는 상품명) |
| vendorId | String | 판매자ID |
| saleStartedAt | String | 판매시작일시 (yyyy-MM-dd'T'HH:mm:ss) |
| saleEndedAt | String | 판매종료일시 (yyyy-MM-dd'T'HH:mm:ss) |
| displayProductName | String | 노출상품명 (쿠팡 판매페이지 노출 상품명) |
| brand | String | 브랜드 |
| generalProductName | String | 제품명 |
| productGroup | String | 상품군 |
| items | Array | 업체상품옵션목록 |

### items (옵션 목록) 상세

| Name | Type | Description |
|------|------|-------------|
| sellerProductItemId | Number | 업체상품옵션아이디 |
| vendorItemId | Number | **옵션아이디** (쿠폰 적용에 사용) - 임시저장 상태는 null, 승인완료 시 값 표시 |
| itemName | String | 업체상품옵션명 |
| originalPrice | Number | 할인율기준가 |
| salePrice | Number | 판매가격 |
| maximumBuyCount | Number | 판매가능수량 |
| outboundShippingTimeDay | Number | 기준출고일(일) |
| adultOnly | String | 19세이상 (ADULT_ONLY/EVERYONE) |
| taxType | String | 과세여부 (TAX/FREE) |
| externalVendorSku | String | 판매자상품코드 (업체상품코드) |
| barcode | String | 바코드 |
| images | Array | 이미지목록 |
| attributes | Array | 옵션목록(속성) |
| offerCondition | String | 상품상태 (NEW/REFURBISHED/USED_BEST/USED_GOOD/USED_NORMAL) |

### 배송 관련 필드

| Name | Type | Description |
|------|------|-------------|
| deliveryMethod | String | 배송방법 (SEQUENCIAL/COLD_FRESH/MAKE_ORDER/AGENT_BUY/VENDOR_DIRECT) |
| deliveryCompanyCode | String | 택배사 코드 |
| deliveryChargeType | String | 배송비종류 (FREE/NOT_FREE/CHARGE_RECEIVED/CONDITIONAL_FREE) |
| deliveryCharge | Number | 기본배송비 |
| freeShipOverAmount | Number | 무료배송 조건 금액 |
| returnCharge | Number | 반품배송비 |

### Response Example (간략화)
```json
{
  "code": "SUCCESS",
  "message": "",
  "data": {
    "sellerProductId": 123459542,
    "sellerProductName": "test_클렌징오일_관리용_상품명",
    "displayCategoryCode": 56137,
    "vendorId": "A0001235",
    "saleStartedAt": "2019-01-09T18:41:14",
    "saleEndedAt": "2099-01-01T23:59:59",
    "displayProductName": "해피바스 솝베리 클렌징 오일",
    "brand": "해피바스",
    "statusName": "승인완료",
    "items": [
      {
        "sellerProductItemId": 1271845812,
        "vendorItemId": 4279191312,
        "itemName": "200ml_1개",
        "originalPrice": 0,
        "salePrice": 1280960,
        "maximumBuyCount": 1,
        "outboundShippingTimeDay": 2,
        "externalVendorSku": "0001"
      },
      {
        "sellerProductItemId": 1271845813,
        "vendorItemId": 4279191317,
        "itemName": "200ml_2개",
        "originalPrice": 13000,
        "salePrice": 10000,
        "maximumBuyCount": 1,
        "outboundShippingTimeDay": 2,
        "externalVendorSku": "0001"
      }
    ]
  }
}
```

---

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지 | 해결 방법 |
|---------------------------|------------|----------|
| 400 (요청변수확인) | 상품 정보가 등록 또는 수정되고 있습니다. 잠시 후 다시 조회해 주시기 바랍니다. | 상품등록 요청 수행 이후 최소 10분 이후에 조회 요청합니다. |
| 400 (요청변수확인) | 업체[A00123456]는 다른 업체[A0011***5]의 상품을 조회할 수 없습니다. | 등록상품ID(sellerProductId) 값을 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | 상품(123456789)의 데이터가 없습니다. | 등록상품ID(sellerProductId) 값을 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | 업체상품아이디[null]는 숫자형으로 입력해주세요. | 등록상품ID(sellerProductId) 값을 올바른 숫자로 입력했는지 확인합니다. |

---

## 등록상품상태 (statusName)

| 상태값 | 설명 |
|-------|------|
| 심사중 | 상품 심사 진행 중 |
| 임시저장 | 임시 저장 상태 |
| 승인대기중 | 승인 대기 중 |
| 승인완료 | 승인 완료 (vendorItemId 확인 가능) |
| 부분승인완료 | 일부 옵션만 승인 완료 |
| 승인반려 | 승인 반려 |
| 상품삭제 | 상품 삭제됨 |

---

## 쿠폰 자동연동에 필요한 핵심 필드

쿠폰을 상품에 적용하려면 `vendorItemId` (옵션ID)가 필요합니다:

```
data.items[].vendorItemId → 쿠폰 적용 시 사용
```

**주의**: `vendorItemId`는 상품이 **승인완료** 상태일 때만 값이 존재합니다. 임시저장 상태에서는 null입니다.
