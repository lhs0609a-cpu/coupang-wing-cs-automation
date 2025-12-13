"""
Fly.io 서버에 쿠팡 계정 등록 (API를 통해)
"""
import requests
import json

# Fly.io 서버 URL
API_BASE_URL = "https://coupang-wing-cs-backend.fly.dev"

def register_coupang_account():
    """쿠팡 계정 등록"""

    account_data = {
        "name": "반품 관리용 쿠팡 계정",
        "vendor_id": "A00492891",
        "access_key": "A00492891",
        "secret_key": "534fcf1c8dfe9d5e222b507f52e772d4637738b7",
        "wing_username": "lhs0609",
        "wing_password": "pascal1623!!"
    }

    print(f"[INFO] Fly.io 서버에 쿠팡 계정 등록 중...")
    print(f"서버: {API_BASE_URL}")
    print(f"Vendor ID: {account_data['vendor_id']}")

    try:
        # 기존 계정 확인
        response = requests.get(f"{API_BASE_URL}/api/coupang-accounts", timeout=30)

        if response.status_code == 200:
            accounts = response.json()
            print(f"✅ 기존 계정 {len(accounts)}개 발견")

            for acc in accounts:
                print(f"  - {acc['name']} (Vendor: {acc['vendor_id']})")

            # 동일한 vendor_id가 있는지 확인
            existing = next((acc for acc in accounts if acc['vendor_id'] == account_data['vendor_id']), None)

            if existing:
                print(f"\n⚠️  동일한 Vendor ID의 계정이 이미 존재합니다 (ID: {existing['id']})")
                print(f"계정명: {existing['name']}")

                # 업데이트
                update_url = f"{API_BASE_URL}/api/coupang-accounts/{existing['id']}"
                update_data = {
                    "name": account_data["name"],
                    "access_key": account_data["access_key"],
                    "secret_key": account_data["secret_key"],
                    "wing_username": account_data["wing_username"],
                    "wing_password": account_data["wing_password"],
                    "is_active": True
                }

                print(f"\n🔄 계정 정보 업데이트 중...")
                update_response = requests.put(update_url, json=update_data, timeout=30)

                if update_response.status_code == 200:
                    print(f"✅ 계정 업데이트 완료!")
                    result = update_response.json()
                    print(f"계정 ID: {result.get('id')}")
                    print(f"계정명: {result.get('name')}")
                    return result
                else:
                    print(f"❌ 업데이트 실패: {update_response.status_code}")
                    print(update_response.text)
                    return None

        # 새 계정 등록
        print(f"\n➕ 새 계정 등록 중...")
        response = requests.post(
            f"{API_BASE_URL}/api/coupang-accounts",
            json=account_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 201:
            print(f"✅ 계정 등록 완료!")
            result = response.json()
            print(f"계정 ID: {result.get('id')}")
            print(f"계정명: {result.get('name')}")
            print(f"Vendor ID: {result.get('vendor_id')}")
            return result
        else:
            print(f"❌ 등록 실패: {response.status_code}")
            print(response.text)
            return None

    except requests.exceptions.Timeout:
        print(f"❌ 타임아웃: 서버 응답 없음 (30초 초과)")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 연결 오류: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def register_naver_account():
    """네이버 계정 등록"""

    account_data = {
        "name": "메인 네이버 계정",
        "naver_username": "lhs0609",
        "naver_password": "pascal1623!!",
        "client_id": "optional",
        "client_secret": "optional",
        "is_default": True
    }

    print(f"\n📡 Fly.io 서버에 네이버 계정 등록 중...")

    try:
        # 기존 계정 확인
        response = requests.get(f"{API_BASE_URL}/api/naver-accounts", timeout=30)

        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                accounts = result['data']
                print(f"✅ 기존 네이버 계정 {len(accounts)}개 발견")

                for acc in accounts:
                    print(f"  - {acc['name']} (기본: {acc.get('is_default', False)})")

                # 동일한 username이 있는지 확인
                existing = next((acc for acc in accounts if acc.get('naver_username') == account_data['naver_username']), None)

                if existing:
                    print(f"\n⚠️  동일한 계정이 이미 존재합니다 (ID: {existing['id']})")
                    print(f"이미 등록된 계정을 사용합니다.")
                    return existing

        # 새 계정 등록
        print(f"\n➕ 새 네이버 계정 등록 중...")
        response = requests.post(
            f"{API_BASE_URL}/api/naver-accounts",
            json=account_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code in [200, 201]:
            print(f"✅ 네이버 계정 등록 완료!")
            result = response.json()
            if result.get('success'):
                account = result.get('data')
                print(f"계정 ID: {account.get('id')}")
                print(f"계정명: {account.get('name')}")
                return account
            return result
        else:
            print(f"❌ 등록 실패: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Fly.io 서버 계정 등록")
    print("=" * 60)

    # 쿠팡 계정 등록
    coupang_result = register_coupang_account()

    # 네이버 계정 등록
    naver_result = register_naver_account()

    print("\n" + "=" * 60)
    print("등록 결과")
    print("=" * 60)
    print(f"쿠팡 계정: {'✅ 성공' if coupang_result else '❌ 실패'}")
    print(f"네이버 계정: {'✅ 성공' if naver_result else '❌ 실패'}")

    if coupang_result and naver_result:
        print("\n✅ 모든 계정이 Fly.io 서버에 등록되었습니다!")
        print("이제 어떤 컴퓨터에서든 접속 가능합니다.")
    else:
        print("\n⚠️  일부 계정 등록이 실패했습니다. 위 오류를 확인하세요.")
