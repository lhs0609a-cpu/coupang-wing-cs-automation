"""
NaverPay Schedule History 테이블 마이그레이션 스크립트
"""
import sqlite3
import os

# DB 경로 설정
DB_PATHS = [
    "/data/coupang_cs.db",  # Fly.io 배포 환경
    os.path.join(os.path.dirname(__file__), "coupang_cs.db"),  # 로컬 환경
    os.path.join(os.path.dirname(__file__), "..", "database", "coupang_cs.db"),
]

def get_db_path():
    """사용 가능한 DB 경로 찾기"""
    for path in DB_PATHS:
        if os.path.exists(path):
            return path
    # 새로 생성할 경로
    return DB_PATHS[1] if not os.path.exists("/data") else DB_PATHS[0]

def migrate():
    db_path = get_db_path()
    print(f"Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # NaverPay Schedule History 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS naverpay_schedule_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_found INTEGER DEFAULT 0,
            new_saved INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'success',
            error_message TEXT
        )
    """)

    # 인덱스 생성
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_naverpay_history_executed_at
        ON naverpay_schedule_history(executed_at)
    """)

    # NaverPay Deliveries 테이블 (이미 있을 수 있음)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS naverpay_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient VARCHAR(100) NOT NULL,
            courier VARCHAR(50) NOT NULL,
            tracking_number VARCHAR(50) NOT NULL,
            product_name VARCHAR(500),
            order_date VARCHAR(20),
            collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            collected_date VARCHAR(10) NOT NULL
        )
    """)

    # NaverPay Schedules 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS naverpay_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id VARCHAR(50) UNIQUE NOT NULL,
            schedule_type VARCHAR(20) NOT NULL,
            interval_minutes INTEGER,
            cron_expression VARCHAR(100),
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_run_at DATETIME,
            next_run_at DATETIME
        )
    """)

    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
