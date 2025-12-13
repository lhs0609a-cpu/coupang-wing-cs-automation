"""
Add receiver_name and receiver_phone columns to return_logs table
"""
import sqlite3
import os
from loguru import logger

def migrate():
    # Fly.io에서는 /data/coupang_cs.db, 로컬에서는 ./database/coupang_cs.db
    db_paths = [
        "/data/coupang_cs.db",
        "./database/coupang_cs.db",
        "database/coupang_cs.db"
    ]

    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        logger.error("Database file not found!")
        return False

    logger.info(f"Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(return_logs)")
        columns = [row[1] for row in cursor.fetchall()]

        logger.info(f"Existing columns: {columns}")

        if "receiver_name" not in columns:
            logger.info("Adding receiver_name column...")
            cursor.execute("ALTER TABLE return_logs ADD COLUMN receiver_name TEXT")
            logger.success("receiver_name column added!")
        else:
            logger.info("receiver_name column already exists")

        if "receiver_phone" not in columns:
            logger.info("Adding receiver_phone column...")
            cursor.execute("ALTER TABLE return_logs ADD COLUMN receiver_phone TEXT")
            logger.success("receiver_phone column added!")
        else:
            logger.info("receiver_phone column already exists")

        conn.commit()
        logger.success("Migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
