"""
간단한 API 테스트 - 다양한 파라미터 조합 시도
"""
import sys
sys.path.append('backend')

from backend.app.services.coupang_api import CoupangAPIClient
from datetime import datetime, timedelta, timezone

client = CoupangAPIClient()

print("="*80)
print("다양한 파라미터 조합 테스트")
print("="*80)

# 테스트 1: 최소 날짜 범위 (1일)
print("\n[테스트 1] 1일 범위")
try:
    today = datetime.now(timezone.utc)
    result = client.get_online_inquiries(
        answered_type="NOANSWER",
        start_date=today.strftime('%Y-%m-%d'),
        end_date=today.strftime('%Y-%m-%d'),
        max_per_page=1
    )
    print(f"✅ 성공! 응답: {result}")
except Exception as e:
    print(f"❌ 실패: {str(e)[:200]}")

# 테스트 2: 어제부터 오늘까지
print("\n[테스트 2] 어제부터 오늘")
try:
    today = datetime.now(timezone.utc)
    yesterday = today - timedelta(days=1)
    result = client.get_online_inquiries(
        answered_type="NOANSWER",
        start_date=yesterday.strftime('%Y-%m-%d'),
        end_date=today.strftime('%Y-%m-%d'),
        max_per_page=1
    )
    print(f"✅ 성공! 응답: {result}")
except Exception as e:
    print(f"❌ 실패: {str(e)[:200]}")

# 테스트 3: 3일 범위
print("\n[테스트 3] 3일 범위")
try:
    today = datetime.now(timezone.utc)
    three_days_ago = today - timedelta(days=3)
    result = client.get_online_inquiries(
        answered_type="NOANSWER",
        start_date=three_days_ago.strftime('%Y-%m-%d'),
        end_date=today.strftime('%Y-%m-%d'),
        max_per_page=1
    )
    print(f"✅ 성공! 응답: {result}")
except Exception as e:
    print(f"❌ 실패: {str(e)[:200]}")

# 테스트 4: ALL 타입
print("\n[테스트 4] answered_type=ALL, 1일")
try:
    today = datetime.now(timezone.utc)
    result = client.get_online_inquiries(
        answered_type="ALL",
        start_date=today.strftime('%Y-%m-%d'),
        end_date=today.strftime('%Y-%m-%d'),
        max_per_page=1
    )
    print(f"✅ 성공! 응답: {result}")
except Exception as e:
    print(f"❌ 실패: {str(e)[:200]}")

print("\n" + "="*80)
