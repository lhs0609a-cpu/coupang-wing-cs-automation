"""
Coupang Wing Web Automation Service V3 - Enhanced with Loop Logic
모든 탭에서 미답변 문의가 없을 때까지 반복 처리
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from loguru import logger
import time
from typing import List, Dict, Optional
from openai import OpenAI
from ..config import settings


class WingWebAutomationV3:
    """
    쿠팡윙 고객문의 자동 응답 시스템 V3
    - 사용자 제공 HTML 구조에 정확히 맞춤
    - 모든 탭에서 미답변이 없을 때까지 무한 반복
    """

    # 시간대별 탭 정의 (순서대로 처리)
    TIME_RANGES = [
        "72시간~30일 이내",
        "24~72시간",
        "24시간 이내"
    ]

    def __init__(self, username: str, password: str, headless: bool = False, max_rounds: int = 100):
        """
        초기화

        Args:
            username: 쿠팡윙 아이디
            password: 쿠팡윙 비밀번호
            headless: 백그라운드 실행 여부
            max_rounds: 최대 반복 횟수 (무한루프 방지)
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.max_rounds = max_rounds
        self.driver = None
        self.wait = None
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

        # 통계
        self.total_rounds = 0
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
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

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

            # 로그인 완료 대기
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

    def click_tab(self, tab_name: str, retry: int = 3) -> bool:
        """
        특정 시간대 탭 클릭

        Args:
            tab_name: 탭 이름 (예: "24시간 이내")
            retry: 재시도 횟수

        Returns:
            bool: 성공 여부
        """
        for attempt in range(retry):
            try:
                logger.info(f"  🔍 '{tab_name}' 탭 찾는 중... (시도 {attempt + 1}/{retry})")

                # 다양한 방법으로 탭 찾기
                tabs = []

                # 방법 1: data-v-* 속성이 있는 버튼/링크
                tabs = self.driver.find_elements(By.CSS_SELECTOR, "[data-v-7fedaa82]")

                # 방법 2: role="tab" 속성
                if not tabs:
                    tabs = self.driver.find_elements(By.CSS_SELECTOR, "[role='tab']")

                # 방법 3: 모든 버튼과 링크
                if not tabs:
                    tabs = self.driver.find_elements(By.TAG_NAME, "button")
                    tabs += self.driver.find_elements(By.TAG_NAME, "a")

                # 텍스트가 일치하는 탭 찾기
                for tab in tabs:
                    try:
                        tab_text = tab.text.strip()
                        if tab_name in tab_text or tab_text in tab_name:
                            # 스크롤하여 보이게 하기
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", tab)
                            time.sleep(0.5)

                            # 클릭 시도
                            try:
                                tab.click()
                            except ElementClickInterceptedException:
                                # JavaScript로 클릭
                                self.driver.execute_script("arguments[0].click();", tab)

                            time.sleep(2)
                            logger.success(f"  ✅ '{tab_name}' 탭 클릭 완료")
                            return True
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        logger.debug(f"    탭 클릭 시도 중 오류: {str(e)}")
                        continue

                logger.warning(f"  ⚠️  '{tab_name}' 탭을 찾을 수 없음")
                time.sleep(1)

            except Exception as e:
                logger.error(f"  ❌ 탭 클릭 오류: {str(e)}")
                time.sleep(1)

        return False

    def get_unanswered_inquiries_in_current_tab(self) -> List[Dict]:
        """
        현재 탭의 미답변 문의 수집
        사용자가 제공한 HTML 구조에 맞춰 구현

        Returns:
            List[Dict]: 문의 정보 리스트
        """
        inquiries = []

        try:
            logger.info("    📥 미답변 문의 수집 중...")
            time.sleep(2)

            # 사용자 제공 HTML 구조에 따라 미답변 문의 찾기
            # <td data-v-7fedaa82="" class="middle-horizontal-padding small-vertical-padding vertical-align replying-no-comments">

            # 방법 1: replying-no-comments 클래스로 찾기 (미답변 문의)
            unanswered_cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "td.replying-no-comments, td[class*='replying-no-comments']"
            )

            logger.info(f"    📊 총 {len(unanswered_cells)}개 미답변 셀 발견")

            for idx, cell in enumerate(unanswered_cells):
                try:
                    # 1. 상품명 찾기
                    # <div class="text-wrapper product-name"><a><span title="상품명">상품명</span></a></div>
                    product_name = None
                    try:
                        product_elem = cell.find_element(
                            By.CSS_SELECTOR,
                            "div.text-wrapper.product-name a span[title], div.product-name a span[title]"
                        )
                        product_name = product_elem.get_attribute("title") or product_elem.text
                    except:
                        try:
                            product_elem = cell.find_element(By.CSS_SELECTOR, "div.text-wrapper a span")
                            product_name = product_elem.get_attribute("title") or product_elem.text
                        except:
                            logger.debug(f"      셀 {idx}: 상품명 없음, 건너뛰기")
                            continue

                    if not product_name or not product_name.strip():
                        logger.debug(f"      셀 {idx}: 상품명이 비어있음")
                        continue

                    # 2. 문의 내용 찾기
                    # <div><span class="inquiry-content">고객 문의 내용</span></div>
                    inquiry_text = None
                    try:
                        inquiry_elem = cell.find_element(By.CSS_SELECTOR, "span.inquiry-content")
                        inquiry_text = inquiry_elem.text.strip()
                    except:
                        try:
                            # 대안: div 안의 span
                            inquiry_elem = cell.find_element(By.CSS_SELECTOR, "div > span")
                            inquiry_text = inquiry_elem.text.strip()
                        except:
                            logger.debug(f"      셀 {idx}: 문의내용 없음")
                            continue

                    if not inquiry_text or not inquiry_text.strip():
                        logger.debug(f"      셀 {idx}: 문의내용이 비어있음")
                        continue

                    # 3. 답변하기 버튼 찾기
                    # <button data-v-7fedaa82="" type="button" class="wing-web-component">답변하기</button>
                    answer_button = None

                    # 부모 row 찾기 (td의 부모 tr)
                    try:
                        row = cell.find_element(By.XPATH, "./ancestor::tr[1]")

                        # row에서 답변하기 버튼 찾기
                        buttons = row.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            btn_text = btn.text.strip()
                            btn_class = btn.get_attribute("class") or ""

                            if "답변하기" in btn_text or "답변" in btn_text:
                                answer_button = btn
                                break
                            elif "wing-web-component" in btn_class:
                                answer_button = btn
                                break
                    except:
                        logger.debug(f"      셀 {idx}: 답변하기 버튼 없음")
                        continue

                    if not answer_button:
                        logger.debug(f"      셀 {idx}: 답변하기 버튼을 찾을 수 없음")
                        continue

                    # 유효한 문의 추가
                    inquiries.append({
                        "product_name": product_name.strip(),
                        "inquiry": inquiry_text.strip(),
                        "answer_button": answer_button,
                        "cell": cell
                    })

                    logger.info(f"      ✅ 문의 {len(inquiries)}: {product_name[:30]}...")

                except StaleElementReferenceException:
                    logger.debug(f"      셀 {idx}: Stale element, 건너뛰기")
                    continue
                except Exception as e:
                    logger.debug(f"      셀 {idx}: 오류 - {str(e)}")
                    continue

            logger.success(f"    ✅ 총 {len(inquiries)}개 미답변 문의 수집 완료")
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
1. 정중하고 친절한 말투 사용 (존댓말)
2. 고객의 문의에 정확하게 답변
3. 필요시 추가 정보 제공 또는 안내
4. 500자 이내로 간결하게 작성
5. 개인정보(전화번호, 이메일)를 절대 요구하지 말 것
6. 마크다운 형식 사용 금지 (일반 텍스트만)
7. 판매자 문의하기로 추가 문의 가능하다는 안내

