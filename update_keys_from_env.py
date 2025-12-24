# -*- coding: utf-8 -*-
"""
.env 파일에서 쿠팡 API 키를 읽어서 DB에 저장
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (모듈 import 전에!)
load_dotenv(Path("backend/.env"))

from backend.app.models.coupang_account import encrypt_value, decrypt_value

DB_PATH = r"backend\database\coupang_cs.db"

print("=" * 80)
print(".env 파일에서 쿠팡 API 키 업데이트")
print("=" * 80)

# .env에서 키 읽기
ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY")
SECRET_KEY = os.getenv("COUPANG_SECRET_KEY")
VENDOR_ID = os.getenv("COUPANG_VENDOR_ID")

if not ACCESS_KEY or not SECRET_KEY or not VENDOR_ID:
    print("\n❌ backend/.env 파일에 COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY, COUPANG_VENDOR_ID가 설정되지 않았습니다.")
    sys.exit(1)

print(f"\n.env에서 읽은 정보:")
print(f"  Vendor ID: {VENDOR_ID}")
print(f"  Access Key: {ACCESS_KEY[:8]}... (길이: {len(ACCESS_KEY)})")
print(f"  Secret Key: {SECRET_KEY[:8]}... (길이: {len(SECRET_KEY)})")

# 암호화
print("\n암호화 중...")
access_key_enc = encrypt_value(ACCESS_KEY)
secret_key_enc = encrypt_value(SECRET_KEY)

print(f"암호화된 Access Key: {access_key_enc[:50]}...")
print(f"암호화된 Secret Key: {secret_key_enc[:50]}...")

# DB 업데이트
print("\nDB 업데이트 중...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 계정이 있는지 확인
cursor.execute("SELECT id FROM coupang_accounts WHERE vendor_id = ?", (VENDOR_ID,))
existing = cursor.fetchone()

if existing:
    # 업데이트
    cursor.execute("""
        UPDATE coupang_accounts
        SET access_key_encrypted = ?,
            secret_key_encrypted = ?,
            is_active = 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE vendor_id = ?
    """, (access_key_enc, secret_key_enc, VENDOR_ID))
    print(f"✓ 기존 계정 업데이트됨 (ID: {existing[0]})")
else:
    # 신규 삽입
    cursor.execute("""
        INSERT INTO coupang_accounts (
            name, vendor_id, access_key_encrypted, secret_key_encrypted, is_active
        ) VALUES (?, ?, ?, ?, ?)
    """, ("쿠팡 계정", VENDOR_ID, access_key_enc, secret_key_enc, 1))
    print(f"✓ 새 계정 생성됨")

conn.commit()

# 확인
cursor.execute("""
    SELECT id, name, vendor_id, access_key_encrypted, secret_key_encrypted
    FROM coupang_accounts
    WHERE vendor_id = ?
""", (VENDOR_ID,))

result = cursor.fetchone()
if result:
    account_id, name, vendor_id, access_enc, secret_enc = result

    access_key_check = decrypt_value(access_enc)
    secret_key_check = decrypt_value(secret_enc)

    print(f"\n업데이트 확인:")
    print(f"  계정 ID: {account_id}")
    print(f"  계정 이름: {name}")
    print(f"  Vendor ID: {vendor_id}")
    print(f"  Access Key: {access_key_check[:8]}... (길이: {len(access_key_check)})")
    print(f"  Secret Key: {secret_key_check[:8]}... (길이: {len(secret_key_check)})")

    if access_key_check == ACCESS_KEY and secret_key_check == SECRET_KEY:
        print("\n✅ 검증 성공: API 키가 올바르게 저장되었습니다!")
    else:
        print("\n❌ 검증 실패: 저장된 키가 일치하지 않습니다")

conn.close()

print("\n" + "=" * 80)
print("완료! 이제 API를 통해 데이터를 수집할 수 있습니다.")
print("=" * 80)
