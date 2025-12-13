# [즉시할인쿠폰] 생성 API

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: 계약서ID(contractId)에 기반한 신규 쿠폰 생성을 위한 API
- **처리 방식**: 비동기방식 (요청만 수행, 실제 결과는 `requestedId`로 요청상태 확인 API를 통해 확인)

## 중요 주의사항
> **즉시할인쿠폰은 최초 생성 시 설정한 쿠폰 적용 상품을 추후 삭제할 수 없습니다.**
>
> 만약 쿠폰을 적용할 상품을 삭제하고 싶은 경우에는 기존에 발행한 쿠폰을 중지하고 새로운 쿠폰을 생성해야 합니다.
>
> **최초 쿠폰 생성 시 쿠폰을 적용할 상품을 신중하게 설정해주세요!**

## Path
```
POST /v2/providers/fms/apis/api/v2/vendors/{vendorId}/coupon
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/fms/apis/api/v2/vendors/A00012345/coupon
```

---

## Request Parameters

### Path Segment Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| vendorId | O | String | 판매자ID - 쿠팡에서 업체에게 발급한 고유 코드 (예: A00012345) |

### Body Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| contractId | O | Number | 업체의 계약서ID |
| name | O | String | 프로모션명 (최대 45자) |
| maxDiscountPrice | O | Number | 최대할인금액 - 최소 10원 이상 |
| discount | O | Number | 할인률 |
| startAt | O | String | 유효시작일 - 다음날 00시부터 작동하도록 설정 가능 (예: 8월4일 15시에 쿠폰 생성 시 8월5일 00시부터 적용) |
| endAt | O | String | 유효종료일 |
| type | O | String | 할인방식 - `RATE`(정률할인), `FIXED_WITH_QUANTITY`(수량별 정액할인), `PRICE`(정액할인) |
| wowExclusive | - | Boolean | 발행 대상 - 쿠폰을 사용할 수 있는 대상 |

### wowExclusive 값 설명

| 값 | 설명 |
|----|------|
| false | 전체고객 (기본값) |
| true | 로켓와우회원한정 |

> **참고**: 일반 다운로드 쿠폰은 `false`로 생성해주시기 바랍니다.
>
> `true`는 로켓와우 회원을 대상으로 골드박스 등 기획전에 선정된 상품에 대해 적용하는 값이며, 상품에 적용 시 사전 승인이 필요합니다.

### Request Example
```json
{
  "contractId": "10",
  "name": "newCoupon 20180328",
  "maxDiscountPrice": "1000",
  "discount": "10",
  "startAt": "2017-12-08 00:00:00",
  "endAt": "2017-12-09 00:00:00",
  "type": "PRICE",
  "wowExclusive": "false"
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
| data.pagination | null | 페이징 없음 |

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
      "requestedId": "123543582159745830895",
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
| 400 (요청변수확인) | 계약의 유효기간 안에 쿠폰이 존재해야 한다(계약서의 유효기간:2017-03-01 00:00:00~2017-12-31 23:59:59) (쿠폰의 유효기간:2016-12-05 00:00:00~2017-09-05 00:00:00) | 계약서의 유효기간 안에 쿠폰의 유효시작일과 종료일이 포함되었는지 확인합니다. |
| 400 (요청변수확인) | Cannot parse "2017-13-05 00:00:00": Value 13 for monthOfYear must be in the range [1,12] | 유효시작일 또는 종료일 값을 올바르게 입력했는지 확인합니다. |
| 400 (요청변수확인) | Cannot parse "2017-08-32 00:00:00": Value 32 for dayOfMonth must be in the range [1,31] | 유효시작일 또는 종료일 값을 올바르게 입력했는지 확인합니다. |
| 400 (요청변수확인) | startAt 패턴을 확인하세요. yyyy-MM-dd HH:mm:ss | 유효시작일 값을 올바른 형식으로 입력했는지 확인합니다. |
| 400 (요청변수확인) | endAt 패턴을 확인하세요. yyyy-MM-dd HH:mm:ss | 유효종료일 값을 올바른 형식으로 입력했는지 확인합니다. |
| 400 (요청변수확인) | discount 양수만 입력 가능합니다. (정률은 1~100, 정액은 1이상) | 할인율(discount) 값을 올바르게 입력했는지 확인합니다. |

---

## 할인방식(type) 상세

| Type | 설명 |
|------|------|
| RATE | 정률할인 - 상품 가격의 일정 비율 할인 |
| FIXED_WITH_QUANTITY | 수량별 정액할인 - 수량에 따른 정액 할인 |
| PRICE | 정액할인 - 고정 금액 할인 |

---

## 참고사항
- 비동기 API이므로 응답의 `requestedId`를 사용하여 별도의 요청상태 확인 API를 호출해야 실제 처리 결과를 확인할 수 있습니다.
- 유효시작일은 쿠폰 생성 다음날 00시부터 설정 가능합니다.
- 쿠폰 적용 상품은 한번 설정하면 삭제할 수 없으므로 신중하게 설정해야 합니다.
