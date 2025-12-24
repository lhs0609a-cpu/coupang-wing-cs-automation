# -*- coding: utf-8 -*-
"""
출고중지 요청 데이터 확인
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3

DB_PATH = r"backend\database\coupang_cs.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 출고중지 요청 데이터 조회
cursor.execute("""
    SELECT coupang_receipt_id, coupang_order_id, product_name,
           receiver_name, receiver_phone, receipt_status, created_at
    FROM return_logs
    WHERE receipt_status LIKE '%RELEASE_STOP%'
    ORDER BY created_at DESC
""")

results = cursor.fetchall()

print("=" * 100)
print(f"출고중지 요청 데이터 (총 {len(results)}건)")
print("=" * 100)

for i, row in enumerate(results, 1):
    receipt_id, order_id, product, receiver_name, receiver_phone, status, created_at = row
    print(f"\n{i}. 접수번호: {receipt_id}")
    print(f"   주문번호: {order_id}")
    print(f"   상품명: {product}")
    print(f"   수령인: {receiver_name} / {receiver_phone}")
    print(f"   상태: {status}")
    print(f"   등록일시: {created_at}")

# 전체 통계
cursor.execute("SELECT COUNT(*) FROM return_logs")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM return_logs WHERE receipt_status LIKE '%RETURN%'")
returns = cursor.fetchone()[0]

print("\n" + "=" * 100)
print("데이터베이스 전체 통계:")
print(f"  - 전체 반품 로그: {total}건")
print(f"  - 출고중지 요청: {len(results)}건")
print(f"  - 일반 반품: {returns}건")
print("=" * 100)

conn.close()
