"""
네이버페이 결제내역 기반 반품 자동화 서비스
https://pay.naver.com/pc/history 에서 주문 찾아서 반품 처리
"""
import time
import logging
from typing import Optional, Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException


logger = logging.getLogger(__name__)


class NaverPayAutomation:
    """네이버페이 결제내역 기반 자동화"""

    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Args:
            headless: 헤드리스 모드 사용 여부
            timeout: 대기 시간 (초)
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None

    def setup_driver(self):
        """Chrome WebDriver 설정"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # User-Agent 설정
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # webdriver-manager를 사용하여 자동으로 ChromeDriver 다운로드 및 관리
        logger.info("ChromeDriver 자동 설치 중...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.timeout)

        # Selenium 감지 회피
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        logger.info("Chrome WebDriver 설정 완료")
        return True

    def login(self, username: str, password: str) -> bool:
        """
        네이버 로그인

        Args:
            username: 네이버 아이디
            password: 네이버 비밀번호

        Returns:
            로그인 성공 여부
        """
        try:
            logger.info("네이버 로그인 시작...")
            self.driver.get("https://nid.naver.com/nidlogin.login")
            time.sleep(2)

            # JavaScript로 로그인 (봇 감지 회피)
            login_script = f"""
                document.getElementById('id').value = '{username}';
                document.getElementById('pw').value = '{password}';
                document.querySelector('.btn_login').click();
            """
            self.driver.execute_script(login_script)

            time.sleep(3)

            # 로그인 성공 확인 (리다이렉트 확인)
            current_url = self.driver.current_url
            if "nid.naver.com" not in current_url:
                logger.success("네이버 로그인 성공")
                return True
            else:
                logger.error("네이버 로그인 실패")
                return False

        except Exception as e:
            logger.error(f"네이버 로그인 중 오류: {str(e)}")
            return False

    def navigate_to_payment_history(self) -> bool:
        """
        네이버페이 결제내역으로 이동

        Returns:
            이동 성공 여부
        """
        try:
            logger.info("네이버페이 결제내역으로 이동...")
            self.driver.get("https://pay.naver.com/pc/history?page=1")
            time.sleep(3)

            # 페이지 로드 확인
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "history_list"))
                )
                logger.success("네이버페이 결제내역 페이지 로드 완료")
                return True
            except TimeoutException:
                logger.warning("결제내역 목록을 찾을 수 없음")
                return True  # 페이지는 로드되었으므로 계속 진행

        except Exception as e:
            logger.error(f"결제내역 페이지 이동 중 오류: {str(e)}")
            return False

    def search_order(
        self,
        product_name: str,
        receiver_name: str,
        max_pages: int = 10
    ) -> Optional[Dict]:
        """
        상품명과 수령인으로 주문 검색

        Args:
            product_name: 상품명
            receiver_name: 수령인 이름
            max_pages: 최대 검색 페이지 수

        Returns:
            찾은 주문 정보 (없으면 None)
        """
        try:
            logger.info(f"주문 검색 시작: 상품명={product_name[:30]}..., 수령인={receiver_name}")

            for page in range(1, max_pages + 1):
                logger.info(f"페이지 {page} 검색 중...")

                # 페이지 이동
                if page > 1:
                    self.driver.get(f"https://pay.naver.com/pc/history?page={page}")
                    time.sleep(2)

                # 주문 목록 가져오기
                try:
                    order_items = self.driver.find_elements(By.CLASS_NAME, "history_item")

                    for idx, item in enumerate(order_items):
                        try:
                            # 상품명 추출
                            try:
                                product_elem = item.find_element(By.CLASS_NAME, "product_name")
                                item_product_name = product_elem.text.strip()
                            except NoSuchElementException:
                                continue

                            # 수령인 추출
                            try:
                                receiver_elem = item.find_element(By.CLASS_NAME, "receiver_name")
                                item_receiver_name = receiver_elem.text.strip()
                            except NoSuchElementException:
                                # 수령인 정보가 다른 클래스에 있을 수 있음
                                try:
                                    receiver_elem = item.find_element(By.XPATH, ".//dt[contains(text(),'받는사람')]/following-sibling::dd")
                                    item_receiver_name = receiver_elem.text.strip()
                                except NoSuchElementException:
                                    item_receiver_name = None

                            # 매칭 확인 (부분 일치)
                            product_match = product_name in item_product_name or item_product_name in product_name
                            receiver_match = receiver_name and item_receiver_name and (
                                receiver_name in item_receiver_name or item_receiver_name in receiver_name
                            )

                            if product_match and receiver_match:
                                logger.success(f"주문 찾음! (페이지 {page}, 항목 {idx + 1})")
                                logger.info(f"  - 상품명: {item_product_name}")
                                logger.info(f"  - 수령인: {item_receiver_name}")

                                return {
                                    "page": page,
                                    "index": idx,
                                    "product_name": item_product_name,
                                    "receiver_name": item_receiver_name,
                                    "element": item,
                                }

                        except Exception as e:
                            logger.warning(f"항목 {idx + 1} 처리 중 오류: {str(e)}")
                            continue

                except NoSuchElementException:
                    logger.warning(f"페이지 {page}에 주문 항목이 없음")

            logger.warning("모든 페이지를 검색했으나 일치하는 주문을 찾지 못함")
            return None

        except Exception as e:
            logger.error(f"주문 검색 중 오류: {str(e)}")
            return None

    def process_return(self, order_element) -> bool:
        """
        주문 반품 처리

        Args:
            order_element: 주문 항목 Selenium Element

        Returns:
            처리 성공 여부
        """
        try:
            logger.info("반품 처리 시작...")

            # 반품 버튼 찾기 및 클릭
            try:
                # 여러 가능한 버튼 클래스 시도
                button_selectors = [
                    ".//button[contains(text(), '반품')]",
                    ".//a[contains(text(), '반품')]",
                    ".//button[contains(@class, 'return')]",
                    ".//button[contains(@class, 'cancel')]",
                ]

                return_button = None
                for selector in button_selectors:
                    try:
                        return_button = order_element.find_element(By.XPATH, selector)
                        break
                    except NoSuchElementException:
                        continue

                if not return_button:
                    logger.error("반품 버튼을 찾을 수 없음")
                    return False

                return_button.click()
                logger.info("반품 버튼 클릭")
                time.sleep(2)

            except Exception as e:
                logger.error(f"반품 버튼 클릭 실패: {str(e)}")
                return False

            # 반품 사유 선택 (첫 번째 옵션)
            try:
                reason_select = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='returnReason']"))
                )
                reason_select.find_elements(By.TAG_NAME, "option")[1].click()  # 첫 번째 사유 선택
                logger.info("반품 사유 선택")
                time.sleep(1)

            except TimeoutException:
                logger.warning("반품 사유 선택 필드를 찾을 수 없음 (스킵)")

            # 반품 신청 버튼 클릭
            try:
                submit_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '신청') or contains(text(), '확인')]"))
                )
                submit_button.click()
                logger.info("반품 신청 버튼 클릭")
                time.sleep(2)

            except TimeoutException:
                logger.error("반품 신청 버튼을 찾을 수 없음")
                return False

            # 최종 확인 팝업 처리
            try:
                confirm_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '확인')]")
                confirm_button.click()
                logger.info("최종 확인 완료")
                time.sleep(2)

            except NoSuchElementException:
                logger.info("확인 팝업 없음 (스킵)")

            logger.success("반품 처리 완료")
            return True

        except Exception as e:
            logger.error(f"반품 처리 중 오류: {str(e)}")
            return False

    def process_return_batch(
        self,
        return_items: List[Dict],
        username: str,
        password: str
    ) -> Dict:
        """
        반품 일괄 처리

        Args:
            return_items: 반품 항목 리스트 [{"product_name": "", "receiver_name": ""}, ...]
            username: 네이버 아이디
            password: 네이버 비밀번호

        Returns:
            처리 결과 딕셔너리
        """
        try:
            # WebDriver 설정
            if not self.driver:
                self.setup_driver()

            # 로그인
            if not self.login(username, password):
                return {
                    "success": False,
                    "message": "로그인 실패",
                    "processed": 0,
                    "failed": len(return_items),
                }

            # 결제내역으로 이동
            if not self.navigate_to_payment_history():
                return {
                    "success": False,
                    "message": "결제내역 페이지 이동 실패",
                    "processed": 0,
                    "failed": len(return_items),
                }

            # 배치 처리
            processed = 0
            failed = 0
            errors = []

            for item in return_items:
                try:
                    product_name = item.get("product_name", "")
                    receiver_name = item.get("receiver_name", "")

                    if not product_name:
                        logger.warning("상품명이 없어 스킵")
                        failed += 1
                        continue

                    # 주문 검색
                    order = self.search_order(product_name, receiver_name, max_pages=10)

                    if not order:
                        error_msg = f"주문을 찾을 수 없음: {product_name[:30]}..."
                        logger.warning(error_msg)
                        errors.append(error_msg)
                        failed += 1
                        continue

                    # 반품 처리
                    if self.process_return(order["element"]):
                        processed += 1
                        logger.success(f"처리 완료: {product_name[:30]}...")
                    else:
                        failed += 1
                        error_msg = f"반품 처리 실패: {product_name[:30]}..."
                        errors.append(error_msg)

                    # 다음 항목 처리 전 대기
                    time.sleep(2)

                except Exception as e:
                    error_msg = f"항목 처리 중 오류: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    failed += 1

            return {
                "success": True,
                "message": f"처리 완료: {processed}건 성공, {failed}건 실패",
                "processed": processed,
                "failed": failed,
                "errors": errors,
            }

        except Exception as e:
            error_msg = f"배치 처리 중 오류: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "processed": 0,
                "failed": len(return_items),
            }

    def close(self):
        """WebDriver 종료"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver 종료")
            except Exception as e:
                logger.warning(f"WebDriver 종료 중 오류: {str(e)}")
