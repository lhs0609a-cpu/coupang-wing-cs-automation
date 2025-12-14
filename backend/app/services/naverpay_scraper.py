"""
네이버페이 배송 정보 스크래핑 서비스
Playwright를 사용한 자동화 (쿠키 기반 세션 유지)
"""
import asyncio
import logging
import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, AsyncGenerator

# 한국 시간대 (UTC+9)
KST = timezone(timedelta(hours=9))
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# 쿠키 저장 경로 (서버 배포 시 /data 볼륨 사용)
COOKIE_STORAGE_PATH = os.environ.get('COOKIE_STORAGE_PATH', '/data/naver_cookies.json')

# 스크래핑 로그 저장
class ScrapeLogger:
    """스크래핑 로그 수집기"""

    def __init__(self, max_logs: int = 100):
        self.logs: List[Dict] = []
        self.max_logs = max_logs

    def add(self, level: str, message: str, details: Optional[Dict] = None):
        """로그 추가"""
        log_entry = {
            "timestamp": datetime.now(KST).isoformat(),
            "level": level,
            "message": message,
            "details": details or {}
        }
        self.logs.append(log_entry)
        # 최대 개수 유지
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        # 표준 로거에도 기록
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

    def info(self, message: str, details: Optional[Dict] = None):
        self.add("info", message, details)

    def warning(self, message: str, details: Optional[Dict] = None):
        self.add("warning", message, details)

    def error(self, message: str, details: Optional[Dict] = None):
        self.add("error", message, details)

    def get_logs(self, limit: int = 50) -> List[Dict]:
        """최근 로그 반환"""
        return self.logs[-limit:]

    def clear(self):
        """로그 초기화"""
        self.logs = []


# 전역 로그 수집기
scrape_logger = ScrapeLogger()
# 로컬 개발 시 fallback
if not os.path.exists(os.path.dirname(COOKIE_STORAGE_PATH)):
    COOKIE_STORAGE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'naver_cookies.json')


@dataclass
class DeliveryItem:
    """배송 정보 데이터 클래스"""
    recipient: str
    courier: str
    tracking_number: str
    product_name: Optional[str] = None
    order_date: Optional[str] = None


