"""
쿠팡 API 인증 테스트
"""
import sys
import os
sys.path.append('backend')

# UTF-8 출력 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from backend.app.services.coupang_api import CoupangAPIClient
from backend.app.config import settings

print("="*80)
print("쿠팡 API 인증 테스트")
print("="*80)

print("\n[설정 정보]")
print(f"  ACCESS_KEY: {settings.COUPANG_ACCESS_KEY}")
print(f"  SECRET_KEY: {settings.COUPANG_SECRET_KEY[:10]}... (길이: {len(settings.COUPANG_SECRET_KEY)})")
print(f"  VENDOR_ID: {settings.COUPANG_VENDOR_ID}")
print(f"  BASE_URL: {settings.COUPANG_API_BASE_URL}")

# API 클라이언트 생성
client = CoupangAPIClient()

# HMAC 생성 테스트
print("\n\n[HMAC 서명 생성 테스트]")
test_path = f"/v2/providers/openapi/apis/api/v4/vendors/{settings.COUPANG_VENDOR_ID}/onlineInquiries"
test_query = "status=WAITING&maxPerPage=50"

try:
    signature, timestamp = client._generate_hmac("GET", test_path, test_query)
    print(f"  Timestamp: {timestamp}")
    print(f"  Signature: {signature}")
    print(f"  ✅ HMAC 생성 성공")

    # 메시지 형식 확인
    message = f"{timestamp}GET{test_path}{test_query}"
    print(f"\n  서명 대상 메시지:")
    print(f"    {message}")
    print(f"    길이: {len(message)}")

except Exception as e:
    print(f"  ❌ HMAC 생성 실패: {str(e)}")
    import traceback
    traceback.print_exc()

# 실제 API 호출 테스트
print("\n\n[실제 API 호출 테스트]")
print("  온라인 문의 조회 시도 중...")

try:
    response = client.get_online_inquiries(status="WAITING", max_per_page=1)
    print(f"  ✅ API 호출 성공!")
    print(f"  응답: {response}")

except Exception as e:
    print(f"  ❌ API 호출 실패")
    print(f"  에러: {str(e)}")

    # 에러 메시지 분석
    error_str = str(e)
    if "HMAC format is invalid" in error_str:
        print("\n  🔍 HMAC 형식 오류 원인:")
        print("    1. SECRET_KEY가 잘못되었을 수 있습니다")
        print("    2. HMAC 생성 알고리즘이 쿠팡 API 요구사항과 다를 수 있습니다")
        print("    3. timestamp 형식이 잘못되었을 수 있습니다")
    elif "Authorization" in error_str:
        print("\n  🔍 인증 오류 - ACCESS_KEY를 확인하세요")
    elif "vendor" in error_str.lower():
        print("\n  🔍 VENDOR_ID 오류 - VENDOR_ID를 확인하세요")

# 콜센터 문의 테스트
print("\n\n[콜센터 문의 조회 테스트]")
try:
    response = client.get_call_center_inquiries(
        inquiry_status="PROGRESS",
        partner_transfer_status="TRANSFER",
        max_per_page=1
    )
    print(f"  ✅ API 호출 성공!")
    print(f"  응답: {response}")

except Exception as e:
    print(f"  ❌ API 호출 실패: {str(e)}")

print("\n" + "="*80)
