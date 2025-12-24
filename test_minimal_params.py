"""
최소 파라미터로 API 테스트
"""
import sys
import hmac
import hashlib
import time
from datetime import datetime, timezone
import httpx

# 설정값
ACCESS_KEY = "7a2a99f7-9202-4d7d-b094-6b6d758601d4"
SECRET_KEY = "13da414b5cf1e3b9ae4b236ab5f9329424d60c96"
VENDOR_ID = "A00492891"
BASE_URL = "https://api-gateway.coupang.com"

def generate_hmac(method, path, query=""):
    utc_now = datetime.now(timezone.utc)
    datetime_str = utc_now.strftime('%y%m%dT%H%M%SZ')

    message = f"{datetime_str}{method}{path}{query}"

    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature, datetime_str

print("="*80)
print("최소 파라미터 테스트")
print("="*80)

# 테스트 1: answeredType만
print("\n[테스트 1] answeredType만")
path = f"/v2/providers/openapi/apis/api/v4/vendors/{VENDOR_ID}/onlineInquiries"
query = "answeredType=NOANSWER&maxPerPage=5"

signature, timestamp = generate_hmac("GET", path, query)
headers = {
    "Content-Type": "application/json;charset=UTF-8",
    "Authorization": f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp}, signature={signature}",
}

client = httpx.Client(timeout=30.0)
try:
    url = f"{BASE_URL}{path}?{query}"
    print(f"URL: {url}")
    response = client.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {str(e)[:200]}")

# 테스트 2: inquiriedDateFrom/To 시도
print("\n[테스트 2] inquiriedDateFrom/To")
query2 = "answeredType=NOANSWER&inquiriedDateFrom=2024-11-14&inquiriedDateTo=2024-11-20&maxPerPage=5"

signature2, timestamp2 = generate_hmac("GET", path, query2)
headers2 = {
    "Content-Type": "application/json;charset=UTF-8",
    "Authorization": f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp2}, signature={signature2}",
}

try:
    url2 = f"{BASE_URL}{path}?{query2}"
    print(f"URL: {url2}")
    response2 = client.get(url2, headers=headers2)
    print(f"Status: {response2.status_code}")
    print(f"Response: {response2.text[:500]}")
except Exception as e:
    print(f"Error: {str(e)[:200]}")

# 테스트 3: createdAtFrom/To 시도
print("\n[테스트 3] createdAtFrom/To")
query3 = "answeredType=NOANSWER&createdAtFrom=2024-11-14&createdAtTo=2024-11-20&maxPerPage=5"

signature3, timestamp3 = generate_hmac("GET", path, query3)
headers3 = {
    "Content-Type": "application/json;charset=UTF-8",
    "Authorization": f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp3}, signature={signature3}",
}

try:
    url3 = f"{BASE_URL}{path}?{query3}"
    print(f"URL: {url3}")
    response3 = client.get(url3, headers=headers3)
    print(f"Status: {response3.status_code}")
    print(f"Response: {response3.text[:500]}")
except Exception as e:
    print(f"Error: {str(e)[:200]}")

client.close()
print("\n" + "="*80)
