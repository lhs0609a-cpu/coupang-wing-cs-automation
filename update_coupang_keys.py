# -*- coding: utf-8 -*-
"""
쿠팡 API 키 업데이트 스크립트
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
from backend.app.models.coupang_account import encrypt_value

DB_PATH = r"backend\database\coupang_cs.db"

print("=" * 80)
print("쿠팡 API 키 업데이트")
print("=" * 80)

# 사용자 입력
print("\n올바른 쿠팡 API 키를 입력해주세요:")
print("(현재 DB에 저장된 키는 비어있습니다)\n")

ACCESS_KEY = input("Access Key: ").strip()
SECRET_KEY = input("Secret Key: ").strip()

if not ACCESS_KEY or not SECRET_KEY:
    print("\n❌ Access Key와 Secret Key를 모두 입력해야 합니다.")
    sys.exit(1)

# 확인
print(f"\n입력한 정보:")
print(f"  Access Key: {ACCESS_KEY[:8]}... (길이: {len(ACCESS_KEY)})")
print(f"  Secret Key: {SECRET_KEY[:8]}... (길이: {len(SECRET_KEY)})")

confirm = input("\n이 정보로 업데이트하시겠습니까? (y/N): ").strip().lower()

if confirm != 'y':
    print("취소되었습니다.")
    sys.exit(0)

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

cursor.execute("""
    UPDATE coupang_accounts
    SET access_key_encrypted = ?,
        secret_key_encrypted = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
""", (access_key_enc, secret_key_enc))

conn.commit()

if cursor.rowcount > 0:
    print(f"✓ 성공: {cursor.rowcount}개 계정 업데이트됨")
else:
    print("❌ 업데이트 실패: 계정을 찾을 수 없습니다")

# 확인
from backend.app.models.coupang_account import decrypt_value

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

    print(f"\n업데이트 확인:")
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
print("다음 명령어로 데이터 수집을 시작하세요:")
print("  venv/Scripts/python.exe fetch_returns_local.py")
print("=" * 80)
