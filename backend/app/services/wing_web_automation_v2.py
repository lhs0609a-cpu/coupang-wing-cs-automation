"""
Coupang Wing Web Automation Service V2 - 실제 HTML 구조 기반
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from loguru import logger
import time
from typing import List, Dict, Optional
from openai import OpenAI
from ..config import settings


class WingWebAutomationV2:
    """
    쿠팡윙 고객문의 자동 응답 시스템 V2
    실제 HTML 구조에 맞춰 구현
    """

    # 시간대별 탭 정의
    TIME_RANGES = [
        "72시간~30일",
        "24~72시간",
        "24시간 이내"
    ]

    def __init__(self, username: str, password: str, headless: bool = False):
        """
        초기화

        Args:
            username: 쿠팡윙 아이디
            password: 쿠팡윙 비밀번호
            headless: 백그라운드 실행 여부
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.driver = None
        self.wait = None
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

        # 통계
        self.total_inquiries = 0
        self.answered_count = 0
        self.failed_count = 0
        self.skipped_count = 0

    def setup_driver(self):
        """웹드라이버 설정"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument('--headless')

            # 안정성을 위한 옵션
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # User agent
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)

            logger.info("✅ 웹드라이버 설정 완료")
            return True
        except Exception as e:
            logger.error(f"❌ 웹드라이버 설정 실패: {str(e)}")
            return False

    def login(self) -> bool:
        """쿠팡윙 로그인"""
        try:
            logger.info("🔐 쿠팡윙 로그인 시작...")

            # 로그인 페이지로 이동
            self.driver.get("https://wing.coupang.com/")
            time.sleep(3)

            # 아이디 입력
            logger.info("  📝 아이디 입력...")
            username_input = None
            try:
                username_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
            except:
                try:
                    username_input = self.driver.find_element(By.NAME, "username")
                except:
                    username_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")

            username_input.clear()
            username_input.send_keys(self.username)
            logger.info("  ✅ 아이디 입력 완료")

            # 비밀번호 입력
            logger.info("  📝 비밀번호 입력...")
            password_input = None
            try:
                password_input = self.driver.find_element(By.ID, "password")
            except:
                try:
                    password_input = self.driver.find_element(By.NAME, "password")
                except:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            password_input.clear()
            password_input.send_keys(self.password)
            logger.info("  ✅ 비밀번호 입력 완료")

            # 로그인 버튼 클릭
            logger.info("  🖱️  로그인 버튼 클릭...")
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

            login_button.click()
            logger.info("  ✅ 로그인 버튼 클릭 완료")

            # 로그인 완료 대기
            logger.info("  ⏳ 로그인 처리 중...")
            time.sleep(5)

            # 로그인 성공 확인
            current_url = self.driver.current_url
            if "wing.coupang.com" in current_url and "xauth" not in current_url:
                logger.success("✅ 로그인 성공!")
                return True
            else:
                logger.error(f"❌ 로그인 실패 - 현재 URL: {current_url}")
                self.driver.save_screenshot("login_failed.png")
                return False

        except Exception as e:
            logger.error(f"❌ 로그인 오류: {str(e)}")
            if self.driver:
                self.driver.save_screenshot("login_error.png")
            return False

    def navigate_to_inquiries(self) -> bool:
        """고객문의 페이지로 이동"""
        try:
            logger.info("📋 고객문의 페이지로 이동...")
            self.driver.get("https://wing.coupang.com/tenants/cs/product/inquiries")
            time.sleep(3)
            logger.success("✅ 고객문의 페이지 이동 완료")
            return True
        except Exception as e:
            logger.error(f"❌ 페이지 이동 오류: {str(e)}")
            return False

    def check_tab_for_inquiries(self, tab_name: str) -> bool:
        """
        특정 시간대 탭에 문의가 있는지 확인

        Args:
            tab_name: 탭 이름 (예: "24시간 이내")

        Returns:
            bool: 문의가 있으면 True
        """
        try:
            logger.info(f"  🔍 '{tab_name}' 탭 확인 중...")

            # 탭 찾기 및 클릭
            tabs = self.driver.find_elements(By.CSS_SELECTOR, "button, a, div[role='tab']")
            tab_found = False

            for tab in tabs:
                if tab_name in tab.text:
                    tab.click()
                    time.sleep(2)
                    tab_found = True
                    logger.info(f"  ✅ '{tab_name}' 탭 클릭 완료")
                    break

            if not tab_found:
                logger.warning(f"  ⚠️  '{tab_name}' 탭을 찾을 수 없음")
                return False

            # 문의 행 찾기
            inquiry_rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "td.replying-no-comments, td[data-v-7fedaa82]"
            )

            if inquiry_rows and len(inquiry_rows) > 0:
                logger.info(f"  ✅ '{tab_name}' 탭에 {len(inquiry_rows)}개 문의 발견!")
                return True
            else:
                logger.info(f"  ℹ️  '{tab_name}' 탭에 문의 없음")
                return False

        except Exception as e:
            logger.error(f"  ❌ 탭 확인 오류: {str(e)}")
            return False

    def get_all_inquiries_in_current_tab(self) -> List[Dict]:
        """
        현재 탭의 모든 문의 수집

        Returns:
            List[Dict]: 문의 정보 리스트
        """
        inquiries = []

        try:
            logger.info("    📥 문의 수집 중...")
            time.sleep(2)

            # 모든 문의 행 찾기
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "td.replying-no-comments, td[class*='replying']"
            )

            logger.info(f"    📊 총 {len(rows)}개 행 발견")

            for idx, row in enumerate(rows):
                try:
                    # 상품명 찾기
                    product_name = None
                    try:
                        product_elem = row.find_element(By.CSS_SELECTOR, "div.product-name a span")
                        product_name = product_elem.get_attribute("title") or product_elem.text
                    except:
                        try:
                            product_elem = row.find_element(By.CSS_SELECTOR, "div.text-wrapper a span")
                            product_name = product_elem.get_attribute("title") or product_elem.text
                        except:
                            logger.debug(f"      Row {idx}: 상품명 없음")
                            continue

                    # 문의 내용 찾기
                    inquiry_text = None
                    try:
                        inquiry_elem = row.find_element(By.CSS_SELECTOR, "span.inquiry-content")
                        inquiry_text = inquiry_elem.text.strip()
                    except:
                        try:
                            inquiry_elem = row.find_element(By.CSS_SELECTOR, "div span")
                            inquiry_text = inquiry_elem.text.strip()
                        except:
                            logger.debug(f"      Row {idx}: 문의내용 없음")
                            continue

                    # 답변하기 버튼 찾기
                    answer_button = None
                    try:
                        buttons = row.find_elements(By.CSS_SELECTOR, "button")
                        for btn in buttons:
                            if "답변하기" in btn.text or "reply" in btn.get_attribute("class").lower():
                                answer_button = btn
                                break
                    except:
                        logger.debug(f"      Row {idx}: 답변하기 버튼 없음")
                        continue

                    if product_name and inquiry_text and answer_button:
                        inquiries.append({
                            "product_name": product_name,
                            "inquiry": inquiry_text,
                            "answer_button": answer_button,
                            "row": row
                        })
                        logger.info(f"      ✅ 문의 {len(inquiries)}: {product_name[:30]}...")

                except StaleElementReferenceException:
                    logger.debug(f"      Row {idx}: Stale element, skipping")
                    continue
                except Exception as e:
                    logger.debug(f"      Row {idx}: 오류 - {str(e)}")
                    continue

            logger.success(f"    ✅ 총 {len(inquiries)}개 유효한 문의 수집 완료")
            return inquiries

        except Exception as e:
            logger.error(f"    ❌ 문의 수집 오류: {str(e)}")
            return []

    def generate_answer_with_gpt(self, product_name: str, inquiry: str) -> str:
        """
        ChatGPT로 답변 생성

        Args:
            product_name: 상품명
            inquiry: 문의 내용

        Returns:
            str: 생성된 답변
        """
        try:
            logger.info("      🤖 ChatGPT 답변 생성 중...")

            if not self.openai_client:
                logger.warning("      ⚠️  OpenAI API 키 없음, 기본 답변 사용")
                return f"안녕하세요. '{product_name}' 관련 문의 주셔서 감사합니다. 빠른 시일 내에 확인 후 답변 드리겠습니다. 감사합니다."

            prompt = f"""
