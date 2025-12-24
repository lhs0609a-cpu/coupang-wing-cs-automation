"""
Coupang Wing Web Automation Service using Selenium
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
import time
from typing import List, Dict, Optional
from openai import OpenAI
from ..config import settings


class WingWebAutomation:
    """
    Coupang Wing Web Automation Service
    """

    def __init__(self, username: str, password: str, headless: bool = False):
        """
        Initialize the web automation service

        Args:
            username: Coupang Wing username
            password: Coupang Wing password
            headless: Run browser in headless mode
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.driver = None
        self.wait = None
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument('--headless')

            # Additional options for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # User agent
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)

            logger.info("WebDriver setup completed")
            return True
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {str(e)}")
            return False

    def login(self) -> bool:
        """
        Login to Coupang Wing

        Returns:
            bool: True if login successful
        """
        try:
            logger.info("Navigating to Coupang Wing login page...")
            # Navigate to wing.coupang.com - it will redirect to OAuth login
            self.driver.get("https://wing.coupang.com/")

            # Wait for redirect to OAuth login page (xauth.coupang.com)
            logger.info("Waiting for OAuth login page redirect...")
            time.sleep(3)

            # Try multiple possible selectors for username field
            logger.info("Entering username...")
            username_input = None
            try:
                # Try common OAuth/Keycloak selectors
                username_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
            except:
                try:
                    username_input = self.driver.find_element(By.NAME, "username")
                except:
                    try:
                        username_input = self.driver.find_element(By.ID, "login-email-input")
                    except:
                        username_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")

            if username_input:
                username_input.clear()
                username_input.send_keys(self.username)
                logger.info("Username entered")
            else:
                raise Exception("Could not find username input field")

            # Try multiple possible selectors for password field
            logger.info("Entering password...")
            password_input = None
            try:
                password_input = self.driver.find_element(By.ID, "password")
            except:
                try:
                    password_input = self.driver.find_element(By.NAME, "password")
                except:
                    try:
                        password_input = self.driver.find_element(By.ID, "login-password-input")
                    except:
                        password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            if password_input:
                password_input.clear()
                password_input.send_keys(self.password)
                logger.info("Password entered")
            else:
                raise Exception("Could not find password input field")

            # Click login button
            logger.info("Clicking login button...")
            login_button = None
            try:
                login_button = self.driver.find_element(By.ID, "kc-login")
            except:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                except:
                    try:
                        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    except:
                        login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '로그인')]")

            if login_button:
                login_button.click()
                logger.info("Login button clicked")
            else:
                raise Exception("Could not find login button")

            # Wait for login to complete
            logger.info("Waiting for login to complete...")
            time.sleep(5)

            # Check if login was successful by checking URL
            current_url = self.driver.current_url
            logger.info(f"Current URL after login: {current_url}")

            if "wing.coupang.com" in current_url and "xauth" not in current_url:
                logger.success("Login successful!")
                return True
            else:
                logger.error(f"Login failed - still at: {current_url}")
                # Take screenshot for debugging
                try:
                    self.driver.save_screenshot("login_failed.png")
                    logger.info("Screenshot saved as login_failed.png")
                except:
                    pass
                return False

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            # Take screenshot for debugging
            try:
                if self.driver:
                    self.driver.save_screenshot("login_error.png")
                    logger.info("Error screenshot saved as login_error.png")
            except:
                pass
            return False

    def navigate_to_inquiries(self) -> bool:
        """
        Navigate to product inquiries page

        Returns:
            bool: True if navigation successful
        """
        try:
            logger.info("Navigating to inquiries page...")
            self.driver.get("https://wing.coupang.com/tenants/cs/product/inquiries")
            time.sleep(3)

            logger.success("Navigated to inquiries page")
            return True
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return False

    def get_inquiries(self) -> List[Dict]:
        """
        Get all product inquiries from the page

        Returns:
            List of inquiry dictionaries with product name and question
        """
        inquiries = []

        try:
            logger.info("Fetching inquiries...")

            # Wait for the table to load
            time.sleep(3)

            # Find all inquiry rows
            rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr.tbody-tr")
            logger.info(f"Found {len(rows)} inquiry rows")

            for idx, row in enumerate(rows):
                try:
                    # Get product name
                    product_element = row.find_element(By.CSS_SELECTOR, "a[data-v-7fedaa82] span[data-v-7fedaa82]")
                    product_name = product_element.get_attribute("title") or product_element.text

                    # Get inquiry text (문의 내용)
                    inquiry_text_element = row.find_element(By.CSS_SELECTOR, "td[data-v-7fedaa82] div.text-overflow")
                    inquiry_text = inquiry_text_element.text

                    # Get answer button
                    answer_button = row.find_element(By.CSS_SELECTOR, "button[data-wuic-props*='답변하기']")

                    inquiries.append({
                        'index': idx,
                        'product_name': product_name.strip(),
                        'inquiry_text': inquiry_text.strip(),
                        'row_element': row,
                        'answer_button': answer_button
                    })

                    logger.info(f"Inquiry {idx + 1}: {product_name[:50]}... - {inquiry_text[:50]}...")

                except Exception as e:
                    logger.warning(f"Failed to parse inquiry row {idx}: {str(e)}")
                    continue

            logger.success(f"Successfully fetched {len(inquiries)} inquiries")
            return inquiries

        except Exception as e:
            logger.error(f"Error fetching inquiries: {str(e)}")
            return []

    def generate_answer(self, product_name: str, inquiry_text: str) -> str:
        """
        Generate answer using ChatGPT

        Args:
            product_name: Product name
            inquiry_text: Customer inquiry

        Returns:
            Generated answer text
        """
        try:
            logger.info(f"Generating answer for: {inquiry_text[:50]}...")

            prompt = f"""당신은 쿠팡 윙 셀러의 고객 서비스 담당자입니다.
아래 상품에 대한 고객 문의에 친절하고 전문적으로 답변해주세요.

상품명: {product_name}
고객 문의: {inquiry_text}

답변 작성 시 주의사항:
1. 존댓말을 사용하고 친절하게 작성
2. 상품에 대한 정확한 정보 제공
3. 고객의 질문에 직접적으로 답변
4. 필요시 추가 문의를 권유
5. 개인정보(전화번호, 이메일 등)를 요구하지 않음
6. 2000자 이내로 작성

답변:"""

            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 쿠팡 윙의 전문 고객 서비스 담당자입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            answer = response.choices[0].message.content.strip()
            logger.success(f"Generated answer: {answer[:100]}...")
            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"문의해 주셔서 감사합니다. 해당 내용은 담당자 확인 후 빠른 시일 내에 답변 드리겠습니다."

    def answer_inquiry(self, inquiry: Dict) -> bool:
        """
        Answer a single inquiry

        Args:
            inquiry: Inquiry dictionary

        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Answering inquiry {inquiry['index'] + 1}...")

            # Click answer button
            answer_button = inquiry['answer_button']
            self.driver.execute_script("arguments[0].scrollIntoView(true);", answer_button)
            time.sleep(1)
            answer_button.click()
            time.sleep(2)

            # Generate answer
            answer_text = self.generate_answer(inquiry['product_name'], inquiry['inquiry_text'])

            # Find textarea and enter answer
            textarea = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.input-textarea"))
            )
            textarea.clear()
            textarea.send_keys(answer_text)

            logger.info("Answer entered in textarea")
            time.sleep(1)

            # Find and click save button (저장하기)
            save_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '저장하기')]"))
            )
            save_button.click()

            logger.success(f"Successfully answered inquiry {inquiry['index'] + 1}")
            time.sleep(2)

            return True

        except Exception as e:
            logger.error(f"Error answering inquiry: {str(e)}")
            return False

    def process_all_inquiries(self) -> Dict:
        """
        Process all inquiries on the page

        Returns:
            Dictionary with processing results
        """
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }

        try:
            # Get all inquiries
            inquiries = self.get_inquiries()
            results['total'] = len(inquiries)

            if not inquiries:
                logger.warning("No inquiries found")
                return results

            # Process each inquiry
            for inquiry in inquiries:
                try:
                    success = self.answer_inquiry(inquiry)
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Inquiry {inquiry['index'] + 1}: Failed to answer")
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Inquiry {inquiry['index'] + 1}: {str(e)}")
                    logger.error(f"Error processing inquiry {inquiry['index'] + 1}: {str(e)}")

            logger.success(f"Processed {results['success']}/{results['total']} inquiries successfully")
            return results

        except Exception as e:
            logger.error(f"Error in process_all_inquiries: {str(e)}")
            results['errors'].append(str(e))
            return results

    def run_full_automation(self) -> Dict:
        """
        Run the full automation workflow:
        1. Setup driver
        2. Login
        3. Navigate to inquiries
        4. Process all inquiries

        Returns:
            Dictionary with results
        """
        results = {
            'success': False,
            'message': '',
            'statistics': {}
        }

        try:
            # Setup driver
            if not self.setup_driver():
                results['message'] = 'Failed to setup WebDriver'
                return results

            # Login
            if not self.login():
                results['message'] = 'Login failed'
                return results

            # Navigate to inquiries
            if not self.navigate_to_inquiries():
                results['message'] = 'Failed to navigate to inquiries page'
                return results

            # Process all inquiries
            stats = self.process_all_inquiries()
            results['statistics'] = stats
            results['success'] = True
            results['message'] = f"Successfully processed {stats['success']}/{stats['total']} inquiries"

            return results

        except Exception as e:
            logger.error(f"Error in run_full_automation: {str(e)}")
            results['message'] = f"Error: {str(e)}"
            return results
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up and close browser"""
        try:
            if self.driver:
                logger.info("Closing browser...")
                self.driver.quit()
                logger.success("Browser closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
