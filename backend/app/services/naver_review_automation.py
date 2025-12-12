"""
Naver Review Automation Service
네이버 리뷰 자동화 서비스 - Playwright 기반
"""
import os
import time
import re
import random
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Tuple, Callable, Dict
from loguru import logger

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. NaverReviewBot will not be available.")

# 하위 호환성을 위해 SELENIUM_AVAILABLE도 유지
SELENIUM_AVAILABLE = PLAYWRIGHT_AVAILABLE


class NaverReviewBot:
    """네이버 리뷰 자동화 봇 - Playwright 기반"""

    def __init__(self, log_callback: Optional[Callable] = None, status_callback: Optional[Callable] = None):
        """
        Args:
            log_callback: 로그 메시지 콜백 함수 (message, level)
            status_callback: 상태 업데이트 콜백 함수 (status, current, total)
        """
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

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

    async def init_browser(self, headless: bool = True) -> bool:
        """Playwright 브라우저 초기화"""
        if not PLAYWRIGHT_AVAILABLE:
            self.log("Playwright가 설치되지 않았습니다.", 'error')
            return False

        try:
            self.log("브라우저 초기화 중...")

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled'
                ]
            )

            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 900},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ko-KR'
            )

            # 봇 감지 우회
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko', 'en-US', 'en'] });
            """)

            self.page = await self.context.new_page()

            self.log("브라우저 초기화 완료!", 'success')
            return True

        except Exception as e:
            self.log(f"브라우저 초기화 실패: {str(e)}", 'error')
            return False

    async def close(self):
        """브라우저 종료"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            self.log("브라우저 종료 완료", 'info')

        except Exception as e:
            self.log(f"브라우저 종료 실패: {str(e)}", 'error')

    async def auto_login(self, naver_id: str, naver_pw: str) -> bool:
        """네이버 자동 로그인"""
        try:
            self.log("네이버 로그인 페이지로 이동 중...")
            await self.page.goto("https://nid.naver.com/nidlogin.login", wait_until='networkidle')
            await asyncio.sleep(2)

            self.log("아이디/비밀번호 입력 중...")

            # JavaScript로 직접 값 설정 (봇 감지 우회)
            await self.page.evaluate(f"document.getElementById('id').value = '{naver_id}'")
            await asyncio.sleep(0.5)
            await self.page.evaluate(f"document.getElementById('pw').value = '{naver_pw}'")
            await asyncio.sleep(0.5)

            # 로그인 버튼 클릭
            await self.page.click('#log\\.login')
            self.log("로그인 버튼 클릭 완료, 로그인 처리 중...")
            await asyncio.sleep(5)

            # 로그인 성공 확인
            current_url = self.page.url
            if "nid.naver.com" in current_url:
                self.log("로그인 실패 또는 추가 인증 필요", 'warning')
                self.log("수동으로 인증을 완료해주세요 (캡차, 2단계 인증 등)", 'warning')
                return False
            else:
                self.log("로그인 성공!", 'success')
                return True

        except Exception as e:
            self.log(f"로그인 실패: {str(e)}", 'error')
            return False

    async def manual_login_wait(self) -> bool:
        """수동 로그인 대기"""
        try:
            self.log("네이버 로그인 페이지로 이동 중...")
            await self.page.goto("https://nid.naver.com/nidlogin.login", wait_until='networkidle')
            self.log("브라우저에서 수동으로 로그인해주세요!", 'warning')
            self.log("로그인 완료 후 자동으로 계속됩니다...", 'info')

            # 로그인 완료 대기 (최대 5분)
            for i in range(60):
                if not self.is_running:
                    return False
                await asyncio.sleep(5)
                current_url = self.page.url
                if "nid.naver.com" not in current_url:
                    self.log("로그인 확인됨!", 'success')
                    return True
                self.log(f"로그인 대기 중... ({i*5}초)", 'info')

            self.log("로그인 시간 초과", 'warning')
            return False

        except Exception as e:
            self.log(f"수동 로그인 대기 실패: {str(e)}", 'error')
            return False

    async def go_to_review_page(self) -> bool:
        """네이버 쇼핑 리뷰 작성 페이지로 이동"""
        try:
            self.log("네이버 쇼핑 작성 가능한 리뷰 페이지로 이동 중...")
            await self.page.goto("https://shopping.naver.com/my/writable-reviews", wait_until='networkidle')
            await asyncio.sleep(3)

            # 페이지 스크롤 (모든 요소 로드)
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)

            self.log("리뷰 작성 페이지 로드 완료!", 'success')
            return True

        except Exception as e:
            self.log(f"리뷰 페이지 이동 실패: {str(e)}", 'error')
            return False

    async def scroll_to_load_more(self) -> bool:
        """페이지를 스크롤하여 더 많은 리뷰 로드"""
        try:
            current_url = self.page.url
            if "writable-reviews" not in current_url:
                self.log("리뷰 페이지가 아닙니다. 페이지로 돌아갑니다", 'warning')
                await self.page.goto("https://shopping.naver.com/my/writable-reviews", wait_until='networkidle')
                await asyncio.sleep(2)

            last_height = await self.page.evaluate("document.body.scrollHeight")
            self.log(f"페이지 스크롤 중... (현재 높이: {last_height}px)")

            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            new_height = await self.page.evaluate("document.body.scrollHeight")

            if new_height > last_height:
                self.log(f"새로운 콘텐츠 로드됨! (새 높이: {new_height}px)", 'success')
                return True
            else:
                self.log(f"페이지 끝에 도달! (높이: {new_height}px)", 'warning')
                return False

        except Exception as e:
            self.log(f"스크롤 오류: {str(e)}", 'error')
            return False

    async def find_next_topmost_button(self, last_y_position: int = 0) -> Tuple[Optional[any], int]:
        """마지막 처리한 위치보다 아래에 있는 '포인트 최대' 버튼 찾기"""
        try:
            await asyncio.sleep(0.5)
            self.log(f"리뷰쓰기 버튼 검색 중... (마지막 Y위치: {last_y_position})")

            # JavaScript로 버튼 찾기
            buttons_info = await self.page.evaluate(f"""
                () => {{
                    const selectors = [
                        "button:has-text('리뷰쓰기')",
                        "button:has-text('리뷰 쓰기')",
                        "a:has-text('리뷰쓰기')",
                        "a:has-text('리뷰 쓰기')"
                    ];

                    const results = [];
                    const allButtons = document.querySelectorAll('button, a');

                    for (const btn of allButtons) {{
                        const text = btn.textContent || '';
                        if (text.includes('리뷰쓰기') || text.includes('리뷰 쓰기')) {{
                            const rect = btn.getBoundingClientRect();
                            const y = rect.top + window.scrollY;

                            if (y > {last_y_position} && rect.width > 0 && rect.height > 0) {{
                                // 부모 요소에서 '포인트 최대' 확인
                                let parent = btn;
                                let hasPointMax = false;
                                let pointAmount = '';

                                for (let i = 0; i < 15; i++) {{
                                    parent = parent.parentElement;
                                    if (!parent) break;

                                    const parentText = parent.textContent || '';
                                    if (parentText.includes('포인트 최대') || (parentText.includes('최대') && parentText.includes('원'))) {{
                                        hasPointMax = true;
                                        const match = parentText.match(/포인트 최대\\s*(\\d[\\d,]*)\\s*원/);
                                        if (match) pointAmount = match[1];
                                        break;
                                    }}
                                }}

                                results.push({{
                                    y: y,
                                    hasPointMax: hasPointMax,
                                    pointAmount: pointAmount,
                                    index: results.length
                                }});
                            }}
                        }}
                    }}

                    // Y좌표로 정렬
                    results.sort((a, b) => a.y - b.y);
                    return results;
                }}
            """)

            if not buttons_info:
                self.log("더 이상 리뷰쓰기 버튼이 없습니다.", 'info')
                return (None, last_y_position)

            self.log(f"총 {len(buttons_info)}개의 리뷰쓰기 버튼 발견, '포인트 최대' 확인 중...")

            last_checked_y = buttons_info[-1]['y'] if buttons_info else last_y_position

            # 포인트 최대가 있는 첫 번째 버튼 찾기
            for idx, btn_info in enumerate(buttons_info, 1):
                if btn_info['hasPointMax']:
                    self.log(f"[{idx}/{len(buttons_info)}] '포인트 최대' 상품 발견! (Y좌표: {btn_info['y']})", 'success')
                    if btn_info['pointAmount']:
                        self.log(f"포인트: {btn_info['pointAmount']}원", 'info')

                    # 해당 버튼 요소 가져오기
                    button = await self._get_button_at_position(btn_info['y'])
                    return (button, btn_info['y'])
                else:
                    self.log(f"[{idx}/{len(buttons_info)}] '포인트 최대'가 없는 상품 건너뜀", 'info')

            self.log(f"현재 화면에 '포인트 최대' 상품 없음. 스크롤 계속", 'warning')
            return (None, last_checked_y)

        except Exception as e:
            self.log(f"버튼 찾기 실패: {str(e)}", 'error')
            return (None, last_y_position)

    async def _get_button_at_position(self, target_y: int):
        """특정 Y 위치의 버튼 요소 반환"""
        try:
            # 해당 위치의 버튼 찾기
            buttons = await self.page.query_selector_all('button, a')
            for btn in buttons:
                try:
                    text = await btn.text_content()
                    if text and ('리뷰쓰기' in text or '리뷰 쓰기' in text):
                        box = await btn.bounding_box()
                        if box:
                            scroll_y = await self.page.evaluate("window.scrollY")
                            btn_y = box['y'] + scroll_y
                            if abs(btn_y - target_y) < 10:
                                return btn
                except:
                    continue
            return None
        except:
            return None

    async def force_click(self, element, description: str = "요소") -> bool:
        """강제 클릭 함수"""
        try:
            await element.click()
            self.log(f"{description} 클릭 성공", 'info')
            return True
        except Exception:
            try:
                await self.page.evaluate("arguments[0].click()", element)
                self.log(f"{description} 클릭 성공 (JavaScript)", 'info')
                return True
            except Exception as e:
                self.log(f"{description} 클릭 실패: {str(e)}", 'warning')
                return False

    async def write_single_review(self, star_rating: int, review_text: str, image_paths: List[str] = None) -> bool:
        """단일 리뷰 작성"""
        try:
            await asyncio.sleep(2)

            # 팝업 창으로 전환
            main_page = self.page
            all_pages = self.context.pages

            popup_page = None
            for page in all_pages:
                if page != main_page:
                    popup_page = page
                    self.log(f"팝업 창으로 전환 완료: {page.url}")
                    break

            if not popup_page:
                # 새 페이지 대기
                try:
                    popup_page = await self.context.wait_for_event('page', timeout=5000)
                    self.log(f"새 팝업 창 감지: {popup_page.url}")
                except:
                    self.log("팝업 창을 찾을 수 없습니다", 'warning')
                    return False

            await popup_page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            self.log("팝업 로딩 완료, 리뷰 작성 시작...")

            # 1단계: 별점 5점 자동 선택
            self.log("1단계: 별점 5점 선택 중...")
            try:
                rating_count = 0

                # "최고예요" 버튼 찾기
                best_buttons = await popup_page.query_selector_all('button, label, span')
                for elem in best_buttons:
                    try:
                        text = await elem.text_content()
                        if text and '최고예요' in text:
                            visible = await elem.is_visible()
                            if visible:
                                await elem.click()
                                rating_count += 1
                                await asyncio.sleep(0.2)
                    except:
                        continue

                # 별점 버튼 클릭 (5번째 별)
                star_buttons = await popup_page.query_selector_all('button[class*="star"], button[aria-label*="별"]')
                if star_buttons and len(star_buttons) >= 5:
                    await star_buttons[4].click()  # 5번째 별
                    rating_count += 1

                if rating_count > 0:
                    self.log(f"별점 5점 선택 완료!", 'success')
                else:
                    self.log("별점 버튼을 찾지 못했습니다", 'warning')

            except Exception as e:
                self.log(f"별점 선택 오류: {str(e)}", 'warning')

            await asyncio.sleep(1)
            await popup_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.3)
            await popup_page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.3)

            # 한국어 어미 질문 자동 응답
            self.log("추가 질문 자동 응답 중...")
            try:
                korean_endings = (
                    '아요', '어요', '커요', '해요', '에요', '워요', '이에요', '예요', '았어요',
                    '나요', '까요', '가요', '죠', '네요', '데요', '래요', '던가요', '던데요',
                    '었어요', '였어요', '습니다', '대요', '세요', '싶어요', '같아요',
                    '되요', '니까', '군요', '거든요', '거예요', '요', '지요', '잖아요'
                )

                clicked_count = 0
                all_elements = await popup_page.query_selector_all('button, a')

                for elem in all_elements:
                    try:
                        text = await elem.text_content()
                        if text:
                            text = text.strip()
                            if text.endswith(korean_endings):
                                visible = await elem.is_visible()
                                if visible:
                                    await elem.click()
                                    clicked_count += 1
                                    await asyncio.sleep(0.05)
                    except:
                        continue

                if clicked_count > 0:
                    self.log(f"{clicked_count}개 질문 응답 완료!", 'success')

            except Exception as e:
                self.log(f"질문 응답 오류: {str(e)}", 'warning')

            await asyncio.sleep(0.3)

            # 2단계: 리뷰 텍스트 입력
            self.log("2단계: 리뷰 텍스트 입력 중...")
            try:
                if len(review_text) < 10:
                    review_text = review_text + " 정말 좋아요!" * ((10 - len(review_text)) // 7 + 1)

                textarea = await popup_page.query_selector('textarea')
                if not textarea:
                    textarea = await popup_page.query_selector('[contenteditable="true"]')

                if textarea:
                    await textarea.fill('')
                    await asyncio.sleep(0.3)
                    await textarea.fill(review_text)
                    self.log(f"리뷰 텍스트 입력 완료! ({len(review_text)}자)", 'success')
                else:
                    self.log("리뷰 입력창을 찾지 못했습니다.", 'warning')

            except Exception as e:
                self.log(f"리뷰 텍스트 입력 중 오류: {str(e)}", 'warning')

            await asyncio.sleep(1.5)

            # 3단계: 사진 첨부
            if image_paths:
                self.log("3단계: 사진 첨부 중...")
                try:
                    # 첨부 버튼 찾기
                    attach_button = None
                    buttons = await popup_page.query_selector_all('button')
                    for btn in buttons:
                        try:
                            text = await btn.text_content()
                            if text and ('사진' in text or '동영상' in text or '첨부' in text):
                                visible = await btn.is_visible()
                                if visible:
                                    attach_button = btn
                                    self.log(f"'사진/동영상 첨부' 버튼 발견: {text.strip()}", 'info')
                                    break
                        except:
                            continue

                    if attach_button:
                        await attach_button.click()
                        self.log("첨부 버튼 클릭", 'success')
                        await asyncio.sleep(1.5)

                        # 파일 input 찾기
                        file_input = await popup_page.query_selector('input[type="file"]')

                        if file_input:
                            valid_paths = []
                            for img_path in image_paths:
                                if os.path.exists(img_path):
                                    valid_paths.append(os.path.abspath(img_path))
                                    self.log(f"이미지 파일 확인: {img_path}", 'info')
                                else:
                                    self.log(f"이미지 파일을 찾을 수 없음: {img_path}", 'warning')

                            if valid_paths:
                                await file_input.set_input_files(valid_paths)
                                self.log(f"이미지 파일 {len(valid_paths)}개 추가 완료!", 'success')
                                await asyncio.sleep(2)

                                # 첨부완료 버튼 클릭
                                complete_buttons = await popup_page.query_selector_all('button')
                                for btn in complete_buttons:
                                    try:
                                        text = await btn.text_content()
                                        if text and ('첨부완료' in text or '완료' in text or '확인' in text):
                                            visible = await btn.is_visible()
                                            if visible:
                                                await btn.click()
                                                self.log("'첨부완료' 버튼 클릭 완료!", 'success')
                                                await asyncio.sleep(2)
                                                break
                                    except:
                                        continue

                except Exception as e:
                    self.log(f"이미지 첨부 중 오류: {str(e)}", 'warning')

            await asyncio.sleep(2)

            # 4단계: 최종 등록 버튼 클릭
            self.log("4단계: 리뷰 등록 중...")
            try:
                submit_btn = None
                buttons = await popup_page.query_selector_all('button')

                for btn in buttons:
                    try:
                        text = await btn.text_content()
                        if text:
                            text = text.strip()
                            if ('등록' in text and '첨부' not in text) or text == '작성완료' or text == '리뷰등록':
                                visible = await btn.is_visible()
                                enabled = await btn.is_enabled()
                                if visible and enabled:
                                    submit_btn = btn
                                    break
                    except:
                        continue

                if submit_btn:
                    await submit_btn.click()
                    self.log("리뷰 등록 완료!", 'success')
                    await asyncio.sleep(2)
                else:
                    self.log("등록 버튼을 찾지 못했습니다.", 'warning')
                    return False

            except Exception as e:
                self.log(f"등록 실패: {str(e)}", 'warning')

            # 팝업 닫기 및 메인 페이지로 복귀
            await asyncio.sleep(1)
            try:
                all_pages = self.context.pages
                for page in all_pages:
                    if page != main_page:
                        try:
                            await page.close()
                        except:
                            pass

                self.page = main_page
                self.log("메인 창으로 복귀")

                if "writable-reviews" not in main_page.url:
                    self.log("리뷰 페이지로 돌아갑니다")
                    await main_page.goto("https://shopping.naver.com/my/writable-reviews", wait_until='networkidle')
                    await asyncio.sleep(2)

            except Exception as e:
                self.log(f"창 전환 오류: {str(e)}", 'warning')

            return True

        except Exception as e:
            self.log(f"리뷰 작성 실패: {str(e)}", 'error')
            try:
                await self.page.goto("https://shopping.naver.com/my/writable-reviews", wait_until='networkidle')
                await asyncio.sleep(2)
            except:
                pass
            return False

    async def run_automation_async(
        self,
        login_method: str,
        naver_id: str,
        naver_pw: str,
        reviews: List[dict],
        headless: bool = False
    ) -> dict:
        """자동화 실행 메인 함수 (비동기)"""
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
            if not await self.init_browser(headless):
                self.update_status("브라우저 초기화 실패")
                result["message"] = "브라우저 초기화 실패"
                self.is_running = False
                return result

            # 2. 로그인
            if login_method == 'auto':
                self.update_status("자동 로그인 중...")
                if not await self.auto_login(naver_id, naver_pw):
                    self.update_status("로그인 실패")
                    result["message"] = "로그인 실패"
                    self.is_running = False
                    return result
            else:
                self.update_status("수동 로그인 대기 중...")
                if not await self.manual_login_wait():
                    self.update_status("로그인 실패")
                    result["message"] = "로그인 시간 초과"
                    self.is_running = False
                    return result

            # 3. 리뷰 페이지로 이동
            self.update_status("리뷰 페이지로 이동 중...")
            if not await self.go_to_review_page():
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
                    btn, last_checked_y = await self.find_next_topmost_button(last_y_position)

                    if not btn:
                        self.log(f"'포인트 최대' 버튼 없음. 스크롤하여 계속 탐색...", 'warning')
                        last_y_position = last_checked_y

                        can_scroll = await self.scroll_to_load_more()

                        if not can_scroll:
                            self.log("페이지 끝에 도달. 모든 '포인트 최대' 상품 처리 완료!", 'success')
                            break

                        await asyncio.sleep(1.5)
                        btn, last_checked_y = await self.find_next_topmost_button(last_y_position)

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
                        await self.page.evaluate("arguments[0].scrollIntoView({block: 'center'})", btn)
                        await asyncio.sleep(0.5)

                        await btn.click()
                        await asyncio.sleep(2)

                        last_y_position = last_checked_y
                    except Exception as e:
                        self.log(f"버튼 클릭 실패: {str(e)}", 'warning')
                        await self.page.goto("https://shopping.naver.com/my/writable-reviews", wait_until='networkidle')
                        await asyncio.sleep(2)
                        continue

                    # 리뷰 데이터 가져오기
                    review_data = reviews[review_index % total_reviews]
                    star_rating = review_data.get('star_rating', 5)
                    review_text = review_data.get('review_text', '좋은 상품입니다!')
                    image_paths = review_data.get('image_paths', [])

                    # 리뷰 작성
                    if await self.write_single_review(star_rating, review_text, image_paths):
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
                            await self.page.evaluate(f"window.scrollTo(0, {last_y_position - 200})")
                            await asyncio.sleep(0.5)
                    except:
                        pass

                except Exception as e:
                    self.log(f"리뷰 작성 중 오류: {str(e)}", 'error')
                    result["failed"] += 1
                    review_index += 1
                    try:
                        await self.page.goto("https://shopping.naver.com/my/writable-reviews", wait_until='networkidle')
                        await asyncio.sleep(2)
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
            await self.close()

        return result

    def run_automation(
        self,
        login_method: str,
        naver_id: str,
        naver_pw: str,
        reviews: List[dict],
        headless: bool = False
    ) -> dict:
        """자동화 실행 메인 함수 (동기 래퍼)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.run_automation_async(login_method, naver_id, naver_pw, reviews, headless)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Automation error: {e}")
            return {
                "success": False,
                "completed": 0,
                "failed": 0,
                "message": str(e)
            }

    def stop(self):
        """자동화 중지"""
        self.is_running = False
        self.log("자동화 중지 요청됨", 'warning')
        self.update_status("중지됨")

        # 비동기 종료는 별도 처리 필요
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.close())
            loop.close()
        except:
            pass

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
