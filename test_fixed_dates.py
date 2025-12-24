"""
올바른 날짜로 API 테스트
"""
import sys
sys.path.append('backend')

from backend.app.services.coupang_api import CoupangAPIClient

client = CoupangAPIClient()

print("="*80)
print("2024년 날짜로 API 테스트")
print("="*80)

# 올바른 날짜 사용 (2024년)
# 2024년 11월 14일부터 11월 20일까지
start_date = "2024-11-14"
end_date = "2024-11-20"

print(f"\n날짜 범위: {start_date} ~ {end_date}")

# 테스트 1: 온라인 문의
print("\n[테스트 1] 온라인 문의 조회")
try:
    result = client.get_online_inquiries(
        answered_type="NOANSWER",
        start_date=start_date,
        end_date=end_date,
        max_per_page=5
    )
    print("✅ 성공!")
    print(f"응답 코드: {result.get('code', 'N/A')}")
    print(f"응답: {result}")
except Exception as e:
    print(f"❌ 실패: {str(e)[:300]}")

# 테스트 2: 콜센터 문의
print("\n[테스트 2] 콜센터 문의 조회")
try:
    result = client.get_call_center_inquiries(
        inquiry_status="PROGRESS",
        partner_transfer_status="TRANSFER",
        partner_counseling_status="WAITING",
        start_date=start_date,
        end_date=end_date,
        max_per_page=5
    )
    print("✅ 성공!")
    print(f"응답 코드: {result.get('code', 'N/A')}")
    print(f"응답: {result}")
except Exception as e:
    print(f"❌ 실패: {str(e)[:300]}")

# 테스트 3: 더 짧은 기간 (3일)
print("\n[테스트 3] 더 짧은 기간 (3일)")
short_start = "2024-11-17"
short_end = "2024-11-20"
try:
    result = client.get_online_inquiries(
        answered_type="ALL",
        start_date=short_start,
        end_date=short_end,
        max_per_page=5
    )
    print("✅ 성공!")
    print(f"응답 코드: {result.get('code', 'N/A')}")

    # 데이터 파싱
    if 'data' in result:
        data = result['data']
        if isinstance(data, dict):
            inquiries = data.get('inquiries', [])
            print(f"문의 개수: {len(inquiries)}개")
            if inquiries:
                print("\n첫 번째 문의 샘플:")
                first = inquiries[0]
                print(f"  - ID: {first.get('inquiryId', 'N/A')}")
                print(f"  - 내용: {first.get('inquiryContent', 'N/A')[:100]}...")
                print(f"  - 날짜: {first.get('inquiryDate', 'N/A')}")
        elif isinstance(data, list):
            print(f"문의 개수: {len(data)}개")
    else:
        print(f"전체 응답: {result}")

except Exception as e:
    print(f"❌ 실패: {str(e)[:300]}")

print("\n" + "="*80)
