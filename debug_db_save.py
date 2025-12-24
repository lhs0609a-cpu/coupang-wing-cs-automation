# -*- coding: utf-8 -*-
"""
DB 저장 디버깅
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
load_dotenv(backend_env)

DB_PATH = r"backend\database\coupang_cs.db"

print("=" * 80)
print("DB 저장 디버깅")
print("=" * 80)

# 환경 변수
ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY", "")
SECRET_KEY = os.getenv("COUPANG_SECRET_KEY", "")
VENDOR_ID = os.getenv("COUPANG_VENDOR_ID", "")

print(f"\n.env 파일:")
print(f"  ACCESS_KEY: {ACCESS_KEY}")
print(f"  SECRET_KEY: {SECRET_KEY}")
print(f"  VENDOR_ID: {VENDOR_ID}")

# 암호화
access_key_enc = encrypt_value(ACCESS_KEY)
secret_key_enc = encrypt_value(SECRET_KEY)

print(f"\n암호화:")
print(f"  access_key_enc: {access_key_enc[:80]}...")
print(f"  secret_key_enc: {secret_key_enc[:80]}...")

# DB 연결
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 기존 데이터 확인
print(f"\n[BEFORE] DB 상태:")
cursor.execute("SELECT id, vendor_id, access_key_encrypted, secret_key_encrypted FROM coupang_accounts WHERE id = 1")
before = cursor.fetchone()
if before:
    print(f"  ID: {before[0]}")
    print(f"  vendor_id: {before[1]}")
    print(f"  access_key_encrypted: {before[2][:80]}...")
    print(f"  secret_key_encrypted: {before[3][:80]}...")
    print(f"  복호화된 access_key: '{decrypt_value(before[2])}' (길이: {len(decrypt_value(before[2]))})")
    print(f"  복호화된 secret_key: '{decrypt_value(before[3])}' (길이: {len(decrypt_value(before[3]))})")
else:
    print("  레코드 없음")

# UPDATE 실행
print(f"\n[UPDATE] 실행 중...")
cursor.execute("""
    UPDATE coupang_accounts
    SET access_key_encrypted = ?,
        secret_key_encrypted = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
""", (access_key_enc, secret_key_enc))

print(f"  영향받은 행: {cursor.rowcount}")

# COMMIT
conn.commit()
print(f"  COMMIT 완료")

# 확인
print(f"\n[AFTER] DB 상태:")
cursor.execute("SELECT id, vendor_id, access_key_encrypted, secret_key_encrypted FROM coupang_accounts WHERE id = 1")
after = cursor.fetchone()
if after:
    print(f"  ID: {after[0]}")
    print(f"  vendor_id: {after[1]}")
    print(f"  access_key_encrypted: {after[2][:80]}...")
    print(f"  secret_key_encrypted: {after[3][:80]}...")
    print(f"  복호화된 access_key: '{decrypt_value(after[2])}' (길이: {len(decrypt_value(after[2]))})")
    print(f"  복호화된 secret_key: '{decrypt_value(after[3])}' (길이: {len(decrypt_value(after[3]))})")
else:
    print("  레코드 없음")

conn.close()

print("\n" + "=" * 80)
