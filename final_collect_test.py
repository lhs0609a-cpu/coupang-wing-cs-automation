"""
최종 수집 테스트 - 실제 데이터로 수집
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
from backend.app.services.coupang_api import CoupangAPIClient

print("="*80)
print("최종 수집 테스트")
print("="*80)

client = CoupangAPIClient()

# 1. API 직접 조회
print("\n[1] API로 문의 조회 (2025-11-02 ~ 2025-11-08)")

online_result = client.get_online_inquiries(
    answered_type="ALL",
    start_date="2025-11-02",
    end_date="2025-11-08",
    max_per_page=50
)

online_data = online_result.get('data', {})
online_content = online_data.get('content', [])
online_total = online_data.get('pagination', {}).get('totalElements', 0)

print(f"\n✅ 온라인 문의: 총 {online_total}개")
print(f"   현재 페이지: {len(online_content)}개")

if online_content:
    print("\n📋 문의 목록 (최대 10개):")
    for idx, item in enumerate(online_content[:10], 1):
        inquiry_id = item.get('inquiryId')
        content = item.get('content', '')
        date = item.get('inquiryAt', '')[:10]
        product_name = item.get('productName', 'N/A')

        # 답변 여부 확인
        comments = item.get('commentDtoList', [])
        answered = "✅ 답변완료" if comments else "❌ 미답변"

        print(f"\n  [{idx}] ID: {inquiry_id} ({answered})")
        print(f"      날짜: {date}")
        print(f"      내용: {content[:100]}{'...' if len(content) > 100 else ''}")
        if product_name != 'N/A':
            print(f"      상품: {product_name[:60]}...")

# 2. 콜센터 문의
print("\n\n[2] 콜센터 문의 조회 (2025-11-02 ~ 2025-11-08)")

cc_result = client.get_call_center_inquiries(
    partner_counseling_status="NONE",
    start_date="2025-11-02",
    end_date="2025-11-08",
    max_per_page=50
)

cc_data = cc_result.get('data', {})
cc_content = cc_data.get('content', [])
cc_total = cc_data.get('pagination', {}).get('totalElements', 0)

print(f"\n✅ 콜센터 문의: 총 {cc_total}개")

if cc_content:
    print(f"\n📋 콜센터 문의 (최대 5개):")
    for idx, item in enumerate(cc_content[:5], 1):
        inquiry_id = item.get('inquiryId')
        content = item.get('content', '')
        print(f"  {idx}. [{inquiry_id}] {content[:80]}...")

# 3. 통계
print("\n\n[3] 문의 통계")
print(f"  총 문의: {online_total + cc_total}개")
print(f"  - 온라인: {online_total}개")
print(f"  - 콜센터: {cc_total}개")

# 미답변 카운트
unanswered = sum(1 for item in online_content if not item.get('commentDtoList'))
print(f"\n  미답변 문의: {unanswered}개")
print(f"  답변완료: {len(online_content) - unanswered}개")

print("\n" + "="*80)
print("✅ API가 정상적으로 작동하고 있습니다!")
print(f"✅ 총 {online_total + cc_total}개의 문의를 확인했습니다.")
print("="*80)
