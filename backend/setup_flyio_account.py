"""Fly.io server account setup"""
import requests

API_BASE_URL = "https://coupang-wing-cs-backend.fly.dev"

print("=" * 60)
print("Fly.io server account setup")
print("=" * 60)

# Coupang account
print("\n[1/2] Coupang account registration...")
coupang_data = {
    "name": "Main Coupang Account",
    "vendor_id": "A00492891",
    "access_key": "A00492891",
    "secret_key": "534fcf1c8dfe9d5e222b507f52e772d4637738b7",
    "wing_username": "lhs0609",
    "wing_password": "pascal1623!!"
}

try:
    resp = requests.post(
        f"{API_BASE_URL}/api/coupang-accounts",
        json=coupang_data,
        timeout=30
    )
    if resp.status_code in [200, 201]:
        print("[OK] Coupang account registered successfully")
        print(f"     ID: {resp.json().get('id')}")
    elif resp.status_code == 400 and "already exists" in resp.text:
        print("[INFO] Coupang account already exists")
    else:
        print(f"[ERROR] Failed: {resp.status_code}")
        print(resp.text[:200])
except Exception as e:
    print(f"[ERROR] {str(e)}")

# Naver account
print("\n[2/2] Naver account registration...")
naver_data = {
    "name": "Main Naver Account",
    "naver_username": "lhs0609",
    "naver_password": "pascal1623!!",
    "client_id": "optional",
    "client_secret": "optional",
    "is_default": True
}

try:
    resp = requests.post(
        f"{API_BASE_URL}/api/naver-accounts",
        json=naver_data,
        timeout=30
    )
    if resp.status_code in [200, 201]:
        print("[OK] Naver account registered successfully")
        result = resp.json()
        if result.get('success'):
            print(f"     ID: {result['data'].get('id')}")
    else:
        print(f"[ERROR] Failed: {resp.status_code}")
        print(resp.text[:200])
except Exception as e:
    print(f"[ERROR] {str(e)}")

print("\n" + "=" * 60)
print("Setup complete!")
print("=" * 60)
