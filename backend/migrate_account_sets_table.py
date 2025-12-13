"""
계정 세트 테이블 생성 마이그레이션
"""
import sqlite3
from loguru import logger
import os

def migrate():
    """account_sets 테이블 생성"""

    # 데이터베이스 경로
    db_path = os.getenv("DATABASE_PATH", "/data/coupang_cs.db")
    if not os.path.exists("/data"):
        db_path = "./database/coupang_cs.db"

    logger.info(f"Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # account_sets 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                description VARCHAR(500),
                coupang_account_id INTEGER,
                naver_account_id INTEGER,
                is_default BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                last_used_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupang_account_id) REFERENCES coupang_accounts(id),
                FOREIGN KEY (naver_account_id) REFERENCES naver_accounts(id)
            )
        """)

        conn.commit()
        logger.success("account_sets 테이블 생성 완료!")

        # 테이블 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='account_sets'")
        result = cursor.fetchone()
        if result:
            logger.success("✅ account_sets 테이블이 존재합니다")
        else:
            logger.error("❌ account_sets 테이블 생성 실패")

    except Exception as e:
        logger.error(f"마이그레이션 오류: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
