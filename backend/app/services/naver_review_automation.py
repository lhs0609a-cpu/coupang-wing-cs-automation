"""
Naver Review Automation Service
네이버 리뷰 자동화 서비스 - Selenium 기반
"""
import os
import time
import re
import random
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Tuple, Callable
from loguru import logger

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not installed. NaverReviewBot will not be available.")


class NaverReviewBot:
    """네이버 리뷰 자동화 봇"""

    def __init__(self, log_callback: Optional[Callable] = None, status_callback: Optional[Callable] = None):
        """
        Args:
            log_callback: 로그 메시지 콜백 함수 (message, level)
            status_callback: 상태 업데이트 콜백 함수 (status, current, total)
        """
        self.driver = None
        self.is_running = False
        self.current_review = 0
        self.total_reviews = 0
        self.status = "대기 중"
        self.session_id = None

        self._log_callback = log_callback
        self._status_callback = status_callback

    def log(self, message: str, level: str = 'info'):
        """로그 메시지 출력"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level.upper()}] {message}"

        # 콘솔 로그
        if level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'success':
            logger.success(message)
        else:
            logger.info(message)

        # 콜백으로 전송
        if self._log_callback:
            try:
                self._log_callback({
                    'time': timestamp,
                    'level': level,
                    'message': message,
                    'session_id': self.session_id
                })
            except Exception as e:
                logger.error(f"Log callback error: {e}")

    def update_status(self, status: str, current: int = None, total: int = None):
        """상태 업데이트"""
        self.status = status
        if current is not None:
            self.current_review = current
        if total is not None:
            self.total_reviews = total

        if self._status_callback:
            try:
                self._status_callback({
                    'status': status,
                    'current': self.current_review,
                    'total': self.total_reviews,
                    'is_running': self.is_running,
                    'session_id': self.session_id
                })
            except Exception as e:
                logger.error(f"Status callback error: {e}")

    def init_driver(self, headless: bool = False) -> bool:
        """Selenium 드라이버 초기화"""
        if not SELENIUM_AVAILABLE:
            self.log("Selenium이 설치되지 않았습니다.", 'error')
            return False

        try:
            self.log("브라우저 초기화 중...")

            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)

            # ChromeDriver 경로
            driver_path = ChromeDriverManager().install()
            driver_dir = os.path.dirname(driver_path)

            # chromedriver.exe 파일 검색
            actual_driver_path = None
            possible_paths = [
                driver_path,
                os.path.join(driver_dir, "chromedriver.exe"),
                os.path.join(driver_dir, "chromedriver-win32", "chromedriver.exe"),
                os.path.join(driver_dir, "chromedriver-win64", "chromedriver.exe"),
            ]

            # 디렉토리에서 chromedriver 검색
            for root, dirs, files in os.walk(driver_dir):
                for file in files:
                    if file in ["chromedriver.exe", "chromedriver"]:
                        found_path = os.path.join(root, file)
                        if os.path.exists(found_path):
                            possible_paths.insert(0, found_path)

            for path in possible_paths:
                if os.path.exists(path):
                    actual_driver_path = path
                    self.log(f"ChromeDriver 찾음: {actual_driver_path}")
                    break

            if not actual_driver_path:
                raise Exception("chromedriver를 찾을 수 없습니다.")

            service = Service(executable_path=actual_driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            self.log("브라우저 초기화 완료!", 'success')
            return True

        except Exception as e:
            self.log(f"브라우저 초기화 실패: {str(e)}", 'error')
            return False

    def auto_login(self, naver_id: str, naver_pw: str) -> bool:
        """네이버 자동 로그인"""
        try:
            self.log("네이버 로그인 페이지로 이동 중...")
            self.driver.get("https://nid.naver.com/nidlogin.login")
            time.sleep(2)

            self.log("아이디/비밀번호 입력 중...")

            # JavaScript로 직접 값 설정 (봇 감지 우회)
            self.driver.execute_script(f"document.getElementById('id').value = '{naver_id}'")
            time.sleep(0.5)
            self.driver.execute_script(f"document.getElementById('pw').value = '{naver_pw}'")
            time.sleep(0.5)

            # 로그인 버튼 클릭
            login_btn = self.driver.find_element(By.ID, "log.login")
            login_btn.click()

            self.log("로그인 버튼 클릭 완료, 로그인 처리 중...")
            time.sleep(5)

            # 로그인 성공 확인
            if "nid.naver.com" in self.driver.current_url:
                self.log("로그인 실패 또는 추가 인증 필요", 'warning')
                self.log("수동으로 인증을 완료해주세요 (캡차, 2단계 인증 등)", 'warning')
                return False
            else:
                self.log("로그인 성공!", 'success')
                return True

        except Exception as e:
            self.log(f"로그인 실패: {str(e)}", 'error')
            return False

    def manual_login_wait(self) -> bool:
        """수동 로그인 대기"""
        try:
            self.log("네이버 로그인 페이지로 이동 중...")
            self.driver.get("https://nid.naver.com/nidlogin.login")
            self.log("브라우저에서 수동으로 로그인해주세요!", 'warning')
            self.log("로그인 완료 후 자동으로 계속됩니다...", 'info')

            # 로그인 완료 대기 (최대 5분)
            for i in range(60):
                if not self.is_running:
                    return False
                time.sleep(5)
                if "nid.naver.com" not in self.driver.current_url:
                    self.log("로그인 확인됨!", 'success')
                    return True
                self.log(f"로그인 대기 중... ({i*5}초)", 'info')

            self.log("로그인 시간 초과", 'warning')
            return False

        except Exception as e:
            self.log(f"수동 로그인 대기 실패: {str(e)}", 'error')
            return False

    def go_to_review_page(self) -> bool:
        """네이버 쇼핑 리뷰 작성 페이지로 이동"""
        try:
            self.log("네이버 쇼핑 작성 가능한 리뷰 페이지로 이동 중...")
            self.driver.get("https://shopping.naver.com/my/writable-reviews")
            time.sleep(3)

            # 페이지 스크롤 (모든 요소 로드)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            self.log("리뷰 작성 페이지 로드 완료!", 'success')
            return True

        except Exception as e:
            self.log(f"리뷰 페이지 이동 실패: {str(e)}", 'error')
            return False

    def scroll_to_load_more(self) -> bool:
        """페이지를 스크롤하여 더 많은 리뷰 로드"""
        try:
            try:
                self.driver.current_url
            except:
                self.log("브라우저 창이 닫혔습니다", 'warning')
                return False

            current_url = self.driver.current_url
            if "writable-reviews" not in current_url:
                self.log("리뷰 페이지가 아닙니다. 페이지로 돌아갑니다", 'warning')
                self.driver.get("https://shopping.naver.com/my/writable-reviews")
                time.sleep(2)

            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.log(f"페이지 스크롤 중... (현재 높이: {last_height}px)")

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height > last_height:
                self.log(f"새로운 콘텐츠 로드됨! (새 높이: {new_height}px)", 'success')
                return True
            else:
                self.log(f"페이지 끝에 도달! (높이: {new_height}px)", 'warning')
                return False

        except Exception as e:
            self.log(f"스크롤 오류: {str(e)}", 'error')
            return False

    def find_next_topmost_button(self, last_y_position: int = 0) -> Tuple[Optional[any], int]:
        """마지막 처리한 위치보다 아래에 있는 '포인트 최대' 버튼 찾기"""
        try:
            time.sleep(0.5)
            self.log(f"리뷰쓰기 버튼 검색 중... (마지막 Y위치: {last_y_position})")

            selectors = [
                "//button[contains(text(), '리뷰쓰기')]",
                "//button[contains(text(), '리뷰 쓰기')]",
                "//a[contains(text(), '리뷰쓰기')]",
                "//a[contains(text(), '리뷰 쓰기')]",
                "//span[contains(text(), '리뷰쓰기')]",
                "//*[contains(@class, 'review') and contains(text(), '쓰기')]",
                "//button[contains(., '리뷰') and contains(., '쓰기')]",
                "//button[contains(@class, 'btn') and contains(text(), '리뷰')]",
            ]

            visible_buttons = []

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        try:
                            if elem.is_displayed():
                                elem_y = elem.location['y']
                                if elem_y > last_y_position:
                                    if elem not in visible_buttons:
                                        visible_buttons.append(elem)
                        except:
                            continue
                except:
                    continue

            if not visible_buttons:
                self.log("더 이상 리뷰쓰기 버튼이 없습니다.", 'info')
                return (None, last_y_position)

            visible_buttons.sort(key=lambda btn: btn.location['y'])
            self.log(f"총 {len(visible_buttons)}개의 리뷰쓰기 버튼 발견, '포인트 최대' 확인 중...")

            last_checked_y = visible_buttons[-1].location['y'] if visible_buttons else last_y_position

            for idx, button in enumerate(visible_buttons, 1):
                try:
                    button_y = button.location['y']
                    parent = button

                    for level in range(15):
                        try:
                            parent = parent.find_element(By.XPATH, "..")
                            parent_text = parent.text

                            if "포인트 최대" in parent_text or ("최대" in parent_text and "원" in parent_text):
                                self.log(f"[{idx}/{len(visible_buttons)}] '포인트 최대' 상품 발견! (Y좌표: {button_y})", 'success')

                                match = re.search(r'포인트 최대\s*(\d+[\d,]*)\s*원', parent_text)
                                if match:
                                    point_amount = match.group(1)
                                    self.log(f"포인트: {point_amount}원", 'info')

                                return (button, button_y)
                        except:
                            continue

                    self.log(f"[{idx}/{len(visible_buttons)}] '포인트 최대'가 없는 상품 건너뜀", 'info')

                except Exception as e:
                    self.log(f"버튼 확인 중 오류: {str(e)}", 'warning')
                    continue

            self.log(f"현재 화면에 '포인트 최대' 상품 없음. 스크롤 계속", 'warning')
            return (None, last_checked_y)

        except Exception as e:
            self.log(f"버튼 찾기 실패: {str(e)}", 'error')
            return (None, last_y_position)

    def force_click(self, element, description: str = "요소") -> bool:
        """강제 클릭 함수"""
        try:
            element.click()
            self.log(f"{description} 클릭 성공 (일반)", 'info')
            return True
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                self.log(f"{description} 클릭 성공 (JavaScript)", 'info')
                return True
            except Exception:
                try:
                    self.driver.execute_script("""
                        var element = arguments[0];
                        var event = new MouseEvent('click', {
                            'view': window,
                            'bubbles': true,
                            'cancelable': true
                        });
                        element.dispatchEvent(event);
                    """, element)
                    self.log(f"{description} 클릭 성공 (이벤트 디스패치)", 'info')
                    return True
                except Exception as e:
                    self.log(f"{description} 클릭 실패: {str(e)}", 'warning')
                    return False

    def write_single_review(self, star_rating: int, review_text: str, image_paths: List[str] = None) -> bool:
        """단일 리뷰 작성"""
        try:
            time.sleep(2)

            # 팝업 창으로 전환
            main_window = self.driver.current_window_handle
            all_windows = self.driver.window_handles

            popup_found = False
            for window in all_windows:
                if window != main_window:
                    self.driver.switch_to.window(window)
                    self.log(f"팝업 창으로 전환 완료: {self.driver.current_url}")
                    popup_found = True
                    break

            if not popup_found:
                self.log("팝업 창을 찾을 수 없습니다", 'warning')
                return False

            time.sleep(3)
            self.log("팝업 로딩 완료, 리뷰 작성 시작...")

            # 1단계: 별점 5점 자동 선택
            self.log("1단계: 별점 5점 선택 중...")
            try:
                rating_count = 0

                best_selectors = [
                    "//button[contains(text(), '최고예요')]",
                    "//label[contains(text(), '최고예요')]",
                    "//*[contains(text(), '최고예요')]",
                ]

                for selector in best_selectors:
                    try:
                        for elem in self.driver.find_elements(By.XPATH, selector):
                            try:
                                if elem.is_displayed() and elem.is_enabled():
                                    self.force_click(elem, "최고예요 버튼")
                                    rating_count += 1
                                    time.sleep(0.2)
                            except:
                                continue
                    except:
                        continue

                star_selectors = [
                    "//button[contains(@class, 'star')]",
                    "//button[contains(@aria-label, '별')]",
                    "//*[contains(@class, 'rating')]//button",
                ]

                all_star_buttons = []
                for selector in star_selectors:
                    try:
                        for btn in self.driver.find_elements(By.XPATH, selector):
                            if btn.is_displayed():
                                all_star_buttons.append(btn)
                    except:
                        continue

                if all_star_buttons:
                    star_groups = {}
                    for btn in all_star_buttons:
                        try:
                            y_pos = btn.location['y']
                            found_group = False
                            for existing_y in list(star_groups.keys()):
                                if abs(existing_y - y_pos) < 10:
                                    star_groups[existing_y].append(btn)
                                    found_group = True
                                    break
                            if not found_group:
                                star_groups[y_pos] = [btn]
                        except:
                            continue

                    for y_pos, buttons in star_groups.items():
                        if len(buttons) >= 5:
                            sorted_btns = sorted(buttons, key=lambda b: b.location['x'])
                            rightmost = sorted_btns[-1]
                            if self.force_click(rightmost, "별점 5점"):
                                rating_count += 1
                                time.sleep(0.2)

                if rating_count > 0:
                    self.log(f"별점 5점 {rating_count}개 선택 완료!", 'success')
                else:
                    self.log("별점 버튼을 찾지 못했습니다", 'warning')
            except Exception as e:
                self.log(f"별점 선택 오류: {str(e)}", 'warning')

            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.3)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.3)

            # 한국어 어미 질문 자동 응답
            self.log("추가 질문 자동 응답 중...")
            try:
                korean_endings = (
                    '아요', '어요', '커요', '해요', '에요', '워요', '이에요', '예요', '았어요',
                    '나요', '까요', '가요', '죠', '네요', '데요', '래요', '던가요', '던데요',
                    '었어요', '였어요', '습니다', 'ㅂ니다', '대요', '세요', '싶어요', '같아요',
                    '되요', '니까', '군요', '거든요', '거예요', '요', '지요', '잖아요', '를까요',
                    '을까요', '나까요', '는가요', '을게요', '께요', '는데요', '던데요'
                )

                clicked_buttons = set()
                clicked_count = 0

                for elem in self.driver.find_elements(By.XPATH, "//*[text()]"):
                    try:
                        if not elem.is_displayed():
                            continue
                        text = elem.text.strip()
                        if not text or not text.endswith(korean_endings):
                            continue

                        btn = None
                        if elem.tag_name in ['a', 'button']:
                            btn = elem
                        else:
                            for xpath in ["./ancestor::button[1]", "./ancestor::a[1]", "./parent::button", "./parent::a"]:
                                try:
                                    btn = elem.find_element(By.XPATH, xpath)
                                    if btn.is_displayed():
                                        break
                                except:
                                    continue

                        if btn and id(btn) not in clicked_buttons:
                            if self.force_click(btn, text[:30]):
                                clicked_buttons.add(id(btn))
                                clicked_count += 1
                                time.sleep(0.05)
                    except:
                        continue

                if clicked_count > 0:
                    self.log(f"{clicked_count}개 질문 응답 완료!", 'success')
            except Exception as e:
                self.log(f"질문 응답 오류: {str(e)}", 'warning')

            time.sleep(0.3)

            # 2단계: 리뷰 텍스트 입력
            self.log("2단계: 리뷰 텍스트 입력 중...")
            try:
                if len(review_text) < 10:
                    review_text = review_text + " 정말 좋아요!" * ((10 - len(review_text)) // 7 + 1)

                textarea_selectors = [
                    "//textarea",
                    "//textarea[contains(@placeholder, '최소')]",
                    "//textarea[contains(@placeholder, '글자')]",
                    "//textarea[contains(@placeholder, '리뷰')]",
                    "//textarea[contains(@placeholder, '어떤')]",
                    "//*[@contenteditable='true']",
                ]

                textarea = None
                for selector in textarea_selectors:
                    try:
                        element = self.driver.find_element(By.XPATH, selector)
                        if element and element.is_displayed():
                            textarea = element
                            self.log(f"리뷰 입력창 발견!", 'info')
                            break
                    except:
                        continue

                if textarea:
                    textarea.clear()
                    time.sleep(0.3)
                    textarea.send_keys(review_text)
                    self.log(f"리뷰 텍스트 입력 완료! ({len(review_text)}자)", 'success')
                else:
                    self.log("리뷰 입력창을 찾지 못했습니다.", 'warning')

            except Exception as e:
                self.log(f"리뷰 텍스트 입력 중 오류: {str(e)}", 'warning')

            time.sleep(1.5)

            # 3단계: 사진 첨부
            if image_paths:
                self.log("3단계: 사진 첨부 중...")
                try:
                    attach_button_selectors = [
                        "//button[contains(text(), '사진')]",
                        "//button[contains(text(), '동영상')]",
                        "//button[contains(text(), '첨부')]",
                        "//*[contains(text(), '사진') and contains(text(), '동영상')]",
                        "//button[contains(@class, 'photo')]",
                        "//button[contains(@class, 'attach')]",
                        "//button[contains(., '사진')]",
                    ]

                    attach_button = None
                    for selector in attach_button_selectors:
                        try:
                            btn = self.driver.find_element(By.XPATH, selector)
                            if btn and btn.is_displayed() and btn.is_enabled():
                                attach_button = btn
                                self.log(f"'사진/동영상 첨부하기' 버튼 발견: {btn.text}", 'info')
                                break
                        except:
                            continue

                    if attach_button:
                        attach_button.click()
                        self.log("첨부 버튼 클릭", 'success')
                        time.sleep(1.5)

                        file_input_selectors = [
                            "//input[@type='file']",
                            "//input[@type='file' and contains(@accept, 'image')]",
                        ]

                        file_input = None
                        for selector in file_input_selectors:
                            try:
                                inputs = self.driver.find_elements(By.XPATH, selector)
                                for inp in inputs:
                                    file_input = inp
                            except:
                                continue

                        if file_input:
                            abs_image_paths = []
                            for img_path in image_paths:
                                if os.path.exists(img_path):
                                    abs_image_paths.append(os.path.abspath(img_path))
                                    self.log(f"이미지 파일 확인: {img_path}", 'info')
                                else:
                                    self.log(f"이미지 파일을 찾을 수 없음: {img_path}", 'warning')

                            if abs_image_paths:
                                all_images = "\n".join(abs_image_paths)
                                file_input.send_keys(all_images)
                                self.log(f"이미지 파일 {len(abs_image_paths)}개 추가 완료!", 'success')
                                time.sleep(2)

                                # 첨부완료 버튼 클릭
                                attach_complete_selectors = [
                                    "//button[contains(text(), '첨부완료')]",
                                    "//button[contains(text(), '완료')]",
                                    "//button[contains(text(), '확인')]",
                                    "//button[contains(@class, 'complete')]",
                                    "//button[contains(., '완료')]",
                                ]

                                attach_complete_btn = None
                                for selector in attach_complete_selectors:
                                    try:
                                        btn = self.driver.find_element(By.XPATH, selector)
                                        if btn and btn.is_displayed() and btn.is_enabled():
                                            attach_complete_btn = btn
                                            break
                                    except:
                                        continue

                                if attach_complete_btn:
                                    attach_complete_btn.click()
                                    self.log("'첨부완료' 버튼 클릭 완료!", 'success')
                                    time.sleep(2)

                except Exception as e:
                    self.log(f"이미지 첨부 중 오류: {str(e)}", 'warning')

            time.sleep(2)

            # 4단계: 최종 등록 버튼 클릭
            self.log("4단계: 리뷰 등록 중...")
            try:
                submit_selectors = [
                    "//button[contains(text(), '등록') and not(contains(text(), '첨부'))]",
                    "//button[@type='submit']",
                    "//button[contains(text(), '작성완료')]",
                    "//button[contains(text(), '리뷰등록')]",
                ]

                submit_btn = None
                for selector in submit_selectors:
                    try:
                        btn = self.driver.find_element(By.XPATH, selector)
                        if btn and btn.is_displayed() and btn.is_enabled():
                            submit_btn = btn
                            break
                    except:
                        continue

                if submit_btn:
                    submit_btn.click()
                    self.log("리뷰 등록 완료!", 'success')
                    time.sleep(2)
                else:
                    self.log("등록 버튼을 찾지 못했습니다.", 'warning')
                    try:
                        self.driver.switch_to.window(main_window)
                    except:
                        pass
                    return False

            except Exception as e:
                self.log(f"등록 실패: {str(e)}", 'warning')

            # 원래 창으로 돌아가기
            time.sleep(1)
            try:
                all_windows = self.driver.window_handles
                if len(all_windows) > 1:
                    for window in all_windows:
                        if window != main_window:
                            try:
                                self.driver.switch_to.window(window)
                                self.driver.close()
                            except:
                                pass

                self.driver.switch_to.window(main_window)
                self.log("메인 창으로 복귀")

                if "writable-reviews" not in self.driver.current_url:
                    self.log("리뷰 페이지로 돌아갑니다")
                    self.driver.get("https://shopping.naver.com/my/writable-reviews")
                    time.sleep(2)
            except Exception as e:
                self.log(f"창 전환 오류: {str(e)}", 'warning')

            return True

        except Exception as e:
            self.log(f"리뷰 작성 실패: {str(e)}", 'error')
            try:
                all_windows = self.driver.window_handles
                for window in all_windows:
                    try:
                        self.driver.switch_to.window(window)
                        if "writable-reviews" in self.driver.current_url:
                            return False
                    except:
                        continue
                self.driver.get("https://shopping.naver.com/my/writable-reviews")
                time.sleep(2)
            except:
                pass
            return False

    def run_automation(
        self,
        login_method: str,
        naver_id: str,
        naver_pw: str,
        reviews: List[dict],
        headless: bool = False
    ) -> dict:
        """자동화 실행 메인 함수

        Args:
            login_method: "auto" 또는 "manual"
            naver_id: 네이버 아이디
            naver_pw: 네이버 비밀번호
            reviews: 리뷰 데이터 리스트 [{"star_rating": 5, "review_text": "...", "image_paths": [...]}]
            headless: 헤드리스 모드 여부

        Returns:
            dict: 실행 결과 {"success": bool, "completed": int, "failed": int, "message": str}
        """
        result = {
            "success": False,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "total_points": 0,
            "message": ""
        }

        try:
            self.is_running = True
            self.session_id = str(uuid.uuid4())[:8]
            self.update_status("초기화 중...")

            # 1. 브라우저 초기화
            if not self.init_driver(headless):
                self.update_status("브라우저 초기화 실패")
                result["message"] = "브라우저 초기화 실패"
                self.is_running = False
                return result

            # 2. 로그인
            if login_method == 'auto':
                self.update_status("자동 로그인 중...")
                if not self.auto_login(naver_id, naver_pw):
                    self.update_status("로그인 실패")
                    result["message"] = "로그인 실패"
                    self.is_running = False
                    return result
            else:
                self.update_status("수동 로그인 대기 중...")
                if not self.manual_login_wait():
                    self.update_status("로그인 실패")
                    result["message"] = "로그인 시간 초과"
                    self.is_running = False
                    return result

            # 3. 리뷰 페이지로 이동
            self.update_status("리뷰 페이지로 이동 중...")
            if not self.go_to_review_page():
                self.update_status("페이지 이동 실패")
                result["message"] = "리뷰 페이지 이동 실패"
                self.is_running = False
                return result

            # 4. 순차적 리뷰 작성
            self.update_status("리뷰 작성 시작...")
            self.log("최상단 리뷰부터 순차적으로 작성합니다!")
            self.log(f"리뷰 템플릿 {len(reviews)}개를 순환하여 사용합니다.")

            completed_reviews = 0
            review_index = 0
            consecutive_no_button_count = 0
            max_consecutive_no_button = 5
            total_reviews = len(reviews)
            last_y_position = 0

            while self.is_running:
                try:
                    btn, last_checked_y = self.find_next_topmost_button(last_y_position)

                    if not btn:
                        self.log(f"'포인트 최대' 버튼 없음. 스크롤하여 계속 탐색...", 'warning')
                        last_y_position = last_checked_y

                        can_scroll = self.scroll_to_load_more()

                        if not can_scroll:
                            self.log("페이지 끝에 도달. 모든 '포인트 최대' 상품 처리 완료!", 'success')
                            break

                        time.sleep(1.5)
                        btn, last_checked_y = self.find_next_topmost_button(last_y_position)

                        if not btn:
                            consecutive_no_button_count += 1
                            if consecutive_no_button_count >= max_consecutive_no_button:
                                self.log("더 이상 '포인트 최대' 상품이 없습니다. 작업 완료!", 'success')
                                break
                            last_y_position = last_checked_y
                            continue
                        else:
                            consecutive_no_button_count = 0
                    else:
                        consecutive_no_button_count = 0
                        self.log(f"리뷰 {completed_reviews + 1} 작성 시작 (템플릿 #{(review_index % total_reviews) + 1} 사용)")

                    # 버튼 클릭
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.5)

                        btn_text = btn.text.strip()
                        self.log(f"버튼 클릭: {btn_text}")
                        btn.click()
                        time.sleep(2)

                        last_y_position = last_checked_y
                    except Exception as e:
                        self.log(f"버튼 클릭 실패: {str(e)}", 'warning')
                        self.driver.get("https://shopping.naver.com/my/writable-reviews")
                        time.sleep(2)
                        continue

                    # 리뷰 데이터 가져오기
                    review_data = reviews[review_index % total_reviews]
                    star_rating = review_data.get('star_rating', 5)
                    review_text = review_data.get('review_text', '좋은 상품입니다!')
                    image_paths = review_data.get('image_paths', [])

                    # 리뷰 작성
                    if self.write_single_review(star_rating, review_text, image_paths):
                        completed_reviews += 1
                        review_index += 1
                        result["completed"] = completed_reviews
                        self.log(f"리뷰 완료! (총 {completed_reviews}개 완료)", 'success')
                        self.update_status(f"리뷰 작성 중... ({completed_reviews}개 완료)", completed_reviews, 0)
                    else:
                        result["failed"] += 1
                        self.log(f"리뷰 작성 실패", 'warning')
                        review_index += 1

                    try:
                        if last_y_position > 0:
                            self.driver.execute_script(f"window.scrollTo(0, {last_y_position - 200});")
                            time.sleep(0.5)
                    except:
                        pass

                except Exception as e:
                    self.log(f"리뷰 작성 중 오류: {str(e)}", 'error')
                    result["failed"] += 1
                    review_index += 1
                    try:
                        all_windows = self.driver.window_handles
                        for window in all_windows:
                            try:
                                self.driver.switch_to.window(window)
                                if "writable-reviews" in self.driver.current_url:
                                    break
                            except:
                                continue
                        else:
                            self.driver.get("https://shopping.naver.com/my/writable-reviews")
                            time.sleep(2)
                    except:
                        pass
                    continue

            self.log(f"모든 리뷰쓰기 완료! (총 {completed_reviews}개 작성)", 'success')
            self.update_status("완료!", completed_reviews, completed_reviews)

            result["success"] = True
            result["message"] = f"총 {completed_reviews}개 리뷰 작성 완료"

        except Exception as e:
            self.log(f"자동화 실행 중 오류: {str(e)}", 'error')
            self.update_status("오류 발생")
            result["message"] = str(e)
        finally:
            self.is_running = False
            # 드라이버 종료
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None

        return result

    def stop(self):
        """자동화 중지"""
        self.is_running = False
        self.log("자동화 중지 요청됨", 'warning')
        self.update_status("중지됨")

        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def get_status(self) -> dict:
        """현재 상태 반환"""
        return {
            'is_running': self.is_running,
            'current': self.current_review,
            'total': self.total_reviews,
            'status': self.status,
            'session_id': self.session_id
        }


# 전역 봇 인스턴스 관리
_bot_instance: Optional[NaverReviewBot] = None


def get_bot_instance() -> Optional[NaverReviewBot]:
    """현재 봇 인스턴스 반환"""
    global _bot_instance
    return _bot_instance


def create_bot_instance(log_callback=None, status_callback=None) -> NaverReviewBot:
    """새 봇 인스턴스 생성"""
    global _bot_instance
    if _bot_instance and _bot_instance.is_running:
        _bot_instance.stop()
    _bot_instance = NaverReviewBot(log_callback, status_callback)
    return _bot_instance


def stop_bot():
    """현재 봇 중지"""
    global _bot_instance
    if _bot_instance:
        _bot_instance.stop()
        _bot_instance = None
