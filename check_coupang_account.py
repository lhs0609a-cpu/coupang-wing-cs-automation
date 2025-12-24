# -*- coding: utf-8 -*-
import sqlite3
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.app.models.coupang_account import decrypt_value

DB_PATH = r"backend\database\coupang_cs.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 쿠팡 계정 정보 확인
cursor.execute("""
    SELECT id, access_key_encrypted, secret_key_encrypted, vendor_id, is_active, created_at, last_used_at
    FROM coupang_accounts
    ORDER BY created_at DESC
""")

accounts = cursor.fetchall()

print("=" * 80)
print("쿠팡 계정 정보")
print("=" * 80)

if not accounts:
    print("등록된 쿠팡 계정이 없습니다.")
else:
    for idx, account in enumerate(accounts, 1):
        account_id, access_key_enc, secret_key_enc, vendor_id, is_active, created_at, last_used_at = account

        print(f"\n계정 {idx}:")
        print(f"  ID: {account_id}")
        print(f"  Vendor ID: {vendor_id}")
        print(f"  활성화: {'예' if is_active else '아니오'}")
        print(f"  생성일: {created_at}")
        print(f"  마지막 사용: {last_used_at}")

        try:
            access_key = decrypt_value(access_key_enc)
            secret_key = decrypt_value(secret_key_enc)

            # 키의 일부만 표시 (보안)
            print(f"  Access Key: {access_key[:8]}... (길이: {len(access_key)})")
            print(f"  Secret Key: {secret_key[:8]}... (길이: {len(secret_key)})")
        except Exception as e:
            print(f"  복호화 실패: {str(e)}")

print("\n" + "=" * 80)

conn.close()