class NaverPayScraper:
    """네이버페이 배송 정보 스크래퍼 (쿠키 기반 세션 유지)"""

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        self.username = None
        self.last_login_check = None

    async def init_browser(self, headless: bool = True):
        """브라우저 초기화"""
        try:
            from playwright.async_api import async_playwright

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
                    '--disable-gpu'
                ]
            )

            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ko-KR'
            )

            self.page = await self.context.new_page()

            # 저장된 쿠키가 있으면 로드
            await self._load_cookies()

            logger.info("브라우저 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"브라우저 초기화 실패: {e}")
            return False

    async def _save_cookies(self):
        """쿠키를 파일에 저장"""
        try:
            if self.context:
                cookies = await self.context.cookies()
                # 디렉토리 생성
                os.makedirs(os.path.dirname(COOKIE_STORAGE_PATH), exist_ok=True)
                with open(COOKIE_STORAGE_PATH, 'w', encoding='utf-8') as f:
                    json.dump({
                        'cookies': cookies,
                        'username': self.username,
                        'saved_at': datetime.now(KST).isoformat()
                    }, f, ensure_ascii=False, indent=2)
                logger.info(f"쿠키 저장 완료: {len(cookies)}개")
        except Exception as e:
            logger.error(f"쿠키 저장 실패: {e}")

    async def _load_cookies(self):
        """저장된 쿠키 로드"""
        try:
            if os.path.exists(COOKIE_STORAGE_PATH):
                with open(COOKIE_STORAGE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                cookies = data.get('cookies', [])
                if cookies and self.context:
                    await self.context.add_cookies(cookies)
                    self.username = data.get('username')
                    logger.info(f"쿠키 로드 완료: {len(cookies)}개, 사용자: {self.username}")
                    return True
        except Exception as e:
            logger.error(f"쿠키 로드 실패: {e}")
        return False

    async def _verify_login_status(self) -> bool:
        """실제 로그인 상태 확인 (네이버 페이지 접근)"""
        try:
            if not self.page:
                return False

            # 네이버 메인 페이지로 이동하여 로그인 상태 확인
            await self.page.goto('https://www.naver.com', wait_until='domcontentloaded')
            await asyncio.sleep(1)

            # 로그인 버튼이 있으면 로그아웃 상태
            login_btn = await self.page.query_selector('.MyView-module__link_login___HpHMW, .link_login, [class*="login"]')
            if login_btn:
                btn_text = await login_btn.inner_text()
                if '로그인' in btn_text:
                    self.is_logged_in = False
                    return False

            # 로그인 상태 확인 완료
            self.is_logged_in = True
            self.last_login_check = datetime.now(KST)
            return True

        except Exception as e:
            logger.error(f"로그인 상태 확인 실패: {e}")
            return False

    async def ensure_logged_in(self) -> bool:
        """로그인 상태 보장 (쿠키 복원 시도)"""
        if not self.browser:
            await self.init_browser(headless=True)

        # 쿠키가 로드되었으면 실제 로그인 상태 확인
        if await self._verify_login_status():
            return True

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
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()

            self.is_logged_in = False
            logger.info("브라우저 종료 완료")

        except Exception as e:
            logger.error(f"브라우저 종료 실패: {e}")

    async def login(self, username: str, password: str) -> Dict:
        """
        네이버 로그인

        Args:
            username: 네이버 아이디
            password: 네이버 비밀번호

        Returns:
            로그인 결과 딕셔너리
        """
        try:
            if not self.browser:
                await self.init_browser(headless=True)

            # 네이버 로그인 페이지로 이동
            await self.page.goto('https://nid.naver.com/nidlogin.login', wait_until='networkidle')
            await asyncio.sleep(1)

            # 아이디 입력
            await self.page.evaluate(f'''
                document.querySelector('#id').value = "{username}";
            ''')
            await asyncio.sleep(0.5)

            # 비밀번호 입력
            await self.page.evaluate(f'''
                document.querySelector('#pw').value = "{password}";
            ''')
            await asyncio.sleep(0.5)

            # 로그인 버튼 클릭
            await self.page.click('#log\\.login')
            await asyncio.sleep(3)

            # 로그인 성공 여부 확인
            current_url = self.page.url

            # 캡차 확인
            if 'captcha' in current_url.lower():
                return {
                    "success": False,
                    "error": "captcha_required",
                    "message": "캡차 인증이 필요합니다. 잠시 후 다시 시도해주세요."
                }

            # 2단계 인증 확인
            if 'otp' in current_url.lower() or 'protect' in current_url.lower():
                return {
                    "success": False,
                    "error": "2fa_required",
                    "message": "2단계 인증이 필요합니다."
                }

            # 로그인 실패 (로그인 페이지에 머물러 있음)
            if 'nidlogin' in current_url:
                return {
                    "success": False,
                    "error": "login_failed",
                    "message": "아이디 또는 비밀번호가 올바르지 않습니다."
                }

            self.is_logged_in = True
            self.username = username
            self.last_login_check = datetime.now(KST)
            logger.info(f"네이버 로그인 성공: {username}")

            # 로그인 성공 시 쿠키 저장
            await self._save_cookies()

            return {
                "success": True,
                "message": "로그인 성공",
                "username": username
            }

        except Exception as e:
            logger.error(f"로그인 중 오류: {e}")
            return {
                "success": False,
                "error": "exception",
                "message": str(e)
            }

    async def scrape_deliveries(self) -> AsyncGenerator[Dict, None]:
        """
        배송중인 상품 정보 스크래핑 (스트리밍)
        - 배송중/배송준비중 페이지로 이동
        - 각 상품을 클릭하여 상세 페이지에서 수령인 확인
        - 배송조회 버튼 클릭하여 택배사/송장번호 추출

        Yields:
            배송 정보 또는 진행 상황 메시지
        """
        import re
        scrape_logger.info("=== 배송 정보 수집 시작 ===")

        if not self.is_logged_in:
            scrape_logger.error("로그인되지 않은 상태입니다")
            yield {"type": "error", "message": "로그인이 필요합니다"}
            return

        scrape_logger.info(f"로그인 상태 확인: 사용자={self.username}")
        deliveries = []

        try:
            # 배송중/배송준비중 페이지로 이동
            delivery_url = 'https://pay.naver.com/pc/history?statusGroup=DELIVERING&page=1'
            yield {"type": "status", "message": "배송중 목록 페이지로 이동 중..."}
            scrape_logger.info(f"배송중 목록 페이지로 이동: {delivery_url}")

            try:
                await self.page.goto(
                    delivery_url,
                    wait_until='domcontentloaded',
                    timeout=30000
                )
                scrape_logger.info("페이지 로드 완료")
            except Exception as nav_error:
                scrape_logger.warning(f"네비게이션 오류: {nav_error}")

            await asyncio.sleep(3)
            current_url = self.page.url
            scrape_logger.info(f"현재 URL: {current_url}")

            yield {"type": "status", "message": "상품 목록 검색 중..."}

            # 페이지 스크롤하여 모든 항목 로드 (무한 스크롤 대응)
            scrape_logger.info("페이지 스크롤 시작")
            last_height = 0
            scroll_count = 0
            max_scrolls = 20  # 최대 스크롤 횟수

            while scroll_count < max_scrolls:
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(1.5)
                new_height = await self.page.evaluate('document.body.scrollHeight')
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_count += 1
                scrape_logger.info(f"스크롤 {scroll_count}회 완료")

            scrape_logger.info("페이지 스크롤 완료")

            # 상품 항목 찾기 - ProductName_article 클래스를 가진 div가 각 상품
            product_items = await self.page.query_selector_all('[class*="ProductName_article"]')
            scrape_logger.info(f"상품 항목 {len(product_items)}개 발견")

            if not product_items:
                # 대체 셀렉터 시도
                product_items = await self.page.query_selector_all('[class*="ProductName_name"]')
                scrape_logger.info(f"대체 셀렉터로 {len(product_items)}개 발견")

            total_products = len(product_items)
            yield {"type": "status", "message": f"{total_products}개 상품 발견, 상세 정보 수집 중..."}

            # 중복 방지
            processed_tracking_numbers = set()

            for idx in range(total_products):
                try:
                    scrape_logger.info(f"상품 {idx + 1}/{total_products} 처리 중...")
                    yield {"type": "status", "message": f"상품 {idx + 1}/{total_products} 처리 중..."}

                    # 매번 상품 목록을 새로 조회 (DOM이 변경될 수 있음)
                    product_items = await self.page.query_selector_all('[class*="ProductName_article"]')
                    if idx >= len(product_items):
                        scrape_logger.warning(f"상품 인덱스 {idx} 초과, 건너뜀")
                        continue

                    product_item = product_items[idx]

                    # 상품명 추출
                    product_name = ""
                    name_elem = await product_item.query_selector('[class*="ProductName_name"], [class*="ProductNameHighlightByKeyword"]')
                    if name_elem:
                        product_name = await name_elem.inner_text()
                        product_name = product_name.strip()
                    scrape_logger.info(f"상품명: {product_name[:50] if product_name else '(알수없음)'}...")

                    # 상품 클릭하여 상세 페이지로 이동
                    await product_item.click()
                    await asyncio.sleep(2)
                    scrape_logger.info(f"상세 페이지 이동 완료: {self.page.url[:60]}...")

                    # 수령인 추출 - DeliveryContent_name 클래스
                    recipient = ""
                    recipient_elem = await self.page.query_selector('[class*="DeliveryContent_name"]')
                    if recipient_elem:
                        recipient_text = await recipient_elem.inner_text()
                        # "배송지명" 텍스트 제거하고 괄호 안 내용 제거
                        recipient = recipient_text.replace("배송지명", "").strip()
                        # 괄호와 그 내용 제거 (예: "박수정(박수정)" -> "박수정")
                        recipient = re.sub(r'\([^)]*\)', '', recipient).strip()
                    scrape_logger.info(f"수령인: {recipient}")

                    # 배송조회 버튼 찾기 및 클릭
                    courier = ""
                    tracking_number = ""

                    delivery_btn = await self.page.query_selector('button:has-text("배송조회"), [class*="AssignmentButtonGroup"] button:has-text("배송조회")')
                    if not delivery_btn:
                        # 대체 셀렉터
                        delivery_btn = await self.page.query_selector('[class*="AssignmentButtonGroup_text"]:has-text("배송조회")')
                        if delivery_btn:
                            delivery_btn = await delivery_btn.evaluate_handle('el => el.closest("button")')

                    if delivery_btn:
                        scrape_logger.info("배송조회 버튼 발견, 클릭 중...")
                        await delivery_btn.click()
                        await asyncio.sleep(2)
                        scrape_logger.info(f"배송조회 페이지 이동: {self.page.url[:60]}...")

                        # 택배사 추출 - Courier_company 클래스
                        courier_elem = await self.page.query_selector('[class*="Courier_company"]')
                        if courier_elem:
                            courier = await courier_elem.inner_text()
                            courier = courier.strip()
                        scrape_logger.info(f"택배사: {courier}")

                        # 송장번호 추출 - Courier_number 클래스
                        tracking_elem = await self.page.query_selector('[class*="Courier_number"]')
                        if tracking_elem:
                            tracking_number = await tracking_elem.inner_text()
                            tracking_number = tracking_number.strip()
                        scrape_logger.info(f"송장번호: {tracking_number}")
                    else:
                        scrape_logger.warning("배송조회 버튼을 찾을 수 없음")

                    scrape_logger.info(f"추출 결과: 수령인={recipient}, 택배사={courier}, 송장={tracking_number}")

                    # 중복 체크 후 저장
                    if tracking_number and tracking_number not in processed_tracking_numbers:
                        processed_tracking_numbers.add(tracking_number)

                        delivery = DeliveryItem(
                            recipient=recipient,
                            courier=courier,
                            tracking_number=tracking_number,
                            product_name=product_name[:100] if product_name else ""
                        )
                        deliveries.append(delivery)

                        yield {
                            "type": "delivery",
                            "data": {
                                "recipient": delivery.recipient,
                                "courier": delivery.courier,
                                "tracking_number": delivery.tracking_number,
                                "product_name": delivery.product_name
                            }
                        }
                    elif tracking_number:
                        scrape_logger.info(f"중복 송장번호, 건너뜀: {tracking_number}")

                    # 목록 페이지로 돌아가기
                    await self.page.goto(delivery_url, wait_until='domcontentloaded', timeout=15000)
                    await asyncio.sleep(2)

                    # 스크롤하여 다음 상품 로드
                    for _ in range(min(idx // 3 + 1, 5)):
                        await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await asyncio.sleep(0.5)

                except Exception as e:
                    scrape_logger.warning(f"상품 {idx + 1} 처리 오류: {e}")
                    # 오류 발생 시 목록 페이지로 복귀 시도
                    try:
                        await self.page.goto(delivery_url, wait_until='domcontentloaded', timeout=15000)
                        await asyncio.sleep(2)
                    except:
                        pass
                    continue

            scrape_logger.info(f"수집 완료: {len(deliveries)}건")

            yield {
                "type": "complete",
                "message": f"수집 완료: {len(deliveries)}건",
                "total": len(deliveries)
            }

        except Exception as e:
            scrape_logger.error(f"스크래핑 오류: {e}")
            yield {"type": "error", "message": str(e)}

    async def scrape_deliveries_sync(self) -> List[Dict]:
        """
        배송중인 상품 정보 스크래핑 (동기식 결과 반환)

        Returns:
            배송 정보 리스트
        """
        deliveries = []
        async for result in self.scrape_deliveries():
            if result["type"] == "delivery":
                deliveries.append(result["data"])
        return deliveries

    def _parse_tracking_info(self, text: str) -> tuple:
        """택배사와 송장번호 파싱"""
        import re

        # 일반적인 패턴: "CJ대한통운 123456789012"
        patterns = [
            r'(CJ대한통운|우체국택배|한진택배|롯데택배|로젠택배|경동택배|대신택배)[:\s]*(\d{10,14})',
            r'(\w+택배)[:\s]*(\d{10,14})',
            r'송장[:\s]*(\d{10,14})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2:
                    return match.group(1), match.group(2)
                elif len(match.groups()) == 1:
                    return "", match.group(1)

        # 숫자만 추출 시도
        numbers = re.findall(r'\d{10,14}', text)
        if numbers:
            return "", numbers[0]

        return "", ""

    async def get_login_status(self) -> Dict:
        """로그인 상태 확인"""
        # 저장된 쿠키 정보 확인
        cookie_info = None
        if os.path.exists(COOKIE_STORAGE_PATH):
            try:
                with open(COOKIE_STORAGE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cookie_info = {
                        'saved_at': data.get('saved_at'),
                        'username': data.get('username')
                    }
            except:
                pass

        return {
            "is_logged_in": self.is_logged_in,
            "username": self.username,
            "last_login_check": self.last_login_check.isoformat() if self.last_login_check else None,
            "has_saved_session": cookie_info is not None,
            "saved_session": cookie_info
        }


# 싱글톤 인스턴스
_scraper_instance: Optional[NaverPayScraper] = None


async def get_scraper() -> NaverPayScraper:
    """스크래퍼 싱글톤 인스턴스 반환"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = NaverPayScraper()
    return _scraper_instance


async def reset_scraper():
    """스크래퍼 인스턴스 리셋"""
    global _scraper_instance
    if _scraper_instance:
        await _scraper_instance.close()
        _scraper_instance = None
