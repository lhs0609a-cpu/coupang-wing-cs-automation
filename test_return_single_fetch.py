"""
반품요청 단건 조회 API 테스트
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.services.coupang_api_client import CoupangAPIClient
from app.models.coupang_account import CoupangAccount
from app.models.return_log import ReturnLog
import json


def test_single_return_fetch():
    """단건 조회 테스트"""
    print("=" * 80)
    print("반품요청 단건 조회 테스트")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 쿠팡 계정 조회
        coupang_account = db.query(CoupangAccount).first()

        if not coupang_account:
            print("[ERROR] 쿠팡 계정이 등록되지 않았습니다.")
            return

        # API 클라이언트 생성
        api_client = CoupangAPIClient(
            vendor_id=coupang_account.vendor_id,
            access_key=coupang_account.access_key,
            secret_key=coupang_account.secret_key
        )

        # DB에서 최근 receipt_id 조회
        recent_log = db.query(ReturnLog).order_by(ReturnLog.created_at.desc()).first()

        if not recent_log:
            print("[WARN] DB에 반품 로그가 없습니다. 먼저 목록 조회를 실행해주세요.")
            print("\n테스트용 receipt_id를 직접 입력하시겠습니까? (예: 50229613)")
            receipt_id_input = input("Receipt ID (Enter를 누르면 테스트 종료): ")

            if not receipt_id_input.strip():
                print("테스트를 종료합니다.")
                return

            receipt_id = int(receipt_id_input.strip())
        else:
            receipt_id = recent_log.coupang_receipt_id
            print(f"\n[INFO] DB에서 조회한 최근 receipt_id: {receipt_id}")
            print(f"  - 상품명: {recent_log.product_name}")
            print(f"  - 상태: {recent_log.receipt_status}")

        # 단건 조회 실행
        print(f"\n{'='*80}")
        print(f"단건 조회 실행: receiptId={receipt_id}")
        print(f"{'='*80}\n")

        result = api_client.get_return_request_by_receipt_id(receipt_id)

        if result and "data" in result:
            print(f"[SUCCESS] API 응답 수신")
            print(f"  - 응답 코드: {result.get('code')}")
            print(f"  - 메시지: {result.get('message')}")

            data = result["data"]
            # 배열인 경우 첫 번째 항목
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
            else:
                item = data

            print(f"\n[반품 상세 정보]")
            print(f"  - Receipt ID: {item.get('receiptId')}")
            print(f"  - Order ID: {item.get('orderId')}")
            print(f"  - Payment ID: {item.get('paymentId')}")
            print(f"  - 반품 유형: {item.get('receiptType')}")
            print(f"  - 상태: {item.get('receiptStatus')}")
            print(f"  - 접수 시간: {item.get('createdAt')}")
            print(f"  - 수정 시간: {item.get('modifiedAt')}")
            print(f"\n[신청인 정보]")
            print(f"  - 이름: {item.get('requesterName')}")
            print(f"  - 전화번호: {item.get('requesterPhoneNumber')}")
            print(f"  - 실전화번호: {item.get('requesterRealPhoneNumber')}")
            print(f"  - 주소: {item.get('requesterAddress')}")
            print(f"  - 상세주소: {item.get('requesterAddressDetail')}")
            print(f"  - 우편번호: {item.get('requesterZipCode')}")

            print(f"\n[반품 사유]")
            print(f"  - 카테고리1: {item.get('cancelReasonCategory1')}")
            print(f"  - 카테고리2: {item.get('cancelReasonCategory2')}")
            print(f"  - 사유 코드: {item.get('reasonCode')}")
            print(f"  - 사유 설명: {item.get('reasonCodeText')}")
            print(f"  - 상세: {item.get('cancelReason')}")

            print(f"\n[귀책 및 환불]")
            print(f"  - 귀책 타입: {item.get('faultByType')}")
            print(f"  - 선환불: {item.get('preRefund')}")

            shipping_charge = item.get('returnShippingCharge')
            if shipping_charge:
                units = shipping_charge.get('units', 0)
                nanos = shipping_charge.get('nanos', 0)
                charge = float(units) + (float(nanos) / 1_000_000_000)
                currency = shipping_charge.get('currencyCode')
                charge_type = "셀러 부담" if charge > 0 else "고객 부담"
                print(f"  - 반품 배송비: {charge:,.0f} {currency} ({charge_type})")

            print(f"\n[배송 정보]")
            print(f"  - 반품 배송 번호: {item.get('returnDeliveryId')}")
            print(f"  - 회수 종류: {item.get('returnDeliveryType')}")
            print(f"  - 출고중지 상태: {item.get('releaseStopStatus')}")

            delivery_dtos = item.get('returnDeliveryDtos', [])
            if delivery_dtos:
                print(f"  - 운송장 정보:")
                for dto in delivery_dtos:
                    print(f"    * {dto.get('deliveryCompanyCode')}: {dto.get('deliveryInvoiceNo')}")

            print(f"\n[반품 아이템]")
            return_items = item.get('returnItems', [])
            print(f"  - 총 {len(return_items)}개 아이템")
            for i, ret_item in enumerate(return_items, 1):
                print(f"\n  [{i}] {ret_item.get('vendorItemName')}")
                print(f"      - Vendor Item ID: {ret_item.get('vendorItemId')}")
                print(f"      - 취소 수량: {ret_item.get('cancelCount')} / {ret_item.get('purchaseCount')}")
                print(f"      - 배송번호: {ret_item.get('shipmentBoxId')}")
                print(f"      - 출고 상태: {ret_item.get('releaseStatus')}")
                print(f"      - 담당자: {ret_item.get('cancelCompleteUser')}")

            print(f"\n[완료 확인]")
            print(f"  - 확인 타입: {item.get('completeConfirmType')}")
            print(f"  - 확인 시간: {item.get('completeConfirmDate')}")

            # JSON으로 전체 응답 저장
            output_file = f"return_detail_{receipt_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n[INFO] 전체 응답을 {output_file}에 저장했습니다.")

        else:
            print(f"[ERROR] 응답 데이터가 없습니다.")

    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    test_single_return_fetch()
