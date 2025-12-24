# -*- coding: utf-8 -*-
"""
쿠팡 API 키 직접 업데이트 (환경 변수에서 가져오기)
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
import os
from backend.app.models.coupang_account import encrypt_value, decrypt_value

DB_PATH = r"backend\database\coupang_cs.db"

print("=" * 80)
print("쿠팡 API 키 업데이트")
print("=" * 80)

# 환경 변수나 설정 파일에서 가져오기
ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY", "A00492891")
SECRET_KEY = os.getenv("COUPANG_SECRET_KEY", "")

print(f"\n현재 환경 변수:")
print(f"  COUPANG_ACCESS_KEY: {ACCESS_KEY}")
print(f"  COUPANG_SECRET_KEY: {'설정됨' if SECRET_KEY else '미설정'}")

if not SECRET_KEY:
    print("\n⚠️  SECRET_KEY가 설정되지 않았습니다.")
    print("쿠팡 Wing에서 발급받은 Secret Key를 입력해주세요.\n")
    SECRET_KEY = input("Secret Key: ").strip()

if not SECRET_KEY:
    print("\n❌ Secret Key를 입력해야 합니다.")
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
    SET access_key_encrypted = ?,
        secret_key_encrypted = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
""", (access_key_enc, secret_key_enc))

affected = cursor.rowcount

# 만약 계정이 없으면 새로 생성
if affected == 0:
    print("기존 계정이 없어서 새로 생성합니다...")
    cursor.execute("""
        INSERT INTO coupang_accounts (
            name, vendor_id, access_key_encrypted, secret_key_encrypted,
            wing_username, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (
        "반품 관리용 쿠팡 계정",
        ACCESS_KEY,
        access_key_enc,
        secret_key_enc,
        "lhs0609",
        True
    ))

conn.commit()

# 확인
cursor.execute("""
    SELECT id, name, vendor_id, access_key_encrypted, secret_key_encrypted
    FROM coupang_accounts
    WHERE id = 1
""")

result = cursor.fetchone()
if result:
    account_id, name, vendor_id, access_enc, secret_enc = result

    access_key_check = decrypt_value(access_enc)
    secret_key_check = decrypt_value(secret_enc)

    print(f"\n✅ 업데이트 성공!")
    print(f"  계정 이름: {name}")
    print(f"  Vendor ID: {vendor_id}")
    print(f"  Access Key: {access_key_check[:10]}... (길이: {len(access_key_check)})")
    print(f"  Secret Key: {secret_key_check[:10]}... (길이: {len(secret_key_check)})")

conn.close()

print("\n" + "=" * 80)
