"""
최종 API 테스트 - 모든 수정 사항 적용
"""
import sys
import os
sys.path.append('backend')

# UTF-8 출력
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from backend.app.services.coupang_api import CoupangAPIClient

client = CoupangAPIClient()

print("="*80)
print("최종 API 테스트")
print("="*80)

# 테스트 1: 온라인 문의 (미답변)
print("\n[테스트 1] 온라인 문의 조회 (미답변)")
try:
    result = client.get_online_inquiries(
        answered_type="NOANSWER",
        start_date="2024-11-14",
        end_date="2024-11-20",
        max_per_page=10
    )
    print(f"✅ 성공!")
    print(f"코드: {result.get('code')}")
    data = result.get('data', {})
    content = data.get('content', [])
    pagination = data.get('pagination', {})
    print(f"총 문의 수: {pagination.get('totalElements', 0)}")
    print(f"현재 페이지 문의 수: {len(content)}")

    if content:
        print(f"\n첫 번째 문의 샘플:")
        first = content[0]
        print(f"  - ID: {first.get('inquiryId')}")
        print(f"  - 내용: {first.get('content', '')[:100]}...")
        print(f"  - 날짜: {first.get('inquiryAt')}")

except Exception as e:
    print(f"❌ 실패: {str(e)[:300]}")

# 테스트 2: 온라인 문의 (전체)
print("\n[테스트 2] 온라인 문의 조회 (전체)")
try:
    result = client.get_online_inquiries(
        answered_type="ALL",
        start_date="2024-11-14",
        end_date="2024-11-20",
        max_per_page=10
    )
    print(f"✅ 성공!")
    print(f"코드: {result.get('code')}")
    data = result.get('data', {})
    pagination = data.get('pagination', {})
    print(f"총 문의 수: {pagination.get('totalElements', 0)}")

except Exception as e:
    print(f"❌ 실패: {str(e)[:300]}")

# 테스트 3: 콜센터 문의 (미답변)
print("\n[테스트 3] 콜센터 문의 조회 (미답변)")
try:
    result = client.get_call_center_inquiries(
        partner_counseling_status="NO_ANSWER",
        start_date="2024-11-14",
        end_date="2024-11-20",
        max_per_page=10
    )
    print(f"✅ 성공!")
    print(f"코드: {result.get('code')}")
    data = result.get('data', {})
    content = data.get('content', [])
    pagination = data.get('pagination', {})
    print(f"총 문의 수: {pagination.get('totalElements', 0)}")
    print(f"현재 페이지 문의 수: {len(content)}")

except Exception as e:
    print(f"❌ 실패: {str(e)[:300]}")

# 테스트 4: 콜센터 문의 (전체)
print("\n[테스트 4] 콜센터 문의 조회 (전체)")
try:
    result = client.get_call_center_inquiries(
        partner_counseling_status="NONE",
        start_date="2024-11-14",
        end_date="2024-11-20",
        max_per_page=10
    )
    print(f"✅ 성공!")
    print(f"코드: {result.get('code')}")
    data = result.get('data', {})
    pagination = data.get('pagination', {})
    print(f"총 문의 수: {pagination.get('totalElements', 0)}")

except Exception as e:
    print(f"❌ 실패: {str(e)[:300]}")

print("\n" + "="*80)
print("✅ 모든 테스트 완료!")
print("="*80)
