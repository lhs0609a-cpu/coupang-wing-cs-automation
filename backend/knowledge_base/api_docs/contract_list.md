# (공통) 계약서 목록 조회 API

## 개요
- **API 적용 가능한 구매자 사용자 지역**: 한국
- **설명**: 현재 설정된 모든 계약의 목록을 조회하기 위한 API
- **조회 대상**: 자유계약기반(NON_CONTRACT_BASED)과 계약기반(CONTRACT_BASED) 타입 계약서 모두 조회 가능

## Path
```
GET /v2/providers/fms/apis/api/v2/vendors/{vendorId}/contract/list
```

## Example Endpoint
```
https://api-gateway.coupang.com/v2/providers/fms/apis/api/v2/vendors/A00012345/contract/list
```

---

## Request Parameters

### Path Segment Parameter

| Name | Required | Type | Description |
|------|----------|------|-------------|
| vendorId | O | String | 판매자ID - 쿠팡에서 업체에게 발급한 고유 코드 (예: A00012345) |

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
| data | Object | 계약서 목록 데이터 |
| data.success | Boolean | 성공 여부 (true or false) |
| data.content | Array | 계약서 목록 |
| data.pagination | Object | 페이징 정보 |

### data.content 상세 (계약서 정보)

| Name | Type | Description |
|------|------|-------------|
| contractId | Number | 업체의 계약서 아이디 (예: 1, 2) - **쿠폰 생성에 사용** |
| vendorContractId | Number | 업체의 계약서 코드 (쿠팡 관리 코드) (예: -1, 1, 2) |
| sellerId | String | 판매자ID (예: A00012345) |
| sellerShareRatio | Number | 해당 계약서에 명시된 업체 분담율(%) (예: 100.0) |
| coupangShareRatio | Number | 해당 계약서에 명시된 쿠팡 분담율(%) (예: 100.0) |
| gmvRatio | Number | 월별 매출 비율 (예: 100.0) |
| start | String | 시작일시 (예: 2018-01-22 00:00:00) |
| end | String | 종료일시 (예: 2018-12-31 23:59:59) |
| type | String | 계약 유형 (CONTRACT_BASED, NON_CONTRACT_BASED) |
| usedBudget | Boolean | 예산제한 사용 여부 (기본값: true) |
| modifiedAt | String | 최종 수정 일시 |
| modifiedBy | String | 최종 수정자ID |

### 계약 유형 (type)

| 값 | 설명 |
|----|------|
| CONTRACT_BASED | 계약기반 |
| NON_CONTRACT_BASED | 자유계약기반 |

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
    "content": [
      {
        "contractId": 1,
        "vendorContractId": 2,
        "sellerId": "A00012345",
        "sellerShareRatio": 100,
        "coupangShareRatio": 0,
        "gmvRatio": 10,
        "start": "2017-03-01 00:00:00",
        "end": "2017-12-31 23:59:59",
        "type": "CONTRACT_BASED",
        "useBudget": true,
        "modifiedAt": "2017-09-21 10:57:07",
        "modifiedBy": "pronimance"
      },
      {
        "contractId": 15,
        "vendorContractId": -1,
        "sellerId": "A00013264",
        "sellerShareRatio": 100,
        "coupangShareRatio": 0,
        "gmvRatio": 0,
        "start": "2017-09-25 11:40:01",
        "end": "2999-12-31 23:59:59",
        "type": "NON_CONTRACT_BASED",
        "useBudget": true,
        "modifiedAt": "2017-09-25 11:40:01",
        "modifiedBy": "bcho"
      },
      {
        "contractId": 9962,
        "vendorContractId": 7,
        "sellerId": "A00012345",
        "sellerShareRatio": 100,
        "coupangShareRatio": 0,
        "gmvRatio": 100,
        "start": "2018-01-22 00:00:00",
        "end": "2018-12-31 23:59:59",
        "type": "CONTRACT_BASED",
        "useBudget": true,
        "modifiedAt": "2018-01-22 16:07:10",
        "modifiedBy": "allie"
      }
    ],
    "pagination": null
  }
}
```

---

## Error Spec

| HTTP 상태 코드 (오류 유형) | 오류 메시지 | 해결 방법 |
|---------------------------|------------|----------|
| 401 (요청변수확인) | 업체정보의 권한을 확인하세요. | 판매자ID(vendorId) 값을 올바로 입력했는지 확인합니다. |

---

## 쿠폰 자동연동 활용

### contractId 선택 기준

1. **유효한 계약서 확인**: `start` ~ `end` 기간이 현재 날짜를 포함하는지 확인
2. **자유계약 우선**: `type: NON_CONTRACT_BASED`는 보통 종료일이 2999년으로 설정되어 있어 유연함
3. **쿠폰 생성 시 사용**: 즉시할인쿠폰, 다운로드쿠폰 생성 시 `contractId` 필수

### 유효한 계약서 필터링 예시
```python
from datetime import datetime

def get_valid_contract_id(contracts):
    """현재 유효한 계약서 ID 반환"""
    now = datetime.now()

    for contract in contracts:
        start = datetime.strptime(contract['start'], '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(contract['end'], '%Y-%m-%d %H:%M:%S')

        if start <= now <= end:
            # 자유계약기반 우선
            if contract['type'] == 'NON_CONTRACT_BASED':
                return contract['contractId']

    # 자유계약 없으면 첫 번째 유효한 계약 반환
    for contract in contracts:
        start = datetime.strptime(contract['start'], '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(contract['end'], '%Y-%m-%d %H:%M:%S')

        if start <= now <= end:
            return contract['contractId']

    return None
```
