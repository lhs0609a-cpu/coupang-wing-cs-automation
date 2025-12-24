"""
쿠팡 윙 CS 자동화 V3 테스트 스크립트

실행 방법:
    python test_wing_automation_v3.py

설명:
    - 쿠팡 윙에 자동 로그인
    - 모든 시간대 탭 순회 (72시간~30일, 24~72시간, 24시간 이내)
    - 미답변 문의 자동 수집
    - ChatGPT로 답변 생성
    - 답변 자동 입력 및 저장
    - 모든 탭에 미답변이 없을 때까지 반복
"""

import sys
import os

# backend 폴더를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.wing_web_automation_v3 import WingWebAutomationV3
from app.config import settings


def print_banner():
    """배너 출력"""
    print()
    print("=" * 70)
    print("  🚀 쿠팡 윙 CS 자동화 V3 테스트")
    print("=" * 70)
    print()


def check_environment():
    """환경 변수 확인"""
    print("📋 환경 변수 확인 중...")
    print()

    username = settings.COUPANG_WING_USERNAME
    password = settings.COUPANG_WING_PASSWORD
    openai_key = settings.OPENAI_API_KEY

    if not username:
        print("❌ 오류: COUPANG_WING_USERNAME이 설정되지 않았습니다.")
        print("   .env 파일에 다음을 추가하세요:")
        print("   COUPANG_WING_USERNAME=your_username")
        return False

    if not password:
        print("❌ 오류: COUPANG_WING_PASSWORD가 설정되지 않았습니다.")
        print("   .env 파일에 다음을 추가하세요:")
        print("   COUPANG_WING_PASSWORD=your_password")
        return False

    if not openai_key:
        print("⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   ChatGPT 답변 생성이 불가능하며, 기본 답변이 사용됩니다.")
        print("   .env 파일에 다음을 추가하는 것을 권장합니다:")
        print("   OPENAI_API_KEY=sk-...")
        print()
        response = input("   계속 진행하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            return False

    print(f"✅ 사용자: {username}")
    print(f"✅ 비밀번호: {'*' * len(password)}")
    if openai_key:
        print(f"✅ OpenAI API 키: {openai_key[:10]}...")
        print(f"✅ OpenAI 모델: {settings.OPENAI_MODEL}")
    print()

    return True


def get_user_preferences():
    """사용자 설정 입력받기"""
    print("⚙️  실행 설정")
    print()

    # Headless 모드
    print("브라우저 화면 표시:")
    print("  1) 브라우저 화면 보임 (권장 - 디버깅 용이)")
    print("  2) 백그라운드 실행 (화면 숨김)")
    print()

    while True:
        choice = input("선택 (1 또는 2) [기본: 1]: ").strip()
        if choice == '' or choice == '1':
            headless = False
            break
        elif choice == '2':
            headless = True
            break
        else:
            print("❌ 잘못된 입력입니다. 1 또는 2를 입력하세요.")

    # 최대 반복 횟수
    print()
    print("최대 반복 횟수 (무한루프 방지):")
    while True:
        max_rounds_input = input("반복 횟수 [기본: 100]: ").strip()
        if max_rounds_input == '':
            max_rounds = 100
            break
        try:
            max_rounds = int(max_rounds_input)
            if max_rounds < 1:
                print("❌ 1 이상의 숫자를 입력하세요.")
                continue
            break
        except ValueError:
            print("❌ 숫자를 입력하세요.")

    print()
    print("─" * 70)
    print("설정 완료:")
    print(f"  - 브라우저 화면: {'보임' if not headless else '숨김'}")
    print(f"  - 최대 반복: {max_rounds}회")
    print("─" * 70)
    print()

    return headless, max_rounds


def run_automation(headless, max_rounds):
    """자동화 실행"""
    username = settings.COUPANG_WING_USERNAME
    password = settings.COUPANG_WING_PASSWORD

    print("🚀 자동화 시작...")
    print()

    # 자동화 인스턴스 생성
    automation = WingWebAutomationV3(
        username=username,
        password=password,
        headless=headless,
        max_rounds=max_rounds
    )

    try:
        # 실행
        results = automation.run_full_automation_loop()

        # 결과 출력
        print()
        print("=" * 70)
        if results['success']:
            print("✅ 자동화 완료!")
        else:
            print("❌ 자동화 실패")
        print("=" * 70)
        print()
        print(f"📊 결과:")
        print(f"  - 성공 여부: {results['success']}")
        print(f"  - 메시지: {results['message']}")
        print()

        if 'statistics' in results:
            stats = results['statistics']
            print(f"📈 통계:")
            print(f"  - 총 라운드: {stats.get('total_rounds', 0)}")
            print(f"  - 총 문의 수: {stats.get('total_inquiries', 0)}")
            print(f"  - 답변 완료: {stats.get('answered', 0)}")
            print(f"  - 답변 실패: {stats.get('failed', 0)}")
            print(f"  - 건너뜀: {stats.get('skipped', 0)}")

            if stats.get('total_inquiries', 0) > 0:
                success_rate = (stats.get('answered', 0) / stats.get('total_inquiries', 1)) * 100
                print(f"  - 성공률: {success_rate:.1f}%")

        print()
        print("=" * 70)

        return results['success']

    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  사용자에 의해 중단되었습니다.")
        automation.cleanup()
        return False

    except Exception as e:
        print()
        print(f"❌ 오류 발생: {str(e)}")
        automation.cleanup()
        return False


def main():
    """메인 함수"""
    try:
        # 배너 출력
        print_banner()

        # 환경 변수 확인
        if not check_environment():
            print()
            print("❌ 환경 변수 설정을 완료한 후 다시 실행하세요.")
            return

        # 사용자 설정
        headless, max_rounds = get_user_preferences()

        # 최종 확인
        print("자동화를 시작합니다.")
        print()
        print("⚠️  주의사항:")
        print("  - 자동화가 진행되는 동안 브라우저를 조작하지 마세요")
        print("  - 네트워크 연결이 안정적인지 확인하세요")
        print("  - 중단하려면 Ctrl+C를 누르세요")
        print()

        input("계속하려면 Enter 키를 누르세요...")
        print()

        # 자동화 실행
        success = run_automation(headless, max_rounds)

        # 종료 메시지
        print()
        if success:
            print("✅ 프로그램이 정상적으로 종료되었습니다.")
        else:
            print("⚠️  프로그램이 오류로 인해 종료되었습니다.")
            print("   로그 파일을 확인하세요: logs/app.log")
            print("   스크린샷을 확인하세요: error_*.png")

    except Exception as e:
        print()
        print(f"❌ 예상치 못한 오류: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        print()
        input("종료하려면 Enter 키를 누르세요...")


if __name__ == "__main__":
    main()
