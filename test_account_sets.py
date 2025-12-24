"""
계정 세트 API 테스트 스크립트
"""
import requests
import json

def test_account_sets_endpoint():
    """계정 세트 엔드포인트 테스트"""
    base_url = "http://localhost:8000"

    print("=" * 60)
    print("계정 세트 API 테스트")
    print("=" * 60)

    # 1. 서버 연결 테스트
    print("\n1. 서버 연결 테스트...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   ✅ 서버 연결 성공: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 서버 연결 실패: {e}")
        return

    # 2. GET /api/account-sets - 계정 세트 목록 조회
    print("\n2. 계정 세트 목록 조회 테스트...")
    try:
        response = requests.get(f"{base_url}/api/account-sets", timeout=5)
        print(f"   응답 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 성공: {data.get('count', 0)}개의 계정 세트 발견")
            print(f"   데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
        elif response.status_code == 404:
            print(f"   ❌ 404 Not Found - 엔드포인트가 등록되지 않았습니다!")
            print(f"   응답: {response.text}")
        else:
            print(f"   ❌ 오류: {response.status_code}")
            print(f"   응답: {response.text}")
    except Exception as e:
        print(f"   ❌ 요청 실패: {e}")

    # 3. POST /api/account-sets - 계정 세트 생성 테스트
    print("\n3. 계정 세트 생성 테스트...")
    test_payload = {
        "name": "테스트 계정 세트",
        "description": "테스트용 계정 세트",
        "coupang_account_name": "테스트 쿠팡",
        "coupang_vendor_id": "TEST_VENDOR_001",
        "coupang_access_key": "test_access_key",
        "coupang_secret_key": "test_secret_key",
        "coupang_wing_username": "test_wing_user",
        "coupang_wing_password": "test_wing_pass",
        "naver_account_name": "테스트 네이버",
        "naver_username": "test_naver_user",
        "naver_password": "test_naver_pass",
        "is_default": True
    }

    try:
        response = requests.post(
            f"{base_url}/api/account-sets",
            json=test_payload,
            timeout=10
        )
        print(f"   응답 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 생성 성공!")
            print(f"   응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
        elif response.status_code == 404:
            print(f"   ❌ 404 Not Found - POST 엔드포인트가 등록되지 않았습니다!")
            print(f"   응답: {response.text}")
        else:
            print(f"   ❌ 오류: {response.status_code}")
            print(f"   응답: {response.text}")
    except Exception as e:
        print(f"   ❌ 요청 실패: {e}")

    # 4. 라우터 목록 확인
    print("\n4. 등록된 라우터 확인...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ API 문서 접근 가능: {base_url}/docs")
            print(f"      브라우저에서 확인하세요!")
        else:
            print(f"   응답 코드: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 요청 실패: {e}")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    test_account_sets_endpoint()
