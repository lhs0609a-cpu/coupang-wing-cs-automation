# -*- coding: utf-8 -*-
"""
로컬에서 쿠팡 반품/출고중지 데이터를 직접 조회하는 스크립트
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (모듈 import 전에!)
load_dotenv(Path("backend/.env"))

from backend.app.services.coupang_api_client import CoupangAPIClient
from backend.app.models.coupang_account import decrypt_value
from loguru import logger

# 데이터베이스 경로
DB_PATH = r"E:\u\coupang-wing-cs-automation\backend\database\coupang_cs.db"

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
        raise Exception("활성화된 쿠팡 계정이 없습니다. 계정 설정에서 쿠팡 API 키를 등록해주세요.")

    # 암호화된 값을 복호화
    access_key = decrypt_value(result[0])
    secret_key = decrypt_value(result[1])
    vendor_id = result[2]

    return access_key, secret_key, vendor_id

def fetch_and_save_returns():
    """쿠팡에서 반품 데이터를 조회하고 로컬 DB에 저장"""

    # 데이터베이스에서 계정 정보 가져오기
    print("Loading Coupang credentials from database...")
    ACCESS_KEY, SECRET_KEY, VENDOR_ID = get_coupang_credentials()
    print(f"Using account: Vendor ID = {VENDOR_ID}")

    # API 클라이언트 초기화
    client = CoupangAPIClient(
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        vendor_id=VENDOR_ID
    )

    # 데이터베이스 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total_fetched = 0
    total_saved = 0
    total_updated = 0

    # 최근 90일간 데이터를 3일 단위로 조회
    batch_days = 3

    print(f"Starting to fetch returns from Coupang...")
    print(f"Period: Last 90 days (in {batch_days}-day batches)")
    print("="*60)

    for i in range(0, 90, batch_days):
        end_date = datetime.now() - timedelta(days=i)
        start_date = end_date - timedelta(days=batch_days)

        start_str = start_date.strftime("%Y-%m-%dT%H:%M")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M")

        print(f"\nBatch {i//batch_days + 1}: {start_str} ~ {end_str}")

        try:
            # 쿠팡 API 호출
            result = client.get_return_requests(
                start_date=start_str,
                end_date=end_str
            )

            if not result or "data" not in result:
                print("  -> No data")
                continue

            return_data = result["data"]
            batch_count = len(return_data)
            total_fetched += batch_count

            print(f"  -> Fetched: {batch_count} items")

            # DB에 저장
            for item in return_data:
                receipt_id = item.get("receiptId")
                order_id = str(item.get("orderId"))

                return_items = item.get("returnItems", [])
                if not return_items:
                    continue

                # 수령인 정보 (API는 평면 구조로 반환)
                receiver_name = item.get("requesterName")
                receiver_phone = item.get("requesterPhoneNumber") or item.get("requesterRealPhoneNumber")
                receiver_address = item.get("requesterAddress")
                receiver_address_detail = item.get("requesterAddressDetail")
                receiver_zipcode = item.get("requesterZipCode")

                for return_item in return_items:
                    product_name = return_item.get("vendorItemPackageName", "") or return_item.get("vendorItemName", "")
                    cancel_count = return_item.get("cancelCount", 1)
                    cancel_reason_cat1 = return_item.get("cancelReasonCategory1", "")
                    cancel_reason_cat2 = return_item.get("cancelReasonCategory2", "")

                    receipt_type = item.get("receiptType", "RETURN")
                    receipt_status = item.get("receiptStatus", "")

                    # 이미 존재하는지 확인
                    cursor.execute("""
                        SELECT id FROM return_logs
                        WHERE coupang_receipt_id = ? AND coupang_order_id = ?
                    """, (receipt_id, order_id))

                    existing = cursor.fetchone()

                    if existing:
                        # 업데이트
                        cursor.execute("""
                            UPDATE return_logs
                            SET receipt_status = ?,
                                receiver_name = ?,
                                receiver_phone = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (receipt_status, receiver_name, receiver_phone, existing[0]))
                        total_updated += 1
                    else:
                        # 신규 삽입
                        cursor.execute("""
                            INSERT INTO return_logs (
                                coupang_receipt_id,
                                coupang_order_id,
                                product_name,
                                receiver_name,
                                receiver_phone,
                                receipt_type,
                                receipt_status,
                                cancel_count,
                                cancel_reason_category1,
                                cancel_reason_category2,
                                naver_processed,
                                status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            receipt_id, order_id, product_name,
                            receiver_name, receiver_phone,
                            receipt_type, receipt_status,
                            cancel_count, cancel_reason_cat1, cancel_reason_cat2,
                            False, "pending"
                        ))
                        total_saved += 1

            conn.commit()

        except Exception as e:
            print(f"  -> Error: {str(e)}")
            continue

    # 최종 통계
    print("\n" + "="*60)
    print(f"SUMMARY:")
    print(f"  Total fetched: {total_fetched}")
    print(f"  Newly saved: {total_saved}")
    print(f"  Updated: {total_updated}")

    # DB 통계
    cursor.execute("SELECT COUNT(*) FROM return_logs")
    total_in_db = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM return_logs WHERE receipt_status LIKE '%RELEASE_STOP%'")
    release_stop_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM return_logs WHERE receipt_status LIKE '%RETURN%'")
    return_count = cursor.fetchone()[0]

    print(f"\nDatabase totals:")
    print(f"  Total return logs: {total_in_db}")
    print(f"  Release stop requests: {release_stop_count}")
    print(f"  Return requests: {return_count}")

    conn.close()

if __name__ == "__main__":
    fetch_and_save_returns()
