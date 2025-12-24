# -*- coding: utf-8 -*-
"""
쿠팡 반품 API 테스트 스크립트
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(Path("backend/.env"))

from backend.app.services.coupang_api_client import CoupangAPIClient
from backend.app.models.coupang_account import decrypt_value
import json

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

# 계정 정보 가져오기
print("=" * 60)
print("쿠팡 반품 API 테스트")
print("=" * 60)

try:
    ACCESS_KEY, SECRET_KEY, VENDOR_ID = get_coupang_credentials()
    print(f"✓ 계정 정보 로드 완료:")
    print(f"  Vendor ID: {VENDOR_ID}")
    print(f"  Access Key: {ACCESS_KEY[:20]}... (길이: {len(ACCESS_KEY)})")
    print(f"  Secret Key: {SECRET_KEY[:20]}... (길이: {len(SECRET_KEY)})\n")
except Exception as e:
    print(f"✗ 계정 정보 로드 실패: {str(e)}")
    sys.exit(1)

# API 클라이언트 초기화
client = CoupangAPIClient(
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    vendor_id=VENDOR_ID
)

# 최근 7일간 데이터 조회 테스트
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

start_str = start_date.strftime("%Y-%m-%dT%H:%M")
end_str = end_date.strftime("%Y-%m-%dT%H:%M")

print(f"테스트 기간: {start_str} ~ {end_str}\n")

# 1. 전체 반품/취소 조회
print("1. 전체 반품/취소 조회 (cancelType 미지정)")
print("-" * 60)
try:
    result = client.get_return_requests(
        start_date=start_str,
        end_date=end_str
    )

    if result and "data" in result:
        count = len(result["data"])
        print(f"✓ 성공: {count}건 조회됨")

        if count > 0:
            print(f"\n첫 번째 항목 예시:")
            first_item = result["data"][0]
            print(f"  - receiptId: {first_item.get('receiptId')}")
            print(f"  - orderId: {first_item.get('orderId')}")
            print(f"  - receiptType: {first_item.get('receiptType')}")
            print(f"  - receiptStatus: {first_item.get('receiptStatus')}")

        # 응답 구조 확인
        print(f"\n응답 구조:")
        print(f"  - code: {result.get('code')}")
        print(f"  - message: {result.get('message')}")
        print(f"  - data 배열 크기: {count}")

        # 페이지네이션 관련 필드 확인
        pagination_fields = ['nextToken', 'hasMore', 'totalCount', 'pageNum', 'totalPages']
        found_pagination = []
        for field in pagination_fields:
            if field in result:
                found_pagination.append(f"{field}: {result[field]}")

        if found_pagination:
            print(f"  - 페이지네이션 필드: {', '.join(found_pagination)}")
        else:
            print(f"  - 페이지네이션 필드 없음")
    else:
        print("✗ 응답에 data 필드 없음")
        print(f"응답: {json.dumps(result, ensure_ascii=False, indent=2)}")

except Exception as e:
    print(f"✗ 실패: {str(e)}")

print("\n")

# 2. 반품만 조회 (cancelType=RETURN)
print("2. 반품만 조회 (cancelType=RETURN)")
print("-" * 60)
try:
    result = client.get_return_requests(
        start_date=start_str,
        end_date=end_str,
        cancel_type="RETURN"
    )

    if result and "data" in result:
        count = len(result["data"])
        print(f"✓ 성공: {count}건 조회됨")

        # 상태별 통계
        status_counts = {}
        for item in result["data"]:
            status = item.get("receiptStatus", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        if status_counts:
            print(f"\n상태별 분포:")
            for status, count in status_counts.items():
                print(f"  - {status}: {count}건")
    else:
        print("✗ 응답에 data 필드 없음")

except Exception as e:
    print(f"✗ 실패: {str(e)}")

print("\n")

# 3. 출고중지 요청만 조회 (status=RU)
print("3. 출고중지 요청만 조회 (cancelType=RETURN, status=RU)")
print("-" * 60)
try:
    result = client.get_return_requests(
        start_date=start_str,
        end_date=end_str,
        cancel_type="RETURN",
        status="RU"
    )

    if result and "data" in result:
        count = len(result["data"])
        print(f"✓ 성공: {count}건 조회됨")

        if count > 0:
            print(f"\n출고중지 요청 상세:")
            for item in result["data"][:5]:  # 최대 5개만 표시
                print(f"  - 접수번호: {item.get('receiptId')}, 주문번호: {item.get('orderId')}, 상태: {item.get('receiptStatus')}")
    else:
        print("✗ 응답에 data 필드 없음")

except Exception as e:
    print(f"✗ 실패: {str(e)}")

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)