답변:
"""

            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 전문적이고 친절한 쿠팡 판매자 CS 담당자입니다. 마크다운을 사용하지 말고 일반 텍스트로만 답변하세요."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )

            answer = response.choices[0].message.content.strip()

            # 마크다운 제거
            answer = answer.replace('**', '').replace('__', '').replace('*', '').replace('_', '')

            logger.success(f"      ✅ ChatGPT 답변 생성 완료 ({len(answer)}자)")
            return answer

        except Exception as e:
            logger.error(f"      ❌ ChatGPT 답변 생성 오류: {str(e)}")
            # 기본 답변 반환
            return f"안녕하세요. '{product_name}' 관련 문의 주셔서 감사합니다. 확인 후 빠른 시일 내에 답변 드리겠습니다. 추가 문의사항이 있으시면 판매자 문의하기를 이용해 주세요. 감사합니다."

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

            logger.info(f"    💬 답변 작성: {product_name[:40]}...")

            # 1. 답변하기 버튼 클릭
            logger.info("      🖱️  답변하기 버튼 클릭...")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", answer_button)
            time.sleep(1)

            try:
                answer_button.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", answer_button)

            time.sleep(2)

            # 2. 답변 생성
            answer_text = self.generate_answer_with_gpt(product_name, inquiry_text)

            # 3. 답변 입력란 찾기
            # <textarea placeholder="상품문의 내 고객의 개인정보(전화번호,이메일 등)를 요구할 경우 해당 문의가 미노출처리될 수 있습니다..." class="textarea_full_58 input-textarea"></textarea>
            logger.info("      📝 답변 입력란 찾는 중...")
            textarea = None

            try:
                textarea = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.input-textarea"))
                )
            except:
                try:
                    textarea = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "textarea[placeholder*='상품문의']"
                    )
                except:
                    try:
                        textarea = self.driver.find_element(By.CSS_SELECTOR, "textarea.textarea_full_58")
                    except:
                        textarea = self.driver.find_element(By.TAG_NAME, "textarea")

            if not textarea:
                logger.error("      ❌ 답변 입력란을 찾을 수 없음")
                return False

            # 4. 답변 입력
            logger.info("      ✍️  답변 입력 중...")
            textarea.clear()
            time.sleep(0.5)
            textarea.send_keys(answer_text)
            time.sleep(1)
            logger.success(f"      ✅ 답변 입력 완료 ({len(answer_text)}자)")

            # 5. 저장하기 버튼 찾기 및 클릭
            # <button data-v-7fedaa82="" type="button" class="wing-web-component">저장하기</button>
            logger.info("      💾 저장하기 버튼 찾는 중...")
            save_button = None

            try:
                # 모든 버튼을 찾아서 "저장하기" 텍스트가 있는 것 찾기
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    btn_text = btn.text.strip()
                    if "저장하기" in btn_text or "저장" in btn_text:
                        save_button = btn
                        break

                if not save_button:
                    # wing-web-component 클래스로 찾기
                    save_button = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button.wing-web-component[data-v-7fedaa82]"
                    )
            except:
                logger.error("      ❌ 저장하기 버튼을 찾을 수 없음")
                return False

            # 6. 저장하기 클릭
            logger.info("      🖱️  저장하기 버튼 클릭...")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_button)
            time.sleep(0.5)

            try:
                save_button.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", save_button)

            time.sleep(3)

            logger.success("    ✅ 답변 저장 완료!")
            self.answered_count += 1
            return True

        except Exception as e:
            logger.error(f"    ❌ 답변 작성 오류: {str(e)}")
            self.failed_count += 1

            # 오류 스크린샷 저장
            try:
                timestamp = int(time.time())
                self.driver.save_screenshot(f"error_answer_{timestamp}.png")
                logger.info(f"      📸 오류 스크린샷 저장: error_answer_{timestamp}.png")
            except:
                pass

            return False

    def process_all_tabs_once(self) -> int:
        """
        모든 시간대 탭을 한 번 순회하며 문의 처리

        Returns:
            int: 처리한 문의 개수
        """
        total_processed = 0

        for tab_name in self.TIME_RANGES:
            logger.info(f"\n{'─'*60}")
            logger.info(f"📂 [{tab_name}] 탭 처리 중...")
            logger.info(f"{'─'*60}")

            # 탭 클릭
            if not self.click_tab(tab_name):
                logger.warning(f"  ⚠️  [{tab_name}] 탭 클릭 실패, 다음 탭으로...")
                continue

            # 현재 탭의 미답변 문의 수집
            inquiries = self.get_unanswered_inquiries_in_current_tab()
            self.total_inquiries += len(inquiries)

            if not inquiries:
                logger.info(f"  ℹ️  [{tab_name}] 탭에 미답변 문의 없음")
                continue

            logger.info(f"  📊 [{tab_name}] 탭에서 {len(inquiries)}개 문의 발견")

            # 각 문의에 답변
            for idx, inquiry_data in enumerate(inquiries, 1):
                logger.info(f"\n  📝 문의 {idx}/{len(inquiries)} 처리 중...")
                logger.info(f"    상품: {inquiry_data['product_name'][:50]}...")
                logger.info(f"    문의: {inquiry_data['inquiry'][:100]}...")

                # 답변 작성
                if self.answer_inquiry(inquiry_data):
                    total_processed += 1
                    logger.success(f"    ✅ 문의 {idx} 답변 완료!")
                else:
                    logger.error(f"    ❌ 문의 {idx} 답변 실패")

                # 다음 문의 처리 전 대기
                time.sleep(2)

            logger.info(f"\n✅ [{tab_name}] 탭 처리 완료! (처리: {len(inquiries)}개)")

        return total_processed

    def run_full_automation_loop(self) -> Dict:
        """
        전체 자동화 프로세스 실행 (모든 탭에서 미답변이 없을 때까지 반복)

        Returns:
            Dict: 실행 결과
        """
        try:
            logger.info("\n" + "="*70)
            logger.info("🚀 쿠팡윙 CS 자동화 V3 시작")
            logger.info("="*70)
            logger.info(f"📌 모든 탭에서 미답변이 없을 때까지 반복 (최대 {self.max_rounds}회)")
            logger.info("="*70)

            # 1. 웹드라이버 설정
            if not self.setup_driver():
                return {"success": False, "message": "웹드라이버 설정 실패"}

            # 2. 로그인
            if not self.login():
                return {"success": False, "message": "로그인 실패"}

            # 3. 고객문의 페이지로 이동
            if not self.navigate_to_inquiries():
                return {"success": False, "message": "페이지 이동 실패"}

            # 4. 모든 탭에서 미답변이 없을 때까지 반복
            while self.total_rounds < self.max_rounds:
                self.total_rounds += 1

                logger.info("\n" + "="*70)
                logger.info(f"🔄 라운드 {self.total_rounds} 시작")
                logger.info("="*70)

                # 한 번 순회
                processed_count = self.process_all_tabs_once()

                logger.info("\n" + "="*70)
                logger.info(f"📊 라운드 {self.total_rounds} 완료")
                logger.info(f"  - 이번 라운드 처리: {processed_count}개")
                logger.info(f"  - 누적 답변 완료: {self.answered_count}개")
                logger.info(f"  - 누적 실패: {self.failed_count}개")
                logger.info("="*70)

                # 처리한 문의가 없으면 종료
                if processed_count == 0:
                    logger.success("\n🎉 모든 탭에 미답변 문의가 없습니다!")
                    logger.success("✅ 자동화 작업 완료!")
                    break

                # 다음 라운드 전 대기
                logger.info("\n⏳ 3초 후 다음 라운드 시작...")
                time.sleep(3)

                # 페이지 새로고침
                logger.info("🔄 페이지 새로고침...")
                self.navigate_to_inquiries()

            # 최대 반복 횟수 도달
            if self.total_rounds >= self.max_rounds:
                logger.warning(f"\n⚠️  최대 반복 횟수({self.max_rounds})에 도달했습니다.")

            # 5. 최종 결과 출력
            logger.info("\n" + "="*70)
            logger.info("📊 최종 처리 통계")
            logger.info("="*70)
            logger.info(f"  총 라운드: {self.total_rounds}")
            logger.info(f"  총 문의 수: {self.total_inquiries}")
            logger.info(f"  답변 완료: {self.answered_count}")
            logger.info(f"  답변 실패: {self.failed_count}")
            logger.info(f"  건너뜀: {self.skipped_count}")
            logger.info(f"  성공률: {(self.answered_count / self.total_inquiries * 100) if self.total_inquiries > 0 else 0:.1f}%")
            logger.info("="*70)

            return {
                "success": True,
                "message": f"총 {self.total_inquiries}개 문의 중 {self.answered_count}개 답변 완료",
                "statistics": {
                    "total_rounds": self.total_rounds,
                    "total_inquiries": self.total_inquiries,
                    "answered": self.answered_count,
                    "failed": self.failed_count,
                    "skipped": self.skipped_count
                }
            }

        except Exception as e:
            logger.error(f"❌ 자동화 오류: {str(e)}")
            return {
                "success": False,
                "message": f"오류 발생: {str(e)}",
                "statistics": {
                    "total_rounds": self.total_rounds,
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
                logger.success("✅ 브라우저 종료 완료")
            except Exception as e:
                logger.error(f"❌ 브라우저 종료 오류: {str(e)}")
