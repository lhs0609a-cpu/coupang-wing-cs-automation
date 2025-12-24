"""
쿠팡 API 반품 목록 조회 테스트
"""
import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.coupang_api_client import CoupangAPIClient
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 API 키 가져오기
ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY")
SECRET_KEY = os.getenv("COUPANG_SECRET_KEY")
VENDOR_ID = os.getenv("COUPANG_VENDOR_ID")

print("=" * 80)
print("🔍 쿠팡 반품 목록 조회 테스트")
print("=" * 80)
print()

# API 클라이언트 생성
try:
    client = CoupangAPIClient(
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        vendor_id=VENDOR_ID
    )
    print("✅ 쿠팡 API 클라이언트 초기화 완료")
    print(f"   - Vendor ID: {VENDOR_ID}")
    print(f"   - Access Key: {ACCESS_KEY[:10]}...")
    print()
except Exception as e:
    print(f"❌ API 클라이언트 초기화 실패: {str(e)}")
    sys.exit(1)

# 최근 7일간의 반품 조회
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"📅 조회 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
print()

try:
    # 반품 목록 조회
    print("🔄 쿠팡 API 호출 중...")
    response = client.get_return_requests(
        start_date=start_date.strftime("%Y-%m-%dT00:00"),
        end_date=end_date.strftime("%Y-%m-%dT23:59"),
        cancel_type=None,  # RETURN + CANCEL 모두 조회
        search_type="timeFrame"
    )

    print("✅ API 호출 성공!")
    print()

    # 응답 구조 확인
    if not response:
        print("⚠️  응답 데이터가 비어있습니다.")
        sys.exit(0)

    if "data" not in response:
        print("⚠️  응답에 'data' 필드가 없습니다.")
        print(f"응답 키: {list(response.keys())}")
        print(f"응답 내용: {response}")
        sys.exit(0)

    returns = response["data"]

    print("=" * 80)
    print(f"📦 총 {len(returns)}건의 반품/취소 요청 발견")
    print("=" * 80)
    print()

    if len(returns) == 0:
        print("📭 반품 내역이 없습니다.")
        print()
        print("💡 팁:")
        print("   - 최근 7일 이내에 반품/취소 요청이 있는지 확인하세요")
        print("   - 쿠팡 판매자센터에서 직접 확인해보세요")
        sys.exit(0)

    # 각 반품 항목 출력
    for idx, return_item in enumerate(returns, 1):
        print(f"\n{'─' * 80}")
        print(f"📋 반품 #{idx}")
        print(f"{'─' * 80}")

        # 기본 정보
        receipt_id = return_item.get("receiptId", "N/A")
        order_id = return_item.get("orderId", "N/A")
        receipt_type = return_item.get("receiptType", "N/A")
        receipt_status = return_item.get("receiptStatus", "N/A")

        print(f"📌 Receipt ID: {receipt_id}")
        print(f"📌 Order ID: {order_id}")
        print(f"📌 타입: {receipt_type}")
        print(f"📌 상태: {receipt_status}")

        # 상태 한글 변환
        status_map = {
            'RELEASE_STOP_UNCHECKED': '출고중지요청',
            'RETURNS_UNCHECKED': '반품접수',
            'VENDOR_WAREHOUSE_CONFIRM': '입고완료',
            'REQUEST_COUPANG_CHECK': '쿠팡확인요청',
            'RETURNS_COMPLETED': '반품완료'
        }
        status_korean = status_map.get(receipt_status, receipt_status)
        print(f"   → 상태 (한글): {status_korean}")

        # 수령인 정보
        shipping_to = return_item.get("shippingTo") or return_item.get("receiverInfo")
        if shipping_to:
            receiver_name = shipping_to.get("name") or shipping_to.get("receiverName", "N/A")
            receiver_phone = shipping_to.get("phoneNumber") or shipping_to.get("phone", "N/A")
            print(f"👤 수령인: {receiver_name}")
            print(f"📞 전화번호: {receiver_phone}")
        else:
            print(f"👤 수령인: 정보 없음")

        # 반품 사유
        reason1 = return_item.get("cancelReasonCategory1", "N/A")
        reason2 = return_item.get("cancelReasonCategory2", "N/A")
        print(f"📝 반품 사유: {reason1} - {reason2}")

        # 반품 상품 목록
        return_items = return_item.get("returnItems", [])
        if return_items:
            print(f"\n🛍️  반품 상품 ({len(return_items)}개):")
            for item_idx, item in enumerate(return_items, 1):
                product_name = item.get("vendorItemPackageName") or item.get("vendorItemName", "N/A")
                vendor_item_id = item.get("vendorItemId", "N/A")
                cancel_count = item.get("cancelCount", 1)

                print(f"   {item_idx}. {product_name}")
                print(f"      - 상품 ID: {vendor_item_id}")
                print(f"      - 수량: {cancel_count}개")

        # 생성 시간
        created_at = return_item.get("createdAt")
        if created_at:
            print(f"🕐 요청 시간: {created_at}")

    print()
    print("=" * 80)
    print(f"✅ 총 {len(returns)}건의 반품 정보 조회 완료")
    print("=" * 80)

except Exception as e:
    print(f"❌ 오류 발생: {str(e)}")
    import traceback
    print()
    print("상세 오류:")
    traceback.print_exc()
    sys.exit(1)
