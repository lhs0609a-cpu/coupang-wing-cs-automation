"""
문의 수집 및 결과 표시
"""
import sys
import os
sys.path.append('backend')

# UTF-8 출력
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from backend.app.database import SessionLocal
from backend.app.services.inquiry_collector import InquiryCollector
from backend.app.services.coupang_api import CoupangAPIClient

print("="*80)
print("문의 수집 및 결과 표시")
print("="*80)

db = SessionLocal()

try:
    # 1. 온라인 문의 수집
    print("\n[1] 온라인 문의 수집 중...")
    collector = InquiryCollector(db)

    online_inquiries = collector.collect_new_inquiries(
        inquiry_type="online",
        status_filter=None
    )

    print(f"✅ 온라인 문의 {len(online_inquiries)}개 수집 완료")

    # 2. 콜센터 문의 수집
    print("\n[2] 콜센터 문의 수집 중...")

    callcenter_inquiries = collector.collect_new_inquiries(
        inquiry_type="callcenter",
        status_filter=None
    )

    print(f"✅ 콜센터 문의 {len(callcenter_inquiries)}개 수집 완료")

    # 3. 통계 조회
    print("\n[3] 전체 통계")
    stats = collector.get_inquiry_stats()

    print(f"\n📊 데이터베이스 현황:")
    print(f"  - 총 문의: {stats['total']}개")
    print(f"  - 미처리(pending): {stats['pending']}개")
    print(f"  - 처리중(processing): {stats['processing']}개")
    print(f"  - 처리완료(processed): {stats['processed']}개")
    print(f"  - 실패(failed): {stats['failed']}개")
    print(f"  - 사람 검토 필요: {stats['requires_human']}개")
    print(f"  - 긴급: {stats['urgent']}개")

    # 4. 최근 수집된 문의 샘플
    if len(online_inquiries) > 0 or len(callcenter_inquiries) > 0:
        print("\n\n📋 최근 수집된 문의 샘플:")

        all_inquiries = online_inquiries + callcenter_inquiries
        for idx, inquiry in enumerate(all_inquiries[:5], 1):
            print(f"\n  [{idx}] 문의 ID: {inquiry.id} (쿠팡 ID: {inquiry.coupang_inquiry_id})")
            print(f"      날짜: {inquiry.inquiry_date}")
            print(f"      상태: {inquiry.status}")
            print(f"      내용: {inquiry.inquiry_text[:100]}..." if len(inquiry.inquiry_text) > 100 else f"      내용: {inquiry.inquiry_text}")
            print(f"      카테고리: {inquiry.inquiry_category}")

            if inquiry.order_number:
                print(f"      주문번호: {inquiry.order_number}")
            if inquiry.product_name:
                print(f"      상품: {inquiry.product_name[:50]}...")

    # 5. API로 직접 조회 (비교용)
    print("\n\n[4] API 직접 조회 (최근 7일)")
    client = CoupangAPIClient()

    # 온라인 문의
    online_result = client.get_online_inquiries(
        answered_type="ALL",
        start_date="2024-11-14",
        end_date="2024-11-20",
        max_per_page=5
    )

    online_data = online_result.get('data', {})
    online_total = online_data.get('pagination', {}).get('totalElements', 0)

    print(f"\n  온라인 문의 (API): 총 {online_total}개")

    online_content = online_data.get('content', [])
    if online_content:
        print(f"  샘플 (최대 5개):")
        for idx, item in enumerate(online_content[:5], 1):
            print(f"    {idx}. [{item.get('inquiryId')}] {item.get('content', '')[:80]}...")

    # 콜센터 문의
    cc_result = client.get_call_center_inquiries(
        partner_counseling_status="NONE",
        start_date="2024-11-14",
        end_date="2024-11-20",
        max_per_page=5
    )

    cc_data = cc_result.get('data', {})
    cc_total = cc_data.get('pagination', {}).get('totalElements', 0)

    print(f"\n  콜센터 문의 (API): 총 {cc_total}개")

    cc_content = cc_data.get('content', [])
    if cc_content:
        print(f"  샘플 (최대 5개):")
        for idx, item in enumerate(cc_content[:5], 1):
            print(f"    {idx}. [{item.get('inquiryId')}] {item.get('content', '')[:80]}...")

except Exception as e:
    print(f"\n❌ 오류 발생: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    db.close()

print("\n" + "="*80)
print("수집 완료!")
print("="*80)
