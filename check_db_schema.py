# -*- coding: utf-8 -*-
import sqlite3
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = r"backend\database\coupang_cs.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 80)
print("데이터베이스 스키마 정보")
print("=" * 80)

# 테이블 목록
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\n테이블 목록:")
for table in tables:
    print(f"  - {table[0]}")

# 계정 관련 테이블 상세 정보
print("\n" + "=" * 80)

# account_sets 테이블 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%account%'")
account_tables = cursor.fetchall()

for table_name in account_tables:
    table_name = table_name[0]
    print(f"\n[{table_name}] 테이블 스키마:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # 데이터 확인
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  → 데이터 {count}건")

    if count > 0 and count < 10:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        print(f"\n  데이터:")
        for row in rows:
            print(f"    {row}")

print("\n" + "=" * 80)
conn.close()
