"""
반품 로그 테이블 필드 추가 마이그레이션
API 문서의 모든 응답 필드를 파싱하기 위한 새로운 컬럼 추가
"""
import sqlite3
import os
from datetime import datetime

DATABASE_PATH = "database/coupang_cs.db"


def migrate():
    """마이그레이션 실행"""
    print(f"[{datetime.now()}] 마이그레이션 시작: ReturnLog 테이블에 새 필드 추가")

    if not os.path.exists(DATABASE_PATH):
        print(f"[ERROR] 데이터베이스 파일이 없습니다: {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # 기존 컬럼 목록 확인
        cursor.execute("PRAGMA table_info(return_logs)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"기존 컬럼 개수: {len(existing_columns)}")

        # 추가할 컬럼 정의
        new_columns = [
            # 쿠팡 시간 정보
            ("coupang_created_at", "TIMESTAMP"),
            ("coupang_modified_at", "TIMESTAMP"),

            # 상품 정보
            ("vendor_item_package_id", "VARCHAR(100)"),
            ("vendor_item_package_name", "VARCHAR(500)"),
            ("seller_product_id", "VARCHAR(100)"),
            ("seller_product_name", "VARCHAR(500)"),
            ("cancel_count_sum", "INTEGER"),
            ("purchase_count", "INTEGER"),
            ("shipment_box_id", "VARCHAR(100)"),
            ("release_status", "VARCHAR(10)"),

            # 수령인 추가 정보
            ("receiver_real_phone", "VARCHAR(50)"),
            ("receiver_address", "VARCHAR(500)"),
            ("receiver_address_detail", "VARCHAR(500)"),
            ("receiver_zipcode", "VARCHAR(20)"),

            # 반품 상태 추가
            ("release_stop_status", "VARCHAR(50)"),

            # 반품 사유 코드
            ("reason_code", "VARCHAR(100)"),
            ("reason_code_text", "VARCHAR(500)"),

            # 귀책 및 환불 정보
            ("fault_by_type", "VARCHAR(50)"),
            ("pre_refund", "BOOLEAN"),
            ("return_shipping_charge", "DECIMAL(10, 2)"),
            ("return_shipping_charge_currency", "VARCHAR(10)"),
            ("enclose_price", "DECIMAL(10, 2)"),
            ("enclose_price_currency", "VARCHAR(10)"),

            # 배송 정보
            ("return_delivery_id", "VARCHAR(100)"),
            ("return_delivery_type", "VARCHAR(50)"),
            ("return_delivery_dtos", "JSON"),

            # 완료 확인 정보
            ("complete_confirm_type", "VARCHAR(50)"),
            ("complete_confirm_date", "TIMESTAMP"),
            ("cancel_complete_user", "VARCHAR(100)"),
        ]

        # 컬럼 추가
        added_count = 0
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE return_logs ADD COLUMN {column_name} {column_type}"
                    cursor.execute(sql)
                    print(f"[OK] 컬럼 추가: {column_name} ({column_type})")
                    added_count += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"[WARN] {column_name} 추가 실패: {e}")
            else:
                print(f"[SKIP] 컬럼 이미 존재: {column_name}")

        # 인덱스 추가
        indexes = [
            ("idx_return_logs_reason_code", "reason_code"),
            ("idx_return_logs_fault_by_type", "fault_by_type"),
        ]

        for index_name, column in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON return_logs({column})")
                print(f"[OK] 인덱스 생성: {index_name} on {column}")
            except Exception as e:
                print(f"[WARN] 인덱스 생성 실패 {index_name}: {e}")

        conn.commit()
        print(f"\n[SUCCESS] 마이그레이션 완료!")
        print(f"   - 추가된 컬럼: {added_count}개")

        # 최종 컬럼 목록 확인
        cursor.execute("PRAGMA table_info(return_logs)")
        final_columns = cursor.fetchall()
        print(f"   - 최종 컬럼 개수: {len(final_columns)}")

    except Exception as e:
        print(f"[ERROR] 마이그레이션 실패: {str(e)}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
