"""
반품 데이터 통계 조회
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.models.return_log import ReturnLog
from sqlalchemy import func


def check_return_statistics():
    """반품 데이터 통계 확인"""
    print("=" * 80)
    print("쿠팡 반품 데이터 통계")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 전체 개수
        total_count = db.query(ReturnLog).count()
        print(f"\n[전체 데이터]")
        print(f"  총 {total_count:,}건")

        if total_count == 0:
            print("\n[INFO] 저장된 데이터가 없습니다.")
            print("먼저 반품 데이터를 수집해주세요:")
            print("  - 자동 수집: POST /api/returns/automation/run-collector")
            print("  - 수동 수집: GET /api/returns/fetch-from-coupang")
            return

        # 상태별 개수
        print(f"\n[상태별 통계]")
        status_counts = db.query(
            ReturnLog.receipt_status,
            func.count(ReturnLog.id)
        ).group_by(ReturnLog.receipt_status).all()

        status_names = {
            "RELEASE_STOP_UNCHECKED": "출고중지요청",
            "RETURNS_UNCHECKED": "반품접수",
            "VENDOR_WAREHOUSE_CONFIRM": "입고완료",
            "REQUEST_COUPANG_CHECK": "쿠팡확인요청",
            "RETURNS_COMPLETED": "반품완료"
        }

        for status, count in sorted(status_counts, key=lambda x: x[1], reverse=True):
            status_name = status_names.get(status, status)
            percentage = (count / total_count * 100) if total_count > 0 else 0
            print(f"  - {status_name} ({status}): {count:,}건 ({percentage:.1f}%)")

        # 타입별 개수
        print(f"\n[타입별 통계]")
        type_counts = db.query(
            ReturnLog.receipt_type,
            func.count(ReturnLog.id)
        ).group_by(ReturnLog.receipt_type).all()

        for receipt_type, count in type_counts:
            type_name = "반품" if receipt_type == "RETURN" else "취소" if receipt_type == "CANCEL" else receipt_type
            percentage = (count / total_count * 100) if total_count > 0 else 0
            print(f"  - {type_name} ({receipt_type}): {count:,}건 ({percentage:.1f}%)")

        # 귀책별 개수
        print(f"\n[귀책별 통계]")
        fault_counts = db.query(
            ReturnLog.fault_by_type,
            func.count(ReturnLog.id)
        ).filter(ReturnLog.fault_by_type.isnot(None)).group_by(ReturnLog.fault_by_type).all()

        fault_names = {
            "CUSTOMER": "고객 과실",
            "VENDOR": "셀러 과실",
            "COUPANG": "쿠팡 과실",
            "WMS": "물류 과실",
            "GENERAL": "일반"
        }

        if fault_counts:
            for fault, count in sorted(fault_counts, key=lambda x: x[1], reverse=True):
                fault_name = fault_names.get(fault, fault)
                percentage = (count / total_count * 100) if total_count > 0 else 0
                print(f"  - {fault_name} ({fault}): {count:,}건 ({percentage:.1f}%)")
        else:
            print(f"  - 귀책 정보 없음")

        # 처리 상태별 개수
        print(f"\n[처리 상태별 통계]")
        process_counts = db.query(
            ReturnLog.status,
            func.count(ReturnLog.id)
        ).group_by(ReturnLog.status).all()

        process_names = {
            "pending": "대기",
            "processing": "처리중",
            "completed": "완료",
            "failed": "실패",
            "skipped": "스킵"
        }

        for status, count in sorted(process_counts, key=lambda x: x[1], reverse=True):
            status_name = process_names.get(status, status)
            percentage = (count / total_count * 100) if total_count > 0 else 0
            print(f"  - {status_name} ({status}): {count:,}건 ({percentage:.1f}%)")

        # 네이버 처리 여부
        print(f"\n[네이버 처리 여부]")
        naver_processed = db.query(ReturnLog).filter(ReturnLog.naver_processed == True).count()
        naver_pending = db.query(ReturnLog).filter(ReturnLog.naver_processed == False).count()

        print(f"  - 처리 완료: {naver_processed:,}건 ({naver_processed/total_count*100:.1f}%)")
        print(f"  - 처리 대기: {naver_pending:,}건 ({naver_pending/total_count*100:.1f}%)")

        # 반품 사유 TOP 5
        print(f"\n[반품 사유 TOP 5]")
        reason_counts = db.query(
            ReturnLog.reason_code,
            ReturnLog.reason_code_text,
            func.count(ReturnLog.id)
        ).filter(
            ReturnLog.reason_code.isnot(None)
        ).group_by(
            ReturnLog.reason_code,
            ReturnLog.reason_code_text
        ).order_by(
            func.count(ReturnLog.id).desc()
        ).limit(5).all()

        if reason_counts:
            for i, (code, text, count) in enumerate(reason_counts, 1):
                percentage = (count / total_count * 100) if total_count > 0 else 0
                print(f"  {i}. [{code}] {text}: {count:,}건 ({percentage:.1f}%)")
        else:
            print(f"  - 사유 코드 정보 없음")

        # 최근 데이터
        print(f"\n[최근 데이터 5건]")
        recent_logs = db.query(ReturnLog).order_by(ReturnLog.created_at.desc()).limit(5).all()

        for i, log in enumerate(recent_logs, 1):
            status_name = status_names.get(log.receipt_status, log.receipt_status)
            print(f"  {i}. Receipt #{log.coupang_receipt_id} - {log.product_name[:40]}...")
            print(f"     상태: {status_name}, 생성: {log.created_at.strftime('%Y-%m-%d %H:%M')}")

    except Exception as e:
        print(f"\n[ERROR] 통계 조회 실패: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_return_statistics()
