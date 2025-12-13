"""
Naver SmartStore Automation Service
네이버 스마트스토어 반품신청 및 주문취소 자동화
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from loguru import logger
import time
from typing import List, Dict, Optional


class NaverSmartStoreAutomation:
    """
    네이버 스마트스토어 자동화 서비스
    - 반품신청 자동화
    - 주문취소 자동화
    """

    def __init__(self, username: str, password: str, headless: bool = False):
        """
        초기화

        Args:
            username: 네이버 아이디
            password: 네이버 비밀번호
            headless: 백그라운드 실행 여부
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.driver = None
        self.wait = None

        # 통계
        self.processed_count = 0
        self.failed_count = 0

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
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # Selenium 4의 자동 드라이버 관리 사용
            logger.info("🔄 ChromeDriver 초기화 중...")
            # Service를 명시하지 않으면 Selenium이 자동으로 드라이버 다운로드 및 관리
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)

            logger.info("✅ 웹드라이버 설정 완료")
            return True
        except Exception as e:
            logger.error(f"❌ 웹드라이버 설정 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def login(self) -> bool:
        """네이버 로그인"""
        try:
            logger.info("🔐 네이버 로그인 시작...")

            # 네이버 로그인 페이지로 이동
            self.driver.get("https://nid.naver.com/nidlogin.login")
            time.sleep(2)

            # 자동입력 방지를 우회하기 위해 JavaScript로 입력
            logger.info("  📝 아이디 입력...")
            self.driver.execute_script(
                f"document.getElementById('id').value = '{self.username}';"
            )

            logger.info("  📝 비밀번호 입력...")
            self.driver.execute_script(
                f"document.getElementById('pw').value = '{self.password}';"
            )

            time.sleep(1)

            # 로그인 버튼 클릭
            logger.info("  🖱️  로그인 버튼 클릭...")
            login_button = self.driver.find_element(By.ID, "log.login")
            login_button.click()

            # 로그인 완료 대기
            time.sleep(5)

            # 로그인 성공 확인
            current_url = self.driver.current_url
            if "nid.naver.com" not in current_url:
                logger.success("✅ 로그인 성공!")
                return True
            else:
                logger.error(f"❌ 로그인 실패 - 현재 URL: {current_url}")
                logger.warning("⚠️  Captcha 또는 2차 인증이 필요할 수 있습니다.")
                self.driver.save_screenshot("naver_login_failed.png")
                return False

        except Exception as e:
            logger.error(f"❌ 로그인 오류: {str(e)}")
            if self.driver:
                self.driver.save_screenshot("naver_login_error.png")
            return False

    def navigate_to_smartstore_center(self) -> bool:
        """스마트스토어 센터로 이동"""
        try:
            logger.info("📋 스마트스토어 센터로 이동...")
            self.driver.get("https://sell.smartstore.naver.com/#/")
            time.sleep(3)
            logger.success("✅ 스마트스토어 센터 이동 완료")
            return True
        except Exception as e:
            logger.error(f"❌ 페이지 이동 오류: {str(e)}")
            return False

    def navigate_to_order_management(self) -> bool:
        """주문 관리 페이지로 이동"""
        try:
            logger.info("📦 주문 관리 페이지로 이동...")
            self.driver.get("https://sell.smartstore.naver.com/#/orders/order-list")
            time.sleep(3)
            logger.success("✅ 주문 관리 페이지 이동 완료")
            return True
        except Exception as e:
            logger.error(f"❌ 페이지 이동 오류: {str(e)}")
            return False

    def search_order_by_product_name(self, product_name: str, order_date: str = None) -> bool:
        """
        상품명으로 주문 검색

        Args:
            product_name: 상품명
            order_date: 주문일자 (YYYY-MM-DD)

        Returns:
            bool: 검색 성공 여부
        """
        try:
            logger.info(f"🔍 상품 검색: {product_name[:50]}...")

            # 검색 입력란 찾기
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'][placeholder*='상품명']"))
            )

            # 검색어 입력
            search_input.clear()
            search_input.send_keys(product_name)
            time.sleep(1)

            # 검색 버튼 클릭
            search_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            search_button.click()
            time.sleep(3)

            logger.success("✅ 검색 완료")
            return True

        except Exception as e:
            logger.error(f"❌ 상품 검색 오류: {str(e)}")
            return False

    def process_return_request(
        self,
        product_name: str,
        coupang_order_id: str,
        return_reason: str = "고객 요청"
    ) -> bool:
        """
        반품 신청 처리

        Args:
            product_name: 상품명
            coupang_order_id: 쿠팡 주문번호 (로그용)
            return_reason: 반품 사유

        Returns:
            bool: 성공 여부
        """
        try:
            logger.info(f"📦 반품 처리 시작: {product_name[:50]}...")

            # 1. 상품 검색
            if not self.search_order_by_product_name(product_name):
                logger.error("  ❌ 상품을 찾을 수 없음")
                return False

            # 2. 첫 번째 검색 결과 찾기
            try:
                # 주문 목록 테이블에서 첫 번째 행 찾기
                first_order_row = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr:first-child"))
                )

                # 반품신청 버튼 찾기
                return_button = first_order_row.find_element(
                    By.XPATH,
                    ".//button[contains(text(), '반품') or contains(text(), '교환/반품')]"
                )

                # 스크롤 및 클릭
                self.driver.execute_script("arguments[0].scrollIntoView(true);", return_button)
                time.sleep(1)

                try:
                    return_button.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", return_button)

                time.sleep(2)
                logger.info("  ✅ 반품신청 버튼 클릭")

            except Exception as e:
                logger.error(f"  ❌ 주문을 찾을 수 없거나 반품신청 버튼이 없음: {str(e)}")
                return False

            # 3. 반품 사유 입력 (필요시)
            try:
                reason_textarea = self.driver.find_element(By.CSS_SELECTOR, "textarea[name='reason']")
                reason_textarea.clear()
                reason_textarea.send_keys(return_reason)
                logger.info("  ✅ 반품 사유 입력")
            except:
                logger.debug("  ℹ️  반품 사유 입력란 없음 (건너뜀)")

            # 4. 반품 확인 버튼 클릭
            try:
                confirm_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '확인') or contains(text(), '신청')]"))
                )
                confirm_button.click()
                time.sleep(2)
                logger.success("  ✅ 반품 신청 완료!")

                self.processed_count += 1
                return True

            except Exception as e:
                logger.error(f"  ❌ 반품 확인 버튼 클릭 실패: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"❌ 반품 처리 오류: {str(e)}")
            self.failed_count += 1

            # 오류 스크린샷 저장
            try:
                timestamp = int(time.time())
                self.driver.save_screenshot(f"error_naver_return_{timestamp}.png")
                logger.info(f"  📸 오류 스크린샷 저장: error_naver_return_{timestamp}.png")
            except:
                pass

            return False

    def process_order_cancel(
        self,
        product_name: str,
        coupang_order_id: str,
        cancel_reason: str = "출고중지 요청"
    ) -> bool:
        """
        주문 취소 처리

        Args:
            product_name: 상품명
            coupang_order_id: 쿠팡 주문번호 (로그용)
            cancel_reason: 취소 사유

        Returns:
            bool: 성공 여부
        """
        try:
            logger.info(f"🚫 주문 취소 시작: {product_name[:50]}...")

            # 1. 상품 검색
            if not self.search_order_by_product_name(product_name):
                logger.error("  ❌ 상품을 찾을 수 없음")
                return False

            # 2. 첫 번째 검색 결과 찾기
            try:
                # 주문 목록 테이블에서 첫 번째 행 찾기
                first_order_row = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr:first-child"))
                )

                # 주문취소 버튼 찾기
                cancel_button = first_order_row.find_element(
                    By.XPATH,
                    ".//button[contains(text(), '취소') or contains(text(), '주문취소')]"
                )

                # 스크롤 및 클릭
                self.driver.execute_script("arguments[0].scrollIntoView(true);", cancel_button)
                time.sleep(1)

                try:
                    cancel_button.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", cancel_button)

                time.sleep(2)
                logger.info("  ✅ 주문취소 버튼 클릭")

            except Exception as e:
                logger.error(f"  ❌ 주문을 찾을 수 없거나 주문취소 버튼이 없음: {str(e)}")
                return False

            # 3. 취소 사유 선택/입력
            try:
                # 취소 사유 선택 (셀렉트박스)
                reason_select = self.driver.find_element(By.CSS_SELECTOR, "select[name='cancelReason']")
                # 첫 번째 옵션 선택 (일반적으로 "판매자 요청" 등)
                self.driver.execute_script(
                    "arguments[0].selectedIndex = 1;",
                    reason_select
                )
                logger.info("  ✅ 취소 사유 선택")
            except:
                logger.debug("  ℹ️  취소 사유 선택란 없음 (건너뜀)")

            # 4. 취소 확인 버튼 클릭
            try:
                confirm_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '확인') or contains(text(), '취소신청')]"))
                )
                confirm_button.click()
                time.sleep(2)
                logger.success("  ✅ 주문 취소 완료!")

                self.processed_count += 1
                return True

            except Exception as e:
                logger.error(f"  ❌ 취소 확인 버튼 클릭 실패: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"❌ 주문 취소 오류: {str(e)}")
            self.failed_count += 1

            # 오류 스크린샷 저장
            try:
                timestamp = int(time.time())
                self.driver.save_screenshot(f"error_naver_cancel_{timestamp}.png")
                logger.info(f"  📸 오류 스크린샷 저장: error_naver_cancel_{timestamp}.png")
            except:
                pass

            return False

    def process_coupang_returns_batch(
        self,
        return_items: List[Dict]
    ) -> Dict:
        """
        쿠팡 반품 목록을 배치로 처리

        Args:
            return_items: 반품 아이템 리스트
                [
                    {
                        "product_name": "상품명",
                        "coupang_order_id": "쿠팡 주문번호",
                        "receipt_status": "RETURNS_UNCHECKED" or "RELEASE_STOP_UNCHECKED",
                        "return_reason": "반품 사유"
                    },
                    ...
                ]

        Returns:
            Dict: 처리 결과
        """
        try:
            logger.info("\n" + "="*70)
            logger.info("🚀 네이버 스마트스토어 반품 자동화 시작")
            logger.info("="*70)
            logger.info(f"📌 총 {len(return_items)}개 반품 처리 예정")
            logger.info("="*70)

            # 1. 웹드라이버 설정
            if not self.setup_driver():
                return {"success": False, "message": "웹드라이버 설정 실패"}

            # 2. 로그인
            if not self.login():
                return {"success": False, "message": "로그인 실패"}

            # 3. 스마트스토어 센터로 이동
            if not self.navigate_to_smartstore_center():
                return {"success": False, "message": "스마트스토어 센터 이동 실패"}

            # 4. 주문 관리 페이지로 이동
            if not self.navigate_to_order_management():
                return {"success": False, "message": "주문 관리 페이지 이동 실패"}

            # 5. 각 반품 아이템 처리
            for idx, item in enumerate(return_items, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"📦 [{idx}/{len(return_items)}] 처리 중...")
                logger.info(f"  상품: {item['product_name'][:50]}...")
                logger.info(f"  쿠팡 주문번호: {item['coupang_order_id']}")
                logger.info(f"  상태: {item['receipt_status']}")
                logger.info(f"{'='*60}")

                # 반품 상태에 따라 처리
                if item['receipt_status'] == 'RELEASE_STOP_UNCHECKED':
                    # 출고중지요청 → 주문취소
                    success = self.process_order_cancel(
                        product_name=item['product_name'],
                        coupang_order_id=item['coupang_order_id'],
                        cancel_reason="쿠팡 출고중지 요청"
                    )
                else:
                    # 반품접수 → 반품신청
                    success = self.process_return_request(
                        product_name=item['product_name'],
                        coupang_order_id=item['coupang_order_id'],
                        return_reason=item.get('return_reason', '고객 요청')
                    )

                if success:
                    logger.success(f"✅ [{idx}] 처리 완료!")
                else:
                    logger.error(f"❌ [{idx}] 처리 실패")

                # 다음 아이템 처리 전 대기
                time.sleep(2)

            # 6. 최종 결과
            logger.info("\n" + "="*70)
            logger.info("📊 최종 처리 통계")
            logger.info("="*70)
            logger.info(f"  총 항목: {len(return_items)}")
            logger.info(f"  처리 완료: {self.processed_count}")
            logger.info(f"  처리 실패: {self.failed_count}")
            logger.info(f"  성공률: {(self.processed_count / len(return_items) * 100) if len(return_items) > 0 else 0:.1f}%")
            logger.info("="*70)

            return {
                "success": True,
                "message": f"총 {len(return_items)}개 중 {self.processed_count}개 처리 완료",
                "statistics": {
                    "total": len(return_items),
                    "processed": self.processed_count,
                    "failed": self.failed_count
                }
            }

        except Exception as e:
            logger.error(f"❌ 배치 처리 오류: {str(e)}")
            return {
                "success": False,
                "message": f"오류 발생: {str(e)}",
                "statistics": {
                    "total": len(return_items),
                    "processed": self.processed_count,
                    "failed": self.failed_count
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
                logger.success("✅ 브라우저 종료 완료")
            except Exception as e:
                logger.error(f"❌ 브라우저 종료 오류: {str(e)}")
