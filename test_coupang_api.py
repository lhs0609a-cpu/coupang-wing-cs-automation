"""Test Coupang API HMAC authentication"""
import hmac
import hashlib
import datetime
import requests

# 쿠팡 API 인증 정보
ACCESS_KEY = "7a2a99f7-9202-4d7d-b094-6b6d758601d4"
SECRET_KEY = "13da414b5cf1e3b9ae4b236ab5f9329424d60c96"
VENDOR_ID = "A00492891"

def generate_hmac(method, path, query=""):
    """Generate HMAC signature"""
    now = datetime.datetime.utcnow()
    datetime_str = now.strftime('%y%m%d') + 'T' + now.strftime('%H%M%S') + 'Z'

    # Create message to sign
    message = datetime_str + method + path + query

    # Generate HMAC
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    print(f"DateTime: {datetime_str}")
    print(f"Method: {method}")
    print(f"Path: {path}")
    print(f"Query: {query}")
    print(f"Message: {message}")
    print(f"Signature: {signature}")

    return signature, datetime_str

def test_coupang_api():
    """Test Coupang API connection"""
    path = f"/v2/providers/openapi/apis/api/v5/vendors/{VENDOR_ID}/onlineInquiries"
    query = f"inquiryStartAt=2025-11-11&inquiryEndAt=2025-11-11&vendorId={VENDOR_ID}&answeredType=ALL&pageSize=1&pageNum=1"

    url = f"https://api-gateway.coupang.com{path}?{query}"

    # Test with query string included in HMAC (WITHOUT ? prefix - correct way)
    print("\n=== Test 1: With query string (no ?) ===")
    signature, datetime_str = generate_hmac("GET", path, query)

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_str}, signature={signature}"
    }

    print(f"\nRequest URL: {url}")
    print(f"Authorization: {headers['Authorization']}")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"\nError: {str(e)}")

    # Test without query string in HMAC
    print("\n\n=== Test 2: Without query string ===")
    signature2, datetime_str2 = generate_hmac("GET", path, "")

    headers2 = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_str2}, signature={signature2}"
    }

    print(f"\nRequest URL: {url}")
    print(f"Authorization: {headers2['Authorization']}")

    try:
        response2 = requests.get(url, headers=headers2, timeout=30)
        print(f"\nStatus Code: {response2.status_code}")
        print(f"Response: {response2.text}")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    test_coupang_api()
