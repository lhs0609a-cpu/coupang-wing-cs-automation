"""
개선된 반품 API 응답 파싱 테스트
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.services.auto_return_collector import AutoReturnCollector
from app.models.return_log import ReturnLog
from datetime import datetime, timedelta


def test_return_collection():
    """반품 데이터 수집 테스트"""
    print("=" * 80)
    print("반품 데이터 수집 테스트")
    print("=" * 80)

    db = SessionLocal()
    try:
        collector = AutoReturnCollector(db)

        # 자동 수집 실행
        result = collector.collect_returns(triggered_by="test")

        print(f"\n[수집 결과]")
        print(f"  - 성공 여부: {result['success']}")
        print(f"  - 메시지: {result['message']}")
        print(f"  - 총 수집: {result.get('total_fetched', 0)}건")
        print(f"  - 신규: {result.get('saved', 0)}건")
        print(f"  - 업데이트: {result.get('updated', 0)}건")

        # 최근 데이터 확인
        print(f"\n[최근 수집 데이터 5건]")
        recent_logs = db.query(ReturnLog).order_by(ReturnLog.created_at.desc()).limit(5).all()

        for i, log in enumerate(recent_logs, 1):
            print(f"\n{i}. Receipt ID: {log.coupang_receipt_id}")
            print(f"   - 상품명: {log.product_name}")
            print(f"   - 상태: {log.receipt_status}")
            print(f"   - 반품 사유 코드: {log.reason_code}")
            print(f"   - 반품 사유: {log.reason_code_text}")
            print(f"   - 귀책: {log.fault_by_type}")
            print(f"   - 반품배송비: {log.return_shipping_charge} {log.return_shipping_charge_currency}")
            print(f"   - 회수지 주소: {log.receiver_address}")
            print(f"   - 배송 타입: {log.return_delivery_type}")
            print(f"   - 운송장 정보: {log.return_delivery_dtos}")
            print(f"   - 출고중지 상태: {log.release_stop_status}")
            print(f"   - 완료 확인 타입: {log.complete_confirm_type}")
            print(f"   - 선환불: {log.pre_refund}")

        # 통계
        stats = collector.get_statistics()
        print(f"\n[전체 통계]")
        print(f"  - 전체: {stats['total']}건")
        print(f"  - 대기: {stats['pending']}건")
        print(f"  - 처리완료: {stats['processed']}건")
        print(f"  - 실패: {stats['failed']}건")
        print(f"  - 최근 24시간: {stats['recent_24h']}건")

        # 필드 확인
        if recent_logs:
            print(f"\n[새 필드 검증]")
            log = recent_logs[0]
            new_fields = [
                ("reason_code", log.reason_code),
                ("reason_code_text", log.reason_code_text),
                ("fault_by_type", log.fault_by_type),
                ("return_shipping_charge", log.return_shipping_charge),
                ("receiver_address", log.receiver_address),
                ("return_delivery_type", log.return_delivery_type),
                ("release_stop_status", log.release_stop_status),
                ("complete_confirm_type", log.complete_confirm_type),
            ]

            filled_count = sum(1 for _, value in new_fields if value is not None)
            print(f"  - 새로 추가된 주요 필드 중 채워진 필드: {filled_count}/{len(new_fields)}")

            for field_name, value in new_fields:
                status = "[OK]" if value is not None else "[EMPTY]"
                print(f"  {status} {field_name}: {value}")

        print("\n" + "=" * 80)
        print("테스트 완료!")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_return_collection()
