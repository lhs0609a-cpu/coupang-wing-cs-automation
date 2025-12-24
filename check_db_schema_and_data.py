"""
데이터베이스 스키마 및 데이터 확인
"""
import sys
import os
sys.path.append('backend')

# UTF-8 출력 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import sqlite3

db_path = "backend/coupang_cs.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*80)
print("데이터베이스 스키마 및 데이터 확인")
print("="*80)

# 테이블 목록
print("\n[테이블 목록]")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

# 각 테이블의 스키마와 데이터 개수
for table in tables:
    table_name = table[0]
    print(f"\n\n{'='*80}")
    print(f"테이블: {table_name}")
    print('='*80)

    # 스키마
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print("\n[컬럼 정보]")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - NULL허용: {not col[3]}, 기본값: {col[4]}, PK: {col[5]}")

    # 데이터 개수
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\n[데이터 개수] {count}개")

    # 샘플 데이터 (최대 3개)
    if count > 0:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        print("\n[샘플 데이터]")
        for idx, row in enumerate(rows, 1):
            print(f"\n  #{idx}")
            for col_idx, col in enumerate(columns):
                value = row[col_idx]
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"    {col[1]}: {value}")

conn.close()

print("\n" + "="*80)
