# -*- coding: utf-8 -*-
"""
.env 파일의 쿠팡 API 키를 DB에 저장
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv
from backend.app.models.coupang_account import encrypt_value, decrypt_value

# backend/.env 파일 로드
backend_env = Path("backend/.env")
if backend_env.exists():
    load_dotenv(backend_env)
    print(f"✓ {backend_env} 파일 로드")
else:
    print(f"✗ {backend_env} 파일을 찾을 수 없습니다")
    sys.exit(1)

DB_PATH = r"backend\database\coupang_cs.db"

print("=" * 80)
print("쿠팡 API 키 저장 (.env → DB)")
print("=" * 80)

# 환경 변수에서 가져오기
ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY", "")
SECRET_KEY = os.getenv("COUPANG_SECRET_KEY", "")
VENDOR_ID = os.getenv("COUPANG_VENDOR_ID", "")

print(f"\n.env 파일에서 읽은 값:")
print(f"  ACCESS_KEY: {ACCESS_KEY[:20]}... (길이: {len(ACCESS_KEY)})")
print(f"  SECRET_KEY: {SECRET_KEY[:20]}... (길이: {len(SECRET_KEY)})")
print(f"  VENDOR_ID: {VENDOR_ID}")

if not ACCESS_KEY or not SECRET_KEY or not VENDOR_ID:
    print("\n❌ .env 파일에 필수 정보가 없습니다.")
    sys.exit(1)

# 암호화
print("\n암호화 중...")
access_key_enc = encrypt_value(ACCESS_KEY)
secret_key_enc = encrypt_value(SECRET_KEY)

# DB 업데이트
print("DB 업데이트 중...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 기존 계정 업데이트
cursor.execute("""
    UPDATE coupang_accounts
    SET vendor_id = ?,
        access_key_encrypted = ?,
        secret_key_encrypted = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
""", (VENDOR_ID, access_key_enc, secret_key_enc))

if cursor.rowcount > 0:
    print(f"✓ 기존 계정 업데이트 완료")
else:
    # 계정이 없으면 새로 생성
    print("기존 계정이 없어서 새로 생성합니다...")
    cursor.execute("""
        INSERT INTO coupang_accounts (
            name, vendor_id, access_key_encrypted, secret_key_encrypted,
            wing_username, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (
        "쿠팡 Wing 계정",
        VENDOR_ID,
        access_key_enc,
        secret_key_enc,
        "lhs0609",
        True
    ))
    print(f"✓ 새 계정 생성 완료")

conn.commit()

# 검증
print("\n검증 중...")
cursor.execute("""
    SELECT id, name, vendor_id, access_key_encrypted, secret_key_encrypted, wing_username
    FROM coupang_accounts
    WHERE id = 1
""")

result = cursor.fetchone()
if result:
    account_id, name, vendor_id, access_enc, secret_enc, wing_username = result

    access_key_check = decrypt_value(access_enc)
    secret_key_check = decrypt_value(secret_enc)

    print(f"\n✅ DB 저장 성공!")
    print(f"  ID: {account_id}")
    print(f"  이름: {name}")
    print(f"  Vendor ID: {vendor_id}")
    print(f"  Wing Username: {wing_username}")
    print(f"  Access Key: {access_key_check[:20]}... (길이: {len(access_key_check)})")
    print(f"  Secret Key: {secret_key_check[:20]}... (길이: {len(secret_key_check)})")

    if access_key_check == ACCESS_KEY and secret_key_check == SECRET_KEY:
        print("\n✅ 검증 성공: API 키가 올바르게 저장되었습니다!")
    else:
        print("\n❌ 검증 실패: 저장된 키가 일치하지 않습니다")
        print(f"예상 Access Key: {ACCESS_KEY[:20]}...")
        print(f"저장된 Access Key: {access_key_check[:20]}...")

conn.close()

print("\n" + "=" * 80)
print("✅ 완료!")
print("=" * 80)
