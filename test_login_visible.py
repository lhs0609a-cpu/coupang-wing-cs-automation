"""
간단한 쿠팡 윙 로그인 테스트 (브라우저 표시)
실제 브라우저를 띄워서 로그인 과정을 보여줍니다.

사용법:
  python test_login_visible.py <아이디> <비밀번호>
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


def test_visible_login(username, password):
    """브라우저를 띄워서 로그인 테스트"""
    driver = None
    try:
        print("\n" + "="*60)
        print("쿠팡 윙 로그인 테스트 (브라우저 표시)")
        print("="*60)
        print(f"아이디: {username}")
        print("="*60 + "\n")

        # Chrome 옵션 (헤드리스 모드 OFF - 브라우저가 보임)
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')

        print("[1/5] Chrome 드라이버 설정 중...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 20)
        print("✅ Chrome 드라이버 설정 완료\n")

        print("[2/5] 쿠팡 윙 사이트 접속 중...")
        print("https://wing.coupang.com/ 으로 이동합니다...")
        driver.get("https://wing.coupang.com/")
        time.sleep(3)
        print(f"✅ 현재 URL: {driver.current_url}\n")

        print("[3/5] 로그인 페이지 확인...")
        if "xauth.coupang.com" in driver.current_url:
            print("✅ OAuth 로그인 페이지로 정상 리디렉트됨\n")
        else:
            print(f"⚠️  예상과 다른 URL: {driver.current_url}\n")

        print("[4/5] 로그인 정보 입력 중...")

        # Username 입력
        print("  - 아이디 입력 중...")
        username_input = wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_input.clear()
        username_input.send_keys(username)
        print(f"  ✅ 아이디 입력 완료: {username}")

        # Password 입력
        print("  - 비밀번호 입력 중...")
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(password)
        print("  ✅ 비밀번호 입력 완료\n")

        # 로그인 버튼 클릭
        print("[5/5] 로그인 버튼 클릭...")
        login_button = driver.find_element(By.ID, "kc-login")
        login_button.click()
        print("✅ 로그인 버튼 클릭 완료\n")

        print("로그인 처리 중... (잠시 기다려주세요)")
        time.sleep(5)

        current_url = driver.current_url
        print(f"최종 URL: {current_url}")
        print(f"페이지 제목: {driver.title}\n")

        if "wing.coupang.com" in current_url and "xauth" not in current_url:
            print("\n" + "="*60)
            print("✅ ✅ ✅ 로그인 성공! ✅ ✅ ✅")
            print("="*60)
            print("\n브라우저를 30초간 유지합니다...")
            print("(쿠팡 윙 페이지를 확인하세요)\n")
            time.sleep(30)
            return True
        else:
            print("\n" + "="*60)
            print("❌ 로그인 실패")
            print("="*60)
            print("\n가능한 원인:")
            print("  1. 아이디 또는 비밀번호가 틀렸습니다")
            print("  2. CAPTCHA 또는 추가 인증이 필요합니다")
            print("  3. 계정이 잠겼거나 제한되었습니다\n")
            print("브라우저를 30초간 유지합니다...")
            print("(로그인 페이지에서 문제를 확인하세요)\n")
            time.sleep(30)
            return False

    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ 오류 발생: {str(e)}")
        print("="*60)
        if driver:
            print("\n브라우저를 20초간 유지합니다...")
            print("(오류 상황을 확인하세요)\n")
            time.sleep(20)
        return False

    finally:
        if driver:
            print("브라우저를 종료합니다...")
            driver.quit()
            print("✅ 완료\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("="*60)
        print("쿠팡 윙 로그인 테스트")
        print("="*60)
        print("\n사용법:")
        print("  python test_login_visible.py <아이디> <비밀번호>")
        print("\n예시:")
        print("  python test_login_visible.py my_username my_password")
        print("\n주의:")
        print("  - 브라우저가 자동으로 열립니다")
        print("  - 로그인 과정을 직접 볼 수 있습니다")
        print("  - 테스트가 끝나면 브라우저가 자동으로 닫힙니다\n")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    success = test_visible_login(username, password)
    sys.exit(0 if success else 1)