당신은 쿠팡 판매자의 CS 담당자입니다.
다음 상품의 고객 문의에 대해 친절하고 전문적인 답변을 작성해주세요.

상품명: {product_name}
고객 문의: {inquiry}

답변 작성 가이드:
1. 정중하고 친절한 말투 사용
2. 고객의 문의에 정확하게 답변
3. 필요시 추가 정보 요청 또는 안내
4. 200자 이내로 간결하게 작성
5. 개인정보(전화번호, 이메일)를 요구하지 말 것
6. 판매자 연락처로 연락 가능하다는 안내 포함

답변:
"""

            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "당신은 전문적이고 친절한 쿠팡 판매자 CS 담당자입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )

            answer = response.choices[0].message.content.strip()
            logger.success(f"      ✅ ChatGPT 답변 생성 완료 ({len(answer)}자)")
            return answer

        except Exception as e:
            logger.error(f"      ❌ ChatGPT 답변 생성 오류: {str(e)}")
            # 기본 답변 반환
            return f"안녕하세요. '{product_name}' 관련 문의 주셔서 감사합니다. 빠른 시일 내에 확인 후 답변 드리겠습니다. 감사합니다."

    def answer_inquiry(self, inquiry_data: Dict) -> bool:
        """
        문의에 답변

        Args:
            inquiry_data: 문의 정보 딕셔너리

        Returns:
            bool: 성공 여부
        """
        try:
            product_name = inquiry_data["product_name"]
            inquiry_text = inquiry_data["inquiry"]
            answer_button = inquiry_data["answer_button"]

            logger.info(f"    💬 답변 작성 시작: {product_name[:30]}...")

            # 1. 답변하기 버튼 클릭
            logger.info("      🖱️  답변하기 버튼 클릭...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", answer_button)
            time.sleep(1)
            answer_button.click()
            time.sleep(2)

            # 2. 답변 생성
            answer_text = self.generate_answer_with_gpt(product_name, inquiry_text)

            # 3. 답변 입력란 찾기
            logger.info("      📝 답변 입력란 찾는 중...")
            textarea = None
            try:
                textarea = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.input-textarea"))
                )
            except:
                try:
                    textarea = self.driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='상품문의']")
                except:
                    textarea = self.driver.find_element(By.TAG_NAME, "textarea")

            if not textarea:
                logger.error("      ❌ 답변 입력란을 찾을 수 없음")
                return False

            # 4. 답변 입력
            logger.info("      ✍️  답변 입력 중...")
            textarea.clear()
            textarea.send_keys(answer_text)
            time.sleep(1)
            logger.success(f"      ✅ 답변 입력 완료 ({len(answer_text)}자)")

            # 5. 저장하기 버튼 찾기 및 클릭
            logger.info("      💾 저장하기 버튼 찾는 중...")
            save_button = None
            try:
                # "저장하기" 텍스트가 있는 버튼 찾기
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if "저장하기" in btn.text or "저장" in btn.text:
                        save_button = btn
                        break

                if not save_button:
                    # data-wuic-props에 "type:primary"가 있는 버튼 찾기
                    save_button = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button[data-wuic-props*='type:primary']"
                    )
            except:
                logger.error("      ❌ 저장하기 버튼을 찾을 수 없음")
                return False

            # 6. 저장하기 클릭
            logger.info("      🖱️  저장하기 버튼 클릭...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
            time.sleep(1)
            save_button.click()
            time.sleep(3)

            logger.success("    ✅ 답변 저장 완료!")
            self.answered_count += 1
            return True

        except Exception as e:
            logger.error(f"    ❌ 답변 작성 오류: {str(e)}")
            self.failed_count += 1

            # 오류 스크린샷 저장
            try:
                self.driver.save_screenshot(f"error_answer_{time.time()}.png")
            except:
                pass

            return False

    def process_all_tabs(self) -> Dict:
        """
        모든 시간대 탭을 순회하며 문의 처리

        Returns:
            Dict: 처리 결과 통계
        """
        logger.info("🔄 모든 탭 순회 시작...")

        has_any_inquiry = False

        for tab_name in self.TIME_RANGES:
            logger.info(f"\n{'='*60}")
            logger.info(f"📂 [{tab_name}] 탭 처리 중...")
            logger.info(f"{'='*60}")

            # 탭에 문의가 있는지 확인
            if not self.check_tab_for_inquiries(tab_name):
                logger.info(f"  ℹ️  [{tab_name}] 탭에 문의 없음, 다음 탭으로...")
                continue

            has_any_inquiry = True

            # 현재 탭의 모든 문의 수집
            inquiries = self.get_all_inquiries_in_current_tab()
            self.total_inquiries += len(inquiries)

            if not inquiries:
                logger.info(f"  ℹ️  [{tab_name}] 탭에서 유효한 문의를 찾을 수 없음")
                continue

            # 각 문의에 답변
            for idx, inquiry_data in enumerate(inquiries, 1):
                logger.info(f"\n  📝 문의 {idx}/{len(inquiries)} 처리 중...")
                logger.info(f"    상품: {inquiry_data['product_name'][:50]}...")
                logger.info(f"    문의: {inquiry_data['inquiry'][:100]}...")

                # 답변 작성
                if self.answer_inquiry(inquiry_data):
                    logger.success(f"    ✅ 문의 {idx} 답변 완료!")
                else:
                    logger.error(f"    ❌ 문의 {idx} 답변 실패")

                # 다음 문의 처리 전 대기
                time.sleep(2)

            logger.info(f"\n✅ [{tab_name}] 탭 처리 완료!")

        # 모든 탭에 문의가 없으면
        if not has_any_inquiry:
            logger.info("\n" + "="*60)
            logger.info("ℹ️  모든 탭에 문의가 없습니다. 프로그램을 종료합니다.")
            logger.info("="*60)

        return {
            "success": True,
            "total_inquiries": self.total_inquiries,
            "answered": self.answered_count,
            "failed": self.failed_count,
            "skipped": self.skipped_count
        }

    def run_full_automation(self) -> Dict:
        """
        전체 자동화 프로세스 실행

        Returns:
            Dict: 실행 결과
        """
        try:
            logger.info("\n" + "="*60)
            logger.info("🚀 쿠팡윙 CS 자동화 시작")
            logger.info("="*60)

            # 1. 웹드라이버 설정
            if not self.setup_driver():
                return {"success": False, "message": "웹드라이버 설정 실패"}

            # 2. 로그인
            if not self.login():
                return {"success": False, "message": "로그인 실패"}

            # 3. 고객문의 페이지로 이동
            if not self.navigate_to_inquiries():
                return {"success": False, "message": "페이지 이동 실패"}

            # 4. 모든 탭 처리
            result = self.process_all_tabs()

            # 5. 결과 출력
            logger.info("\n" + "="*60)
            logger.info("📊 처리 완료 통계")
            logger.info("="*60)
            logger.info(f"  총 문의 수: {result['total_inquiries']}")
            logger.info(f"  답변 완료: {result['answered']}")
            logger.info(f"  답변 실패: {result['failed']}")
            logger.info(f"  건너뜀: {result['skipped']}")
            logger.info("="*60)

            result["message"] = f"총 {result['total_inquiries']}개 문의 중 {result['answered']}개 답변 완료"
            return result

        except Exception as e:
            logger.error(f"❌ 자동화 오류: {str(e)}")
            return {
                "success": False,
                "message": f"오류 발생: {str(e)}",
                "statistics": {
                    "total_inquiries": self.total_inquiries,
                    "answered": self.answered_count,
                    "failed": self.failed_count,
                    "skipped": self.skipped_count
                }
            }
        finally:
            self.cleanup()

    def cleanup(self):
        """리소스 정리"""
        if self.driver:
            try:
                logger.info("🧹 브라우저 종료 중...")
                self.driver.quit()
                logger.info("✅ 브라우저 종료 완료")
            except Exception as e:
                logger.error(f"❌ 브라우저 종료 오류: {str(e)}")
