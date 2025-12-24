# -*- coding: utf-8 -*-
"""
쿠팡 반품 API 응답 구조 확인
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import json

# .env 파일 로드
load_dotenv(Path("backend/.env"))

from backend.app.services.coupang_api_client import CoupangAPIClient
from backend.app.models.coupang_account import decrypt_value

DB_PATH = r"backend\database\coupang_cs.db"

def get_coupang_credentials():
    """데이터베이스에서 쿠팡 계정 정보 가져오기"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT access_key_encrypted, secret_key_encrypted, vendor_id
        FROM coupang_accounts
        WHERE is_active = 1
        ORDER BY last_used_at DESC
        LIMIT 1
    """)

    result = cursor.fetchone()
    conn.close()

    if not result:
        raise Exception("활성화된 쿠팡 계정이 없습니다.")

    access_key = decrypt_value(result[0])
    secret_key = decrypt_value(result[1])
    vendor_id = result[2]

    return access_key, secret_key, vendor_id

print("=" * 80)
print("쿠팡 반품 API 응답 구조 확인")
print("=" * 80)

try:
    ACCESS_KEY, SECRET_KEY, VENDOR_ID = get_coupang_credentials()
    print(f"✓ 계정 정보 로드 완료: Vendor ID = {VENDOR_ID}\n")
except Exception as e:
    print(f"✗ 계정 정보 로드 실패: {str(e)}")
    sys.exit(1)

# API 클라이언트 초기화
client = CoupangAPIClient(
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    vendor_id=VENDOR_ID
)

# 최근 1일간 데이터 조회 (타임아웃 방지)
end_date = datetime.now()
start_date = end_date - timedelta(days=1)

start_str = start_date.strftime("%Y-%m-%dT%H:%M")
end_str = end_date.strftime("%Y-%m-%dT%H:%M")

print(f"조회 기간: {start_str} ~ {end_str}\n")

try:
    result = client.get_return_requests(
        start_date=start_str,
        end_date=end_str,
        cancel_type="RETURN"
    )

    if result and "data" in result and len(result["data"]) > 0:
        print(f"✓ {len(result['data'])}건 조회됨\n")

        # 첫 번째 항목의 전체 JSON 구조 출력
        first_item = result["data"][0]
        print("=" * 80)
        print("첫 번째 반품 항목의 전체 JSON 구조:")
        print("=" * 80)
        print(json.dumps(first_item, ensure_ascii=False, indent=2))

        print("\n" + "=" * 80)
        print("주요 필드 확인:")
        print("=" * 80)

        # 수령인 관련 필드들 확인
        print(f"\n1. 기본 정보:")
        print(f"   receiptId: {first_item.get('receiptId')}")
        print(f"   orderId: {first_item.get('orderId')}")
        print(f"   receiptType: {first_item.get('receiptType')}")
        print(f"   receiptStatus: {first_item.get('receiptStatus')}")

        print(f"\n2. 수령인 정보 (여러 필드명 확인):")

        # 가능한 모든 필드명 확인
        possible_fields = [
            'requesterName', 'requesterPhoneNumber', 'requesterRealPhoneNumber',
            'shippingTo', 'receiverInfo', 'receiverName', 'receiverPhone',
            'name', 'phoneNumber', 'address', 'zipCode',
            'requesterAddress', 'requesterAddressDetail', 'requesterZipCode'
        ]

        for field in possible_fields:
            value = first_item.get(field)
            if value:
                print(f"   {field}: {value}")

        # shippingTo나 receiverInfo가 객체인 경우
        shipping_to = first_item.get('shippingTo')
        if shipping_to:
            print(f"\n3. shippingTo 객체:")
            print(json.dumps(shipping_to, ensure_ascii=False, indent=4))

        receiver_info = first_item.get('receiverInfo')
        if receiver_info:
            print(f"\n4. receiverInfo 객체:")
            print(json.dumps(receiver_info, ensure_ascii=False, indent=4))

        # returnItems 확인
        return_items = first_item.get('returnItems', [])
        if return_items:
            print(f"\n5. returnItems (첫 번째 항목):")
            print(json.dumps(return_items[0], ensure_ascii=False, indent=4))

    else:
        print("✗ 조회된 데이터 없음")

except Exception as e:
    print(f"✗ 조회 실패: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
