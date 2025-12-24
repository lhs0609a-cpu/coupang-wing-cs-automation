# -*- coding: utf-8 -*-
import sqlite3
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = r"backend\database\coupang_cs.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 전체 반품 로그
cursor.execute('SELECT COUNT(*) FROM return_logs')
total = cursor.fetchone()[0]
print(f'전체 반품 로그: {total}')

# 출고중지 요청
cursor.execute("SELECT COUNT(*) FROM return_logs WHERE receipt_status LIKE '%RELEASE_STOP%'")
release_stop = cursor.fetchone()[0]
print(f'출고중지 요청: {release_stop}')

# 상태별 통계
cursor.execute("SELECT receipt_status, COUNT(*) FROM return_logs GROUP BY receipt_status ORDER BY COUNT(*) DESC")
print('\n상태별 통계:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

# 최근 데이터 확인
cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM return_logs")
dates = cursor.fetchone()
print(f'\n데이터 기간: {dates[0]} ~ {dates[1]}')

conn.close()
