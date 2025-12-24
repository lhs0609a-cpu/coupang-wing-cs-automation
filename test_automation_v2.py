"""
쿠팡윙 CS 자동화 V2 테스트 스크립트
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_server_health():
    """서버 상태 확인"""
    print_section("1. 서버 상태 확인")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 서버 상태: {data.get('status', 'unknown')}")
            print(f"   업타임: {data.get('uptime_seconds', 0):.0f}초")
            return True
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("\n서버가 실행 중인지 확인하세요:")
        print("  1. START.bat 실행")
        print("  2. 또는 python run_server.py")
        return False

def test_wing_web_status():
    """Wing Web 자동화 서비스 상태 확인"""
    print_section("2. Wing Web 자동화 서비스 확인")
    try:
        response = requests.get(f"{BASE_URL}/api/wing-web/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 서비스: {data.get('service')}")
            print(f"   상태: {data.get('status')}")
            print(f"\n   지원 기능:")
            for feature in data.get('features', []):
                print(f"   - {feature}")
            print(f"\n   필수 설정:")
            for req in data.get('requirements', []):
                print(f"   - {req}")
            return True
        else:
            print(f"❌ 서비스 상태 확인 실패: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
        return False

def test_login(headless=False):
    """로그인 테스트"""
    print_section("3. 로그인 테스트")
    print(f"   headless 모드: {headless}")
    print(f"   {'브라우저 창이 열립니다...' if not headless else '백그라운드에서 실행됩니다...'}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/wing-web/test-login",
            json={"headless": headless},
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ {data.get('message')}")
                return True
            else:
                print(f"❌ {data.get('message')}")
                return False
        else:
            print(f"❌ 로그인 테스트 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ 요청 시간 초과 (60초)")
        print("   .env 파일의 로그인 정보를 확인하세요")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
        return False

def test_auto_answer_v2(headless=False):
    """V2 자동 답변 테스트"""
    print_section("4. V2 자동 답변 실행")
    print(f"   headless 모드: {headless}")
    print(f"   {'브라우저 창이 열립니다...' if not headless else '백그라운드에서 실행됩니다...'}")
    print("\n   ⏳ 처리 중... (최대 5분 소요)")

    try:
        response = requests.post(
            f"{BASE_URL}/api/wing-web/auto-answer-v2",
            json={"headless": headless},
            timeout=300  # 5분
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ {data.get('message')}")

            stats = data.get('statistics', {})
            print(f"\n   📊 통계:")
            print(f"   - 총 문의 수: {stats.get('total_inquiries', 0)}")
            print(f"   - 답변 완료: {stats.get('answered', 0)}")
            print(f"   - 답변 실패: {stats.get('failed', 0)}")
            print(f"   - 건너뜀: {stats.get('skipped', 0)}")
            return True
        else:
            print(f"\n❌ 자동 답변 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("\n❌ 요청 시간 초과 (5분)")
        print("   문의가 많거나 서버가 느린 경우 발생할 수 있습니다")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 요청 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("  쿠팡윙 CS 자동화 V2 - 테스트 스크립트")
    print("="*60)

    # 사용자에게 headless 모드 선택
    print("\nheadless 모드를 선택하세요:")
    print("  1. headless=false (브라우저 창 보기 - 권장)")
    print("  2. headless=true (백그라운드 실행)")

    choice = input("\n선택 (1 또는 2, 기본값 1): ").strip()
    headless = (choice == "2")

    # 1. 서버 상태 확인
    if not test_server_health():
        print("\n❌ 서버가 실행되지 않았습니다. 종료합니다.")
        sys.exit(1)

    time.sleep(1)

    # 2. 서비스 상태 확인
    if not test_wing_web_status():
        print("\n❌ Wing Web 서비스를 사용할 수 없습니다. 종료합니다.")
        sys.exit(1)

    time.sleep(1)

    # 3. 로그인 테스트 (선택)
    print("\n로그인 테스트를 실행하시겠습니까? (y/n, 기본값 y): ", end="")
    do_login_test = input().strip().lower() != 'n'

    if do_login_test:
        if not test_login(headless):
            print("\n❌ 로그인에 실패했습니다.")
            print("\n.env 파일을 확인하세요:")
            print("  COUPANG_WING_USERNAME=your_username@email.com")
            print("  COUPANG_WING_PASSWORD=your_password")

            print("\n계속 진행하시겠습니까? (y/n, 기본값 n): ", end="")
            if input().strip().lower() != 'y':
                sys.exit(1)

        time.sleep(1)

    # 4. V2 자동 답변 실행 (선택)
    print("\nV2 자동 답변을 실행하시겠습니까? (y/n, 기본값 y): ", end="")
    do_auto_answer = input().strip().lower() != 'n'

    if do_auto_answer:
        if test_auto_answer_v2(headless):
            print("\n✅ 모든 테스트 완료!")
        else:
            print("\n❌ 자동 답변 실행 실패")
            sys.exit(1)
    else:
        print("\n✅ 테스트 완료 (자동 답변 생략)")

    print("\n" + "="*60)
    print("  테스트 종료")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
