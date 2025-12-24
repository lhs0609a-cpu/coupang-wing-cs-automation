# -*- coding: utf-8 -*-
"""
개선된 쿠팡 반품/출고중지 데이터 수집 스크립트
- 페이지네이션 처리 (API 응답 구조 확인 후 구현)
- 1일 단위 조회 (데이터 누락 방지)
- 출고중지 요청 우선 수집
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

# .env 파일 로드
load_dotenv(Path("backend/.env"))

from backend.app.services.coupang_api_client import CoupangAPIClient
from backend.app.models.coupang_account import decrypt_value
from loguru import logger
import time

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
        raise Exception("활성화된 쿠팡 계정이 없습니다.")

    access_key = decrypt_value(result[0])
    secret_key = decrypt_value(result[1])
    vendor_id = result[2]

    if not access_key or not secret_key:
        raise Exception("쿠팡 API 키가 비어있습니다. update_coupang_keys.py를 실행하여 키를 등록하세요.")

    return access_key, secret_key, vendor_id


def save_return_to_db(cursor, item):
    """반품 데이터를 DB에 저장"""
    receipt_id = item.get("receiptId")
    order_id = str(item.get("orderId"))

    return_items = item.get("returnItems", [])
    if not return_items:
        return 0

    # 수령인 정보 (API는 평면 구조로 반환)
    receiver_name = item.get("requesterName")
    receiver_phone = item.get("requesterPhoneNumber") or item.get("requesterRealPhoneNumber")
    receiver_address = item.get("requesterAddress")
    receiver_address_detail = item.get("requesterAddressDetail")
    receiver_zipcode = item.get("requesterZipCode")

    saved_count = 0
    updated_count = 0

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
            updated_count += 1
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
            saved_count += 1

    return saved_count, updated_count


def fetch_returns_by_period(client, conn, start_date, end_date, status=None, cancel_type=None):
    """특정 기간의 반품 데이터 조회"""
    cursor = conn.cursor()

    start_str = start_date.strftime("%Y-%m-%dT%H:%M")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M")

    status_msg = f", status={status}" if status else ""
    cancel_msg = f", cancelType={cancel_type}" if cancel_type else ""
    print(f"  기간: {start_str} ~ {end_str}{status_msg}{cancel_msg}")

    total_saved = 0
    total_updated = 0
    total_fetched = 0

    try:
        # API 호출
        result = client.get_return_requests(
            start_date=start_str,
            end_date=end_str,
            status=status,
            cancel_type=cancel_type
        )

        if not result or "data" not in result:
            print("    -> 데이터 없음")
            return 0, 0, 0

        return_data = result["data"]
        batch_count = len(return_data)
        total_fetched = batch_count

        print(f"    -> 조회: {batch_count}건")

        # TODO: 페이지네이션 처리
        # 쿠팡 API 응답에 nextToken이나 hasMore 같은 필드가 있는지 확인 필요
        # 만약 50개를 초과하는 데이터가 있다면, 다음 페이지를 조회해야 함

        # DB에 저장
        for item in return_data:
            saved, updated = save_return_to_db(cursor, item)
            total_saved += saved
            total_updated += updated

        conn.commit()

        print(f"    -> 저장: {total_saved}건, 업데이트: {total_updated}건")

        # API Rate Limit 방지
        time.sleep(0.5)

    except Exception as e:
        print(f"    -> 에러: {str(e)}")

    return total_fetched, total_saved, total_updated


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("쿠팡 반품/출고중지 데이터 수집 (개선 버전)")
    print("=" * 80)

    # 계정 정보 로드
    print("\n1. 계정 정보 로드 중...")
    try:
        ACCESS_KEY, SECRET_KEY, VENDOR_ID = get_coupang_credentials()
        print(f"   ✓ Vendor ID: {VENDOR_ID}")
    except Exception as e:
        print(f"   ✗ 실패: {str(e)}")
        return

    # API 클라이언트 초기화
    client = CoupangAPIClient(
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        vendor_id=VENDOR_ID
    )

    # DB 연결
    conn = sqlite3.connect(DB_PATH)

    total_stats = {
        "fetched": 0,
        "saved": 0,
        "updated": 0
    }

    # 최근 30일간 데이터를 1일 단위로 조회
    batch_days = 1
    total_days = 30

    print(f"\n2. 데이터 수집 시작 (최근 {total_days}일, {batch_days}일 단위)")
    print("=" * 80)

    # 2-1. 출고중지 요청 우선 수집 (status=RU, cancelType=RETURN)
    print("\n[1단계] 출고중지 요청 (RELEASE_STOP_UNCHECKED) 수집")
    print("-" * 80)

    for i in range(0, total_days, batch_days):
        end_date = datetime.now() - timedelta(days=i)
        start_date = end_date - timedelta(days=batch_days)

        print(f"\n배치 {i//batch_days + 1}/{total_days//batch_days}:")

        fetched, saved, updated = fetch_returns_by_period(
            client, conn, start_date, end_date,
            status="RU",  # 출고중지요청
            cancel_type="RETURN"
        )

        total_stats["fetched"] += fetched
        total_stats["saved"] += saved
        total_stats["updated"] += updated

    # 2-2. 전체 반품 데이터 수집 (누락 방지)
    print("\n\n[2단계] 전체 반품 데이터 수집")
    print("-" * 80)

    for i in range(0, total_days, batch_days):
        end_date = datetime.now() - timedelta(days=i)
        start_date = end_date - timedelta(days=batch_days)

        print(f"\n배치 {i//batch_days + 1}/{total_days//batch_days}:")

        fetched, saved, updated = fetch_returns_by_period(
            client, conn, start_date, end_date,
            cancel_type="RETURN"
        )

        total_stats["fetched"] += fetched
        total_stats["saved"] += saved
        total_stats["updated"] += updated

    # 최종 통계
    print("\n" + "=" * 80)
    print("수집 완료!")
    print("=" * 80)
    print(f"총 조회: {total_stats['fetched']}건")
    print(f"신규 저장: {total_stats['saved']}건")
    print(f"업데이트: {total_stats['updated']}건")

    # DB 통계
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM return_logs")
    total_in_db = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM return_logs WHERE receipt_status LIKE '%RELEASE_STOP%'")
    release_stop_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM return_logs WHERE receipt_status LIKE '%RETURN%'")
    return_count = cursor.fetchone()[0]

    print(f"\nDB 통계:")
    print(f"  전체 반품 로그: {total_in_db}건")
    print(f"  출고중지 요청: {release_stop_count}건")
    print(f"  일반 반품: {return_count}건")

    conn.close()

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
