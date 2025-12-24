# -*- coding: utf-8 -*-
import sqlite3
import os
import sys

# UTF-8 출력 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db_path = r"E:\u\coupang-wing-cs-automation\backend\database\coupang_cs.db"

if not os.path.exists(db_path):
    print(f"Database file not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Total count
cursor.execute("SELECT COUNT(*) FROM return_logs")
total = cursor.fetchone()[0]
print(f"Total return logs: {total}")

# By status
cursor.execute("SELECT receipt_status, COUNT(*) FROM return_logs GROUP BY receipt_status")
print("\nBy status:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Release stop count
cursor.execute("SELECT COUNT(*) FROM return_logs WHERE receipt_status LIKE '%RELEASE_STOP%'")
release_stop_count = cursor.fetchone()[0]
print(f"\nRelease stop requests: {release_stop_count}")

# Return count
cursor.execute("SELECT COUNT(*) FROM return_logs WHERE receipt_status LIKE '%RETURN%'")
return_count = cursor.fetchone()[0]
print(f"Return requests: {return_count}")

conn.close()
