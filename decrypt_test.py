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

cursor.execute("""
    SELECT id, name, vendor_id, access_key_encrypted, secret_key_encrypted
    FROM coupang_accounts
    WHERE id = 1
""")

result = cursor.fetchone()

if result:
    account_id, name, vendor_id, access_enc, secret_enc = result

    print("=" * 80)
    print("쿠팡 계정 복호화 테스트")
    print("=" * 80)
    print(f"\nID: {account_id}")
    print(f"이름: {name}")
    print(f"Vendor ID: {vendor_id}")

    print(f"\n암호화된 Access Key:")
    print(f"  {access_enc[:50]}...")

    print(f"\n암호화된 Secret Key:")
    print(f"  {secret_enc[:50]}...")

    try:
        access_key = decrypt_value(access_enc)
        secret_key = decrypt_value(secret_enc)

        print(f"\n복호화 결과:")
        print(f"  Access Key: '{access_key}' (길이: {len(access_key)})")
        print(f"  Secret Key: '{secret_key}' (길이: {len(secret_key)})")

        if len(access_key) == 0:
            print("\n⚠️  Access Key가 비어있습니다!")
        if len(secret_key) == 0:
            print("⚠️  Secret Key가 비어있습니다!")

    except Exception as e:
        print(f"\n복호화 실패: {str(e)}")

print("\n" + "=" * 80)
conn.close()
