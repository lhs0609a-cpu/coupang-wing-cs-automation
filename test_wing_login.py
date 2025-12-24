"""
쿠팡 윙 로그인 테스트 스크립트
실제로 브라우저를 열어서 로그인을 시도합니다.
"""
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_login(username, password):
    """쿠팡 윙 로그인 테스트"""
    driver = None
    try:
        print("=" * 60)
        print("쿠팡 윙 로그인 테스트 시작")
        print("=" * 60)

        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--window-size=1920,1080')

        print("\n[1/5] Chrome 드라이버 설정 중...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 20)
        print("✅ Chrome 드라이버 설정 완료")

        print("\n[2/5] 쿠팡 윙 사이트 접속 중...")
        driver.get("https://wing.coupang.com/")
        time.sleep(3)
        print(f"✅ 현재 URL: {driver.current_url}")

        print("\n[3/5] 로그인 페이지로 리디렉트 확인...")
        if "xauth.coupang.com" in driver.current_url:
            print("✅ OAuth 로그인 페이지로 리디렉트됨")
        else:
            print(f"⚠️  예상치 못한 URL: {driver.current_url}")

        print("\n[4/5] 로그인 정보 입력 중...")

        # Username 입력
        try:
            username_input = wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_input.clear()
            username_input.send_keys(username)
            print(f"✅ 아이디 입력: {username}")
        except Exception as e:
            print(f"❌ 아이디 입력 실패: {str(e)}")
            # 페이지 소스 일부 출력
            print("\n페이지에서 찾은 input 요소들:")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs[:5]:
                print(f"  - type: {inp.get_attribute('type')}, id: {inp.get_attribute('id')}, name: {inp.get_attribute('name')}")
            raise

        # Password 입력
        try:
            password_input = driver.find_element(By.ID, "password")
            password_input.clear()
            password_input.send_keys(password)
            print("✅ 비밀번호 입력 완료")
        except Exception as e:
            print(f"❌ 비밀번호 입력 실패: {str(e)}")
            raise

        # 로그인 버튼 클릭
        try:
            login_button = driver.find_element(By.ID, "kc-login")
            print("✅ 로그인 버튼 찾음")
            login_button.click()
            print("✅ 로그인 버튼 클릭")
        except Exception as e:
            print(f"❌ 로그인 버튼 클릭 실패: {str(e)}")
            # 버튼 찾기
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"\n페이지에서 찾은 버튼들 ({len(buttons)}개):")
            for btn in buttons[:5]:
                print(f"  - text: {btn.text}, id: {btn.get_attribute('id')}, class: {btn.get_attribute('class')}")
            raise

        print("\n[5/5] 로그인 완료 대기 중...")
        time.sleep(5)

        current_url = driver.current_url
        print(f"\n최종 URL: {current_url}")

        if "wing.coupang.com" in current_url and "xauth" not in current_url:
            print("\n" + "=" * 60)
            print("✅ ✅ ✅ 로그인 성공! ✅ ✅ ✅")
            print("=" * 60)
            print(f"현재 페이지 제목: {driver.title}")
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ ❌ ❌ 로그인 실패 ❌ ❌ ❌")
            print("=" * 60)
            print(f"예상: wing.coupang.com")
            print(f"실제: {current_url}")

            # 스크린샷 저장
            screenshot_path = "login_failed_test.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n스크린샷 저장: {screenshot_path}")
            return False

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ 오류 발생: {str(e)}")
        print("=" * 60)
        if driver:
            try:
                driver.save_screenshot("login_error_test.png")
                print("스크린샷 저장: login_error_test.png")
            except:
                pass
        return False

    finally:
        if driver:
            print("\n브라우저를 10초 후에 닫습니다... (확인하시려면 브라우저를 보세요)")
            time.sleep(10)
            driver.quit()
            print("✅ 브라우저 종료")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("사용법: python test_wing_login.py <아이디> <비밀번호>")
        print("\n예시:")
        print('  python test_wing_login.py myusername mypassword')
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    success = test_login(username, password)
    sys.exit(0 if success else 1)
