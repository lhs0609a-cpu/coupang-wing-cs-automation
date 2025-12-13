"""
BulkApplyProgress 테이블 생성 마이그레이션 스크립트
"""
import sqlite3
import os

def migrate():
    # 데이터베이스 경로
    db_path = os.path.join(os.path.dirname(__file__), "app", "coupang_wing.db")

    if not os.path.exists(db_path):
        print(f"데이터베이스를 찾을 수 없습니다: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # BulkApplyProgress 테이블 생성
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

        # 인덱스 생성
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_bulk_apply_progress_coupang_account_id
            ON bulk_apply_progress(coupang_account_id)
        """)

        conn.commit()
        print("✅ bulk_apply_progress 테이블이 성공적으로 생성되었습니다.")
        return True

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
