# [다운로드쿠폰] 생성 API

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: 고객이 다운받아 사용할 수 있는 쿠폰을 생성
- **URL API Name**: CREATE_COUPON

## 주요 특징
- 쿠폰이 붙은 상품의 총 주문액이 판매자가 설정한 일정금액을 충족해야 사용가능
- 쿠폰은 정률/정액할인으로 발급 가능
- 동일 쿠폰에 **최대 3개의 정책** 생성 가능
  - 예: 10,000원 구매시 1천원 할인, 20,000원 구매시 3천원 할인, 30,000원 구매시 3천원 할인 등
- 한 개의 옵션ID(vendoritem)당 하나의 쿠폰 생성 가능
- 생성 후 **최소 1시간 이후**부터 프론트에 반영
  - 예: 오후 3시에 쿠폰 생성 시 → 가장 빠른 유효기간 시작시간은 오후 4시

## 중요 주의사항
> **다운로드쿠폰은 최초 생성 시 설정한 쿠폰 적용 상품을 추후 바꿀 수 없습니다.**
>
> 만약 쿠폰을 적용할 상품을 추가 혹은 삭제하고 싶은 경우에는 기존에 발행한 쿠폰을 중지하고 새로운 쿠폰을 생성해야 합니다.
>
> **최초 쿠폰 생성 시 쿠폰을 적용할 상품을 신중하게 설정해주세요!**

## Path
```
POST /v2/providers/marketplace_openapi/apis/api/v1/coupons
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/marketplace_openapi/apis/api/v1/coupons
```

---

## Request Parameters

### Body Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| title | O | String | 쿠폰 명칭 - 해당쿠폰 다운로드 페이지 명칭 (고객에게 노출됨) |
| contractId | O | Number | 업체의 계약서ID |
| couponType | O | String | 쿠폰유형 (다운로드쿠폰은 `DOWNLOAD` 사용) |
| startDate | O | String | 쿠폰적용 시작일 (YYYY-MM-DD HH:MM:SS) |
| endDate | O | String | 쿠폰적용 종료일 (YYYY-MM-DD HH:MM:SS) |
| userId | O | String | 사용자 계정 (WING 로그인 ID) |
| policies | O | Array | 쿠폰 세부정책 (최대 3개, 동일 타입만 가능) |

### policies 상세

| Name | Required | Type | Description |
|------|----------|------|-------------|
| title | - | String | 해당쿠폰 정책명칭 - 장바구니에서 쿠폰선택시 노출 (고객에게 노출됨) |
| typeOfDiscount | - | String | 쿠폰 정책유형 (RATE: 정률할인, PRICE: 정액할인) |
| description | - | String | 쿠폰 상세 설명 - 장바구니에서 쿠폰정책 명칭의 부연설명 |
| minimumPrice | - | Number | 쿠폰 적용 최소구매금액 |
| discount | - | Number | 쿠폰 할인금액 또는 비율(%) - RATE: 1~99 정수, PRICE: 10원 단위 금액 |
| maximumDiscountPrice | - | Number | 최대 할인 금액 (RATE일 때 유효, PRICE일 때는 임의의 숫자 입력) |
| maximumPerDaily | - | Number | 최대 발급 개수(1인/1일) - 9,999 초과 입력 불가 |

> **참고**: 한 쿠폰에 서로 다른 타입의 정책 생성 불가
> - PRICE / PRICE → 가능
> - PRICE / RATE → 불가능

### Request Example
```json
{
  "title": "쿠폰 명칭",
  "contractId": "15",
  "couponType": "DOWNLOAD",
  "startDate": "2019-05-22 19:55:00",
  "endDate": "2019-06-08 11:00:00",
  "userId": "testaccout1",
  "policies": [
    {
      "title": "해당쿠폰의 정책 1 명칭",
      "typeOfDiscount": "PRICE",
      "description": "해당정책 안내 문구 작성",
      "minimumPrice": 10000,
      "discount": 1000,
      "maximumDiscountPrice": 1000,
      "maximumPerDaily": 1
    },
    {
      "title": "해당쿠폰의 정책 2 명칭",
      "typeOfDiscount": "PRICE",
      "description": "해당정책 안내 문구 작성",
      "minimumPrice": 20000,
      "discount": 2000,
      "maximumDiscountPrice": 1000,
      "maximumPerDaily": 1
    },
    {
      "title": "해당쿠폰의 정책 3 명칭",
      "typeOfDiscount": "PRICE",
      "description": "해당정책 안내 문구 작성",
      "minimumPrice": 30000,
      "discount": 3000,
      "maximumDiscountPrice": 1000,
      "maximumPerDaily": 1
    }
  ]
}
```

---

## Response Message

