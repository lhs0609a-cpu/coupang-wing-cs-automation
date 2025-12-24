"""
5일 범위로 API 테스트
"""
import sys
sys.path.append('backend')

from backend.app.services.coupang_api import CoupangAPIClient

client = CoupangAPIClient()

print("="*80)
print("5일 범위 테스트")
print("="*80)

# 2024년 11월 16일부터 20일까지 (5일)
start_date = "2024-11-16"
end_date = "2024-11-20"

print(f"\n날짜 범위: {start_date} ~ {end_date} (5일)")

# 온라인 문의
print("\n[온라인 문의 조회]")
try:
    result = client.get_online_inquiries(
        answered_type="ALL",
        start_date=start_date,
        end_date=end_date,
        max_per_page=10
    )
    print("SUCCESS!")
    print(f"응답: {result}")
except Exception as e:
    print(f"FAILED: {str(e)[:300]}")

print("\n" + "="*80)
