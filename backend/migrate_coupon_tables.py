"""
쿠폰 자동연동 관련 테이블 생성 마이그레이션 스크립트
"""
import sqlite3
import os

def migrate():
    # 데이터베이스 경로
    db_path = os.path.join(os.path.dirname(__file__), "app", "coupang_wing.db")

    # Fly.io에서는 /data/coupang_wing.db 경로 사용
    if not os.path.exists(db_path):
        db_path = "/data/coupang_wing.db"

    if not os.path.exists(db_path):
        print(f"데이터베이스를 찾을 수 없습니다: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. CouponAutoSyncConfig 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coupon_auto_sync_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupang_account_id INTEGER NOT NULL,
                is_enabled BOOLEAN DEFAULT 0,
                instant_coupon_enabled BOOLEAN DEFAULT 0,
                instant_coupon_id INTEGER,
                instant_coupon_name VARCHAR(200),
                download_coupon_enabled BOOLEAN DEFAULT 0,
                download_coupon_id INTEGER,
                download_coupon_name VARCHAR(200),
                apply_delay_days INTEGER DEFAULT 1,
                contract_id INTEGER,
                excluded_categories TEXT,
                excluded_product_ids TEXT,
                last_sync_at DATETIME,
                last_checked_product_date VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupang_account_id) REFERENCES coupang_accounts(id)
            )
        """)
        print("✅ coupon_auto_sync_configs 테이블 생성 완료")

        # 2. ProductCouponTracking 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_coupon_trackings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupang_account_id INTEGER NOT NULL,
                seller_product_id INTEGER NOT NULL,
                seller_product_name VARCHAR(500),
                product_created_at DATETIME NOT NULL,
                coupon_apply_scheduled_at DATETIME NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                instant_coupon_applied BOOLEAN DEFAULT 0,
                instant_coupon_applied_at DATETIME,
                instant_coupon_request_id VARCHAR(100),
                download_coupon_applied BOOLEAN DEFAULT 0,
                download_coupon_applied_at DATETIME,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupang_account_id) REFERENCES coupang_accounts(id)
            )
        """)
        print("✅ product_coupon_trackings 테이블 생성 완료")

        # 인덱스 생성
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_product_coupon_trackings_seller_product_id
            ON product_coupon_trackings(seller_product_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_product_coupon_trackings_status
            ON product_coupon_trackings(status)
        """)

        # 3. BulkApplyProgress 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bulk_apply_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupang_account_id INTEGER NOT NULL,
                status VARCHAR(50) DEFAULT 'collecting',
                total_days INTEGER DEFAULT 0,
                processed_days INTEGER DEFAULT 0,
                current_date VARCHAR(20),
                total_products INTEGER DEFAULT 0,
                total_items INTEGER DEFAULT 0,
                instant_total INTEGER DEFAULT 0,
                instant_success INTEGER DEFAULT 0,
                instant_failed INTEGER DEFAULT 0,
                download_total INTEGER DEFAULT 0,
                download_success INTEGER DEFAULT 0,
                download_failed INTEGER DEFAULT 0,
                error_message TEXT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (coupang_account_id) REFERENCES coupang_accounts(id)
            )
        """)
        print("✅ bulk_apply_progress 테이블 생성 완료")

        # 인덱스 생성
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_bulk_apply_progress_coupang_account_id
            ON bulk_apply_progress(coupang_account_id)
        """)

        # 4. CouponApplyLog 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coupon_apply_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupang_account_id INTEGER NOT NULL,
                seller_product_id INTEGER NOT NULL,
                vendor_item_id INTEGER,
                coupon_type VARCHAR(50) NOT NULL,
                coupon_id INTEGER NOT NULL,
                coupon_name VARCHAR(200),
                success BOOLEAN DEFAULT 0,
                request_id VARCHAR(100),
                error_code VARCHAR(50),
                error_message TEXT,
                request_data TEXT,
                response_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupang_account_id) REFERENCES coupang_accounts(id)
            )
        """)
        print("✅ coupon_apply_logs 테이블 생성 완료")

        conn.commit()
        print("\n✅ 모든 쿠폰 관련 테이블이 성공적으로 생성되었습니다.")
        return True

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
