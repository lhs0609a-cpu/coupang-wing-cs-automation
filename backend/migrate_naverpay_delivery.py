"""
NaverPay 배송 추적 테이블 마이그레이션 스크립트
"""
import sqlite3
import os
from datetime import datetime

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(__file__), "app", "coupang_cs.db")

def migrate():
    """마이그레이션 실행"""
    print(f"[*] NaverPay Delivery Table Migration Start...")
    print(f"    DB Path: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. naverpay_deliveries 테이블 생성
        print("\n[1] Creating naverpay_deliveries table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS naverpay_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                courier TEXT NOT NULL,
                tracking_number TEXT NOT NULL,
                product_name TEXT,
                order_date TEXT,
                collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                collected_date TEXT NOT NULL
            )
        """)

        # 인덱스 생성
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tracking_date
            ON naverpay_deliveries(tracking_number, collected_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_collected_at
            ON naverpay_deliveries(collected_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_courier
            ON naverpay_deliveries(courier)
        """)
        print("    [OK] naverpay_deliveries table created")

        # 2. naverpay_delivery_history 테이블 생성
        print("\n[2] Creating naverpay_delivery_history table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS naverpay_delivery_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                courier TEXT NOT NULL,
                tracking_number TEXT NOT NULL,
                product_name TEXT,
                order_date TEXT,
                collected_at DATETIME NOT NULL,
                collected_date TEXT NOT NULL,
                archived_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                archived_date TEXT NOT NULL
            )
        """)
        print("    [OK] naverpay_delivery_history table created")

        # 3. naverpay_schedules 테이블 생성
        print("\n[3] Creating naverpay_schedules table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS naverpay_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                schedule_type TEXT NOT NULL,
                interval_minutes INTEGER,
                cron_expression TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_run_at DATETIME,
                next_run_at DATETIME
            )
        """)
        print("    [OK] naverpay_schedules table created")

        conn.commit()

        # 테이블 확인
        print("\n[*] Checking created tables:")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'naverpay%'
        """)
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"    - {table[0]}: {count} records")

        print("\n[OK] Migration completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def check_tables():
    """테이블 존재 여부 확인"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'naverpay%'
    """)
    tables = cursor.fetchall()
    conn.close()

    return [t[0] for t in tables]


if __name__ == "__main__":
    existing = check_tables()
    if existing:
        print(f"기존 테이블 발견: {existing}")
        response = input("테이블을 다시 생성하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("마이그레이션 취소됨")
            exit(0)

    migrate()
