"""
더 넓은 기간으로 문의 조회 (실제 데이터 확인)
"""
import sys
sys.path.append('backend')

# UTF-8 출력
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from backend.app.services.coupang_api import CoupangAPIClient

client = CoupangAPIClient()

print("="*80)
print("다양한 기간으로 문의 조회")
print("="*80)

# 여러 기간 시도
date_ranges = [
    ("2024-11-01", "2024-11-07", "11월 1주"),
    ("2024-11-08", "2024-11-14", "11월 2주"),
    ("2024-11-14", "2024-11-20", "11월 3주"),
    ("2024-10-24", "2024-10-30", "10월 마지막주"),
]

for start, end, label in date_ranges:
    print(f"\n[{label}] {start} ~ {end}")

    try:
        result = client.get_online_inquiries(
            answered_type="ALL",
            start_date=start,
            end_date=end,
            max_per_page=5
        )

        data = result.get('data', {})
        total = data.get('pagination', {}).get('totalElements', 0)
        content = data.get('content', [])

        print(f"  온라인 문의: {total}개")

        if content:
            print(f"  샘플:")
            for idx, item in enumerate(content[:3], 1):
                inquiry_id = item.get('inquiryId')
                text = item.get('content', '')[:60]
                date = item.get('inquiryAt', '')[:10]
                print(f"    {idx}. [{inquiry_id}] {date} - {text}...")

    except Exception as e:
        print(f"  ❌ 오류: {str(e)[:100]}")

print("\n" + "="*80)
