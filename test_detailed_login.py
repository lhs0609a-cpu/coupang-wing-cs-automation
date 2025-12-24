"""
쿠팡 윙 로그인 상세 테스트 스크립트
각 단계별로 정확한 문제점을 파악합니다.
"""
import os
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / 'backend' / '.env'
load_dotenv(env_path)

class LoginTester:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.wait = None
        self.errors = []
        self.warnings = []
        self.success_steps = []

    def log_success(self, step, message):
        """성공 로그"""
        msg = f"✅ [{step}] {message}"
        print(msg)
        self.success_steps.append(msg)

    def log_error(self, step, message, exception=None):
        """에러 로그"""
        msg = f"❌ [{step}] {message}"
        if exception:
            msg += f"\n   상세: {str(exception)}"
        print(msg)
        self.errors.append(msg)

    def log_warning(self, step, message):
        """경고 로그"""
        msg = f"⚠️  [{step}] {message}"
        print(msg)
        self.warnings.append(msg)

    def log_info(self, message):
        """정보 로그"""
        print(f"ℹ️  {message}")

    def setup_driver(self):
        """1단계: 크롬 드라이버 설정"""
        print("\n" + "="*80)
        print("1단계: 크롬 드라이버 설정")
        print("="*80)

        try:
            chrome_options = Options()
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')

            self.log_info("ChromeDriver 다운로드 및 설치 중...")
            service = Service(ChromeDriverManager().install())

            self.log_info("Chrome 브라우저 시작 중...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)

            self.log_success("1단계", "크롬 드라이버 설정 완료")
            return True

        except Exception as e:
            self.log_error("1단계", "크롬 드라이버 설정 실패", e)
            return False

    def navigate_to_site(self):
        """2단계: 쿠팡 윙 사이트 접속"""
        print("\n" + "="*80)
        print("2단계: 쿠팡 윙 사이트 접속")
        print("="*80)

        try:
            self.log_info("https://wing.coupang.com/ 접속 중...")
            self.driver.get("https://wing.coupang.com/")
            time.sleep(3)

            current_url = self.driver.current_url
            self.log_info(f"현재 URL: {current_url}")

            if "xauth.coupang.com" in current_url:
                self.log_success("2단계", "OAuth 로그인 페이지로 정상 리디렉트됨")
                return True
            elif "wing.coupang.com" in current_url:
                self.log_warning("2단계", "이미 로그인되어 있을 수 있습니다")
                return True
            else:
                self.log_error("2단계", f"예상치 못한 URL로 리디렉트: {current_url}")
                return False

        except Exception as e:
            self.log_error("2단계", "사이트 접속 실패", e)
            return False

    def analyze_login_page(self):
        """3단계: 로그인 페이지 분석"""
        print("\n" + "="*80)
        print("3단계: 로그인 페이지 분석")
        print("="*80)

        try:
            self.log_info("페이지 제목: " + self.driver.title)

            # 모든 input 요소 찾기
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            self.log_info(f"찾은 input 요소: {len(inputs)}개")

            for i, inp in enumerate(inputs[:10], 1):
                input_type = inp.get_attribute('type') or 'text'
                input_id = inp.get_attribute('id') or '(없음)'
                input_name = inp.get_attribute('name') or '(없음)'
                input_placeholder = inp.get_attribute('placeholder') or '(없음)'
                print(f"  {i}. type={input_type}, id={input_id}, name={input_name}, placeholder={input_placeholder}")

            # 모든 button 요소 찾기
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            self.log_info(f"찾은 button 요소: {len(buttons)}개")

            for i, btn in enumerate(buttons[:5], 1):
                btn_text = btn.text or '(텍스트 없음)'
                btn_id = btn.get_attribute('id') or '(없음)'
                btn_type = btn.get_attribute('type') or '(없음)'
                print(f"  {i}. text={btn_text}, id={btn_id}, type={btn_type}")

            self.log_success("3단계", "로그인 페이지 분석 완료")
            return True

        except Exception as e:
            self.log_error("3단계", "페이지 분석 실패", e)
            return False

    def enter_credentials(self):
        """4단계: 로그인 정보 입력"""
        print("\n" + "="*80)
        print("4단계: 로그인 정보 입력")
        print("="*80)

        # Username 입력 시도
        username_success = False
        selectors = [
            ("ID", By.ID, "username"),
            ("NAME", By.NAME, "username"),
            ("ID", By.ID, "login-email-input"),
            ("CSS", By.CSS_SELECTOR, "input[type='text']"),
            ("CSS", By.CSS_SELECTOR, "input[type='email']"),
        ]

        for selector_name, selector_type, selector_value in selectors:
            try:
                self.log_info(f"아이디 입력란 찾기 시도: {selector_name}='{selector_value}'")
                username_input = self.wait.until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                username_input.clear()
                username_input.send_keys(self.username)
                self.log_success("4단계-1", f"아이디 입력 성공 (방법: {selector_name})")
                username_success = True
                break
            except Exception as e:
                self.log_info(f"  실패: {str(e)[:100]}")
                continue

        if not username_success:
            self.log_error("4단계-1", "아이디 입력란을 찾을 수 없습니다")
            return False

        # Password 입력 시도
        password_success = False
        selectors = [
            ("ID", By.ID, "password"),
            ("NAME", By.NAME, "password"),
            ("ID", By.ID, "login-password-input"),
            ("CSS", By.CSS_SELECTOR, "input[type='password']"),
        ]

        for selector_name, selector_type, selector_value in selectors:
            try:
                self.log_info(f"비밀번호 입력란 찾기 시도: {selector_name}='{selector_value}'")
                password_input = self.driver.find_element(selector_type, selector_value)
                password_input.clear()
                password_input.send_keys(self.password)
                self.log_success("4단계-2", f"비밀번호 입력 성공 (방법: {selector_name})")
                password_success = True
                break
            except Exception as e:
                self.log_info(f"  실패: {str(e)[:100]}")
                continue

        if not password_success:
            self.log_error("4단계-2", "비밀번호 입력란을 찾을 수 없습니다")
            return False

        self.log_success("4단계", "로그인 정보 입력 완료")
        return True

    def click_login_button(self):
        """5단계: 로그인 버튼 클릭"""
        print("\n" + "="*80)
        print("5단계: 로그인 버튼 클릭")
        print("="*80)

        selectors = [
            ("ID", By.ID, "kc-login"),
            ("CSS", By.CSS_SELECTOR, "input[type='submit']"),
            ("CSS", By.CSS_SELECTOR, "button[type='submit']"),
            ("XPATH", By.XPATH, "//button[contains(text(), '로그인')]"),
            ("XPATH", By.XPATH, "//input[@value='로그인']"),
        ]

        for selector_name, selector_type, selector_value in selectors:
            try:
                self.log_info(f"로그인 버튼 찾기 시도: {selector_name}='{selector_value}'")
                login_button = self.driver.find_element(selector_type, selector_value)
                login_button.click()
                self.log_success("5단계", f"로그인 버튼 클릭 성공 (방법: {selector_name})")
                return True
            except Exception as e:
                self.log_info(f"  실패: {str(e)[:100]}")
                continue

        self.log_error("5단계", "로그인 버튼을 찾을 수 없습니다")
        return False

    def verify_login(self):
        """6단계: 로그인 성공 확인"""
        print("\n" + "="*80)
        print("6단계: 로그인 성공 확인")
        print("="*80)

        try:
            self.log_info("로그인 처리 대기 중... (5초)")
            time.sleep(5)

            current_url = self.driver.current_url
            page_title = self.driver.title

            self.log_info(f"최종 URL: {current_url}")
            self.log_info(f"페이지 제목: {page_title}")

            if "wing.coupang.com" in current_url and "xauth" not in current_url:
                self.log_success("6단계", "로그인 성공! wing.coupang.com으로 정상 접속됨")
                return True
            elif "xauth.coupang.com" in current_url:
                self.log_error("6단계", "로그인 실패 - 아직 로그인 페이지에 있습니다")
                self.log_info("가능한 원인:")
                self.log_info("  1. 아이디 또는 비밀번호가 틀렸습니다")
                self.log_info("  2. CAPTCHA 또는 추가 인증이 필요합니다")
                self.log_info("  3. 계정이 잠겼거나 제한되었습니다")

                # 에러 메시지 확인
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error'], [class*='alert']")
                    if error_elements:
                        self.log_info("페이지에서 발견된 에러 메시지:")
                        for elem in error_elements[:3]:
                            if elem.text:
                                print(f"    - {elem.text}")
                except:
                    pass

                return False
            else:
                self.log_warning("6단계", f"예상치 못한 페이지로 이동: {current_url}")
                return False

        except Exception as e:
            self.log_error("6단계", "로그인 확인 중 오류 발생", e)
            return False

    def save_screenshot(self, filename="login_test_result.png"):
        """스크린샷 저장"""
        try:
            if self.driver:
                filepath = os.path.join(os.getcwd(), filename)
                self.driver.save_screenshot(filepath)
                self.log_info(f"스크린샷 저장: {filepath}")
        except Exception as e:
            self.log_warning("스크린샷", f"저장 실패: {str(e)}")

    def print_summary(self):
        """최종 결과 요약"""
        print("\n" + "="*80)
        print("테스트 결과 요약")
        print("="*80)

        print(f"\n✅ 성공한 단계: {len(self.success_steps)}개")
        for step in self.success_steps:
            print(f"  {step}")

        if self.warnings:
            print(f"\n⚠️  경고: {len(self.warnings)}개")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.errors:
            print(f"\n❌ 오류: {len(self.errors)}개")
            for error in self.errors:
                print(f"  {error}")

        print("\n" + "="*80)
        if not self.errors:
            print("🎉 전체 테스트 성공!")
        else:
            print("💥 테스트 실패 - 위의 오류를 확인하세요")
        print("="*80)

    def run_test(self):
        """전체 테스트 실행"""
        try:
            print("\n" + "#"*80)
            print("# 쿠팡 윙 로그인 상세 테스트")
            print("#"*80)
            print(f"아이디: {self.username}")
            print(f"비밀번호: {'*' * len(self.password)}")

            if not self.setup_driver():
                return False

            if not self.navigate_to_site():
                self.save_screenshot("error_step2_navigate.png")
                return False

            if not self.analyze_login_page():
                self.save_screenshot("error_step3_analyze.png")
                return False

            if not self.enter_credentials():
                self.save_screenshot("error_step4_credentials.png")
                return False

            if not self.click_login_button():
                self.save_screenshot("error_step5_button.png")
                return False

            success = self.verify_login()

            if success:
                self.save_screenshot("success_logged_in.png")
            else:
                self.save_screenshot("error_step6_verify.png")

            self.log_info("\n브라우저를 15초간 유지합니다 (확인하세요)...")
            time.sleep(15)

            return success

        except KeyboardInterrupt:
            self.log_warning("테스트", "사용자가 중단했습니다")
            return False
        except Exception as e:
            self.log_error("테스트", "예기치 않은 오류 발생", e)
            self.save_screenshot("error_unexpected.png")
            return False
        finally:
            self.print_summary()
            if self.driver:
                self.log_info("브라우저 종료 중...")
                self.driver.quit()

def main():
    # .env 파일에서 계정 정보 읽기
    username = os.getenv('COUPANG_WING_USERNAME')
    password = os.getenv('COUPANG_WING_PASSWORD')

    # 명령행 인자가 있으면 그것을 우선 사용
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]

    if not username or not password or username == 'your_email_here' or password == 'your_password_here':
        print("❌ 오류: 계정 정보가 설정되지 않았습니다\n")
        print("방법 1: 명령행 인자로 전달")
        print("  python test_detailed_login.py <아이디> <비밀번호>\n")
        print("방법 2: backend/.env 파일에 설정")
        print("  COUPANG_WING_USERNAME=your_username")
        print("  COUPANG_WING_PASSWORD=your_password")
        return 1

    tester = LoginTester(username, password)
    success = tester.run_test()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
