"""
쿠팡 윙 Playwright 클라이언트
- 로그인 및 세션 관리
- 쿠키 기반 세션 유지
- 공통 페이지 네비게이션
"""
import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Callable
from pathlib import Path
from loguru import logger

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. WingPlaywrightClient will not be available.")

# 한국 시간대
KST = timezone(timedelta(hours=9))

# 쿠키 저장 경로
WING_COOKIE_DIR = os.environ.get('WING_COOKIE_DIR', '/data/wing_cookies')


class WingPlaywrightClient:
    """쿠팡 윙 Playwright 클라이언트"""

    # 쿠팡 윙 URL
    WING_BASE_URL = "https://wing.coupang.com"
    WING_LOGIN_URL = "https://wing.coupang.com/"
    WING_CS_URL = "https://wing.coupang.com/tenants/cs/callcenter"

    def __init__(
        self,
        account_id: int = None,
        log_callback: Optional[Callable] = None
    ):
        self.account_id = account_id
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        self.username = None
        self._log_callback = log_callback

    def log(self, message: str, level: str = 'info'):
        """로그 메시지 출력"""
        if level == 'error':
            logger.error(f"[WingClient] {message}")
        elif level == 'warning':
            logger.warning(f"[WingClient] {message}")
        elif level == 'success':
            logger.success(f"[WingClient] {message}")
        else:
            logger.info(f"[WingClient] {message}")

        if self._log_callback:
            try:
                self._log_callback({
                    'time': datetime.now(KST).strftime("%H:%M:%S"),
                    'level': level,
                    'message': message
                })
            except Exception as e:
                logger.error(f"Log callback error: {e}")

    async def init_browser(self, headless: bool = True) -> bool:
        """브라우저 초기화"""
        if not PLAYWRIGHT_AVAILABLE:
            self.log("Playwright가 설치되지 않았습니다", 'error')
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
                viewport={'width': 1920, 'height': 1080},
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

            # 저장된 쿠키 로드
            await self._load_cookies()

            self.log("브라우저 초기화 완료!", 'success')
            return True

        except Exception as e:
            self.log(f"브라우저 초기화 실패: {e}", 'error')
            return False

    async def login(self, username: str, password: str) -> Dict:
        """
        쿠팡 윙 로그인

        Args:
            username: Wing 아이디
            password: Wing 비밀번호

        Returns:
            로그인 결과 딕셔너리
        """
        try:
            self.log("쿠팡 윙 로그인 시작...")

            # 로그인 페이지로 이동
            await self.page.goto(self.WING_LOGIN_URL, wait_until='networkidle')
            await asyncio.sleep(2)

            current_url = self.page.url
            self.log(f"현재 URL: {current_url}")

            # 이미 로그인된 상태인지 확인
            if "wing.coupang.com" in current_url and "xauth" not in current_url and "login" not in current_url.lower():
                self.log("이미 로그인된 상태입니다", 'success')
                self.is_logged_in = True
                self.username = username
                return {"success": True, "message": "이미 로그인됨"}

            # 로그인 폼 요소 찾기 (다양한 선택자 시도)
            username_selectors = ['#username', 'input[name="username"]', 'input[type="email"]', 'input[type="text"]']
            password_selectors = ['#password', 'input[name="password"]', 'input[type="password"]']
            login_btn_selectors = ['#kc-login', 'button[type="submit"]', 'input[type="submit"]', '.login-btn', 'button:has-text("로그인")']

            # 아이디 입력
            self.log("아이디 입력 중...")
            username_input = None
            for selector in username_selectors:
                try:
                    elem = await self.page.query_selector(selector)
                    if elem and await elem.is_visible():
                        username_input = elem
                        break
                except:
                    continue

            if username_input:
                await username_input.fill(username)
                await asyncio.sleep(0.5)
            else:
                self.log("아이디 입력 필드를 찾을 수 없습니다", 'error')
                await self._save_screenshot("login_no_username_field")
                return {"success": False, "error": "username_field_not_found", "message": "아이디 입력 필드를 찾을 수 없음"}

            # 비밀번호 입력
            self.log("비밀번호 입력 중...")
            password_input = None
            for selector in password_selectors:
                try:
                    elem = await self.page.query_selector(selector)
                    if elem and await elem.is_visible():
                        password_input = elem
                        break
                except:
                    continue

            if password_input:
                await password_input.fill(password)
                await asyncio.sleep(0.5)
            else:
                self.log("비밀번호 입력 필드를 찾을 수 없습니다", 'error')
                await self._save_screenshot("login_no_password_field")
                return {"success": False, "error": "password_field_not_found", "message": "비밀번호 입력 필드를 찾을 수 없음"}

            # 로그인 버튼 클릭
            self.log("로그인 버튼 클릭...")
            login_btn = None
            for selector in login_btn_selectors:
                try:
                    elem = await self.page.query_selector(selector)
                    if elem and await elem.is_visible():
                        login_btn = elem
                        break
                except:
                    continue

            if login_btn:
                await login_btn.click()
            else:
                # 엔터키로 시도
                await self.page.keyboard.press('Enter')

            self.log("로그인 처리 중...")
            await asyncio.sleep(5)

            # 로그인 결과 확인
            current_url = self.page.url

            if "wing.coupang.com" in current_url and "xauth" not in current_url and "login" not in current_url.lower():
                self.log("쿠팡 윙 로그인 성공!", 'success')
                self.is_logged_in = True
                self.username = username

                # 쿠키 저장
                await self._save_cookies()

                return {"success": True, "message": "로그인 성공"}
            else:
                self.log(f"로그인 실패 - 현재 URL: {current_url}", 'error')
                await self._save_screenshot("login_failed")

                # 에러 메시지 확인
                error_msg = ""
                try:
                    error_elem = await self.page.query_selector('.error-message, .alert-error, #error-message')
                    if error_elem:
                        error_msg = await error_elem.inner_text()
                except:
                    pass

                return {
                    "success": False,
                    "error": "login_failed",
                    "message": error_msg or "로그인 실패 - 아이디/비밀번호 확인 필요"
                }

        except Exception as e:
            self.log(f"로그인 오류: {e}", 'error')
            await self._save_screenshot("login_exception")
            return {"success": False, "error": "exception", "message": str(e)}

    async def check_login_status(self) -> bool:
        """로그인 상태 확인"""
        try:
            current_url = self.page.url

            # 윙 메인 페이지로 이동해서 확인
            await self.page.goto(self.WING_BASE_URL, wait_until='networkidle')
            await asyncio.sleep(2)

            new_url = self.page.url

            if "wing.coupang.com" in new_url and "xauth" not in new_url and "login" not in new_url.lower():
                self.is_logged_in = True
                return True
            else:
                self.is_logged_in = False
                return False

        except Exception as e:
            self.log(f"로그인 상태 확인 오류: {e}", 'error')
            return False

    async def navigate_to_cs_page(self) -> bool:
        """고객센터 문의 페이지로 이동"""
        try:
            self.log("고객센터 문의 페이지로 이동 중...")
            await self.page.goto(self.WING_CS_URL, wait_until='networkidle')
            await asyncio.sleep(2)

            current_url = self.page.url
            if "callcenter" in current_url or "cs" in current_url:
                self.log("고객센터 페이지 이동 완료", 'success')
                return True
            else:
                self.log(f"고객센터 페이지 이동 실패: {current_url}", 'error')
                return False

        except Exception as e:
            self.log(f"페이지 이동 실패: {e}", 'error')
            return False

    async def navigate_to_url(self, url: str) -> bool:
        """지정된 URL로 이동"""
        try:
            self.log(f"URL로 이동 중: {url}")
            await self.page.goto(url, wait_until='networkidle')
            await asyncio.sleep(2)
            return True
        except Exception as e:
            self.log(f"URL 이동 실패: {e}", 'error')
            return False

    async def _save_cookies(self):
        """쿠키 저장"""
        try:
            if self.context:
                cookies = await self.context.cookies()
                cookie_path = self._get_cookie_path()

                # 디렉토리 생성
                os.makedirs(os.path.dirname(cookie_path), exist_ok=True)

                with open(cookie_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'cookies': cookies,
                        'username': self.username,
                        'account_id': self.account_id,
                        'saved_at': datetime.now(KST).isoformat()
                    }, f, ensure_ascii=False, indent=2)

                self.log(f"쿠키 저장 완료: {len(cookies)}개")
        except Exception as e:
            self.log(f"쿠키 저장 실패: {e}", 'error')

    async def _load_cookies(self) -> bool:
        """저장된 쿠키 로드"""
        try:
            cookie_path = self._get_cookie_path()
            if os.path.exists(cookie_path):
                with open(cookie_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                cookies = data.get('cookies', [])
                if cookies and self.context:
                    await self.context.add_cookies(cookies)
                    self.username = data.get('username')
                    self.log(f"쿠키 로드 완료: {len(cookies)}개")
                    return True
        except Exception as e:
            self.log(f"쿠키 로드 실패: {e}", 'error')
        return False

    def _get_cookie_path(self) -> str:
        """계정별 쿠키 경로 반환"""
        if self.account_id:
            return os.path.join(WING_COOKIE_DIR, f'wing_cookies_{self.account_id}.json')
        return os.path.join(WING_COOKIE_DIR, 'wing_cookies_default.json')

    async def _save_screenshot(self, name: str):
        """스크린샷 저장 (디버깅용)"""
        try:
            if self.page:
                timestamp = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
                screenshot_dir = os.environ.get('SCREENSHOT_DIR', '/data/screenshots')
                os.makedirs(screenshot_dir, exist_ok=True)

                path = os.path.join(screenshot_dir, f'{name}_{timestamp}.png')
                await self.page.screenshot(path=path)
                self.log(f"스크린샷 저장: {path}")
        except Exception as e:
            self.log(f"스크린샷 저장 실패: {e}", 'error')

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
            self.is_logged_in = False

            self.log("브라우저 종료 완료")
        except Exception as e:
            self.log(f"브라우저 종료 실패: {e}", 'error')