| Name | Type | Description |
|------|------|-------------|
| couponId | Number | 쿠폰ID - 쿠폰 아이템 생성/삭제/조회 등에 사용 |
| vendorId | String | 업체 코드 |
| couponType | String | 쿠폰 분류 |
| lastModifiedBy | String | 쿠폰생성(최종수정) 계정 |
| lastModifiedDate | String | 쿠폰생성(최종수정) 시간 |
| title | String | 쿠폰 명칭 |
| publishedDate | String | 발행일 |
| startDate | String | 쿠폰적용 시작일 |
| couponStatus | String | 쿠폰상태 (생성시 STANDBY) |
| couponPolicies | Array | 쿠폰 세부정책 |

### couponPolicies 상세

| Name | Type | Description |
|------|------|-------------|
| description | String | 쿠폰 상세 설명 |
| discount | Number | 쿠폰 할인금액 또는 비율(%) |
| maximumDiscountPrice | Number | 최대 할인 금액 (PRICE일 때는 -1로 노출) |
| maximumPerDaily | Number | 최대 발급 갯수(1인/1일) |
| minimumPrice | Number | 쿠폰 적용 최소구매금액 |
| title | String | 해당쿠폰 정책명칭 |
| typeOfDiscount | String | 쿠폰 정책유형 (RATE, PRICE) |
| manageCode | String | 내부 관리 코드 |

### Response Example
```json
{
  "couponId": 15354534,
  "vendorId": "A00013264",
  "couponType": "DOWNLOAD",
  "lastModifiedBy": "testaccout1",
  "lastModifiedDate": "2019-05-22 15:40:59",
  "title": "쿠폰 명칭",
  "publishedDate": null,
  "startDate": "2019-05-22 19:55:00",
  "couponStatus": "STANDBY",
  "couponPolicies": [
    {
      "description": "해당정책 안내 문구 작성",
      "discount": 1000,
      "maximumDiscountPrice": -1,
      "maximumPerDaily": 1,
      "minimumPrice": 10000,
      "title": "해당쿠폰의 정책 1 명칭",
      "typeOfDiscount": "PRICE",
      "manageCode": "FMS_15_A00013264_15585072594380"
    },
    {
      "description": "해당정책 안내 문구 작성",
      "discount": 2000,
      "maximumDiscountPrice": -1,
      "maximumPerDaily": 1,
      "minimumPrice": 20000,
      "title": "해당쿠폰의 정책 2 명칭",
      "typeOfDiscount": "PRICE",
      "manageCode": "FMS_15_A00013264_15585072594381"
    },
    {
      "description": "해당정책 안내 문구 작성",
      "discount": 3000,
      "maximumDiscountPrice": -1,
      "maximumPerDaily": 1,
      "minimumPrice": 30000,
      "title": "해당쿠폰의 정책 3 명칭",
      "typeOfDiscount": "PRICE",
      "manageCode": "FMS_15_A00013264_15585072594382"
    }
  ]
}
```

---

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지 | 해결 방법 |
|---------------------------|------------|----------|
| 400 (요청변수확인) | contractId=15* (으)로 계약이 판매자=A00012345 에 속하지 않습니다. | 계약서ID(contractId) 값을 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | startAt 패턴을 확인하세요. yyyy-MM-dd HH:mm:ss, 프로모션 기간을 확인해주세요. | 쿠폰적용 시작일(startDate) 값을 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | endAt 패턴을 확인하세요. yyyy-MM-dd HH:mm:ss, 프로모션 기간을 확인해주세요. | 쿠폰적용 종료일(endDate) 값을 올바로 입력했는지 확인합니다. |
| 400 (요청변수확인) | createCouponRequest.title 은 빈칸임. createCouponRequest.title 은 필수임 | 쿠폰 명칭(title) 값을 입력했는지 확인합니다. |
| 400 (요청변수확인) | policies[0] 금액 정보는 10원 단위로 입력해야 합니다. | 쿠폰 할인금액(discount) 값을 10원 단위로 입력했는지 확인합니다. |
| 400 (요청변수확인) | policies[0].maxPerDaily 1~9999 양수만 입력 가능합니다. | 최대 발급 개수(maximumPerDaily) 값을 올바로 입력했는지 확인합니다. |

---

## 즉시할인쿠폰과의 차이점

| 항목 | 즉시할인쿠폰 | 다운로드쿠폰 |
|-----|------------|------------|
| 고객 행동 | 자동 적용 | 고객이 직접 다운로드 |
| 정책 개수 | 1개 | 최대 3개 |
| 최소 구매금액 | 없음 | 설정 가능 |
| 적용 시간 | 다음날 00시부터 | 생성 후 1시간 후부터 |
| API 경로 | /fms/apis/api/v2/ | /marketplace_openapi/apis/api/v1/ |
