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
        """실제 로그인 상태 확인 (네이버페이 페이지 접근)"""
        try:
            if not self.page:
                return False

            # 네이버페이 페이지로 이동하여 로그인 상태 확인
            await self.page.goto('https://pay.naver.com/pc/history', wait_until='domcontentloaded')
            await asyncio.sleep(2)

            current_url = self.page.url
            logger.info(f"로그인 상태 확인 - 현재 URL: {current_url}")

            # 로그인 페이지로 리다이렉트되면 로그아웃 상태
            if 'nidlogin.login' in current_url or 'nid.naver.com' in current_url:
                logger.info("로그인 필요: 로그인 페이지로 리다이렉트됨")
                self.is_logged_in = False
                return False

            # pay.naver.com에 머물러 있으면 로그인 상태
            if 'pay.naver.com' in current_url:
                self.is_logged_in = True
                self.last_login_check = datetime.now(KST)
                logger.info("로그인 상태 확인 완료")
                return True

            # 기타 URL인 경우
            self.is_logged_in = False
            return False

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
        - 배송중 페이지로 이동
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
            # 배송중 페이지로 이동 (정확한 URL)
            delivery_url = 'https://pay.naver.com/pc/history?subFilter=deliveringFilter&page=1'
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

            # 로그인 페이지로 리다이렉트 됐는지 확인
            if 'nidlogin.login' in current_url or 'nid.naver.com' in current_url:
                scrape_logger.error("세션 만료: 로그인 페이지로 리다이렉트됨")
                self.is_logged_in = False
                yield {"type": "error", "message": "네이버 로그인 세션이 만료되었습니다. 다시 로그인해주세요."}
                return

            yield {"type": "status", "message": "모든 상품 로드 중..."}

            # 스크롤 + "이전내역 더보기" 클릭으로 모든 상품 로드
            scrape_logger.info("페이지 스크롤 및 이전내역 더보기 클릭 시작")
            load_more_count = 0
            max_load_more = 50  # 최대 50회

            while load_more_count < max_load_more:
                # 스크롤
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(1)

                # "이전내역 더보기" 버튼 찾기
                load_more_btn = await self.page.query_selector('button[class*="LoadMoreHistoryButton_button-more"]')
                if load_more_btn:
                    try:
                        scrape_logger.info(f"이전내역 더보기 클릭 ({load_more_count + 1}회)")
                        await load_more_btn.click(force=True, timeout=5000)
                        await asyncio.sleep(2)
                        load_more_count += 1
                    except Exception as e:
                        scrape_logger.info(f"이전내역 더보기 클릭 종료: {e}")
                        break
                else:
                    # 버튼이 없으면 종료
                    scrape_logger.info("이전내역 더보기 버튼 없음, 로드 완료")
                    break

            scrape_logger.info(f"총 {load_more_count}회 이전내역 더보기 클릭 완료")

            yield {"type": "status", "message": "상품 정보 수집 중..."}

            # JavaScript로 모든 상품 정보를 한번에 수집 (상품명 + 상세페이지 URL)
            product_data = await self.page.evaluate('''() => {
                const results = [];
                // 각 주문 항목 찾기
                const orderItems = document.querySelectorAll('li[class*="PaymentItem_item"]');
                orderItems.forEach(item => {
                    // 상품명 추출
                    const nameEl = item.querySelector('span[class*="ProductNameHighlightByKeyword_article"]') ||
                                   item.querySelector('[class*="ProductName_name"]');
                    const productName = nameEl ? nameEl.innerText.trim() : '';

                    // 상세 페이지 링크 추출
                    const linkEl = item.querySelector('a[href*="/order/status/"]');
                    const detailUrl = linkEl ? linkEl.href : '';

                    if (productName && detailUrl) {
                        results.push({ productName, detailUrl });
                    }
                });
                return results;
            }''')
            scrape_logger.info(f"상품 정보 {len(product_data)}개 수집됨")

            if not product_data:
                # 대체 방법: 상세 링크만 수집
                product_data = await self.page.evaluate('''() => {
                    const links = document.querySelectorAll('a[href*="/order/status/"]');
                    return Array.from(links).map(a => ({
                        productName: '',
                        detailUrl: a.href
                    }));
                }''')
                scrape_logger.info(f"대체 방법으로 {len(product_data)}개 링크 수집")

            total_products = len(product_data)

            if total_products == 0:
                scrape_logger.warning("상품을 찾지 못함")
                empty_msg = await self.page.query_selector('[class*="Empty"], [class*="empty"]')
                if empty_msg:
                    empty_text = await empty_msg.inner_text()
                    yield {"type": "status", "message": f"배송중인 상품이 없습니다: {empty_text}"}
                else:
                    yield {"type": "status", "message": "배송중인 상품을 찾을 수 없습니다."}

            yield {"type": "status", "message": f"{total_products}개 상품 발견, 상세 정보 수집 중..."}

            # 중복 방지
            processed_tracking_numbers = set()
            processed_urls = set()

            for idx, item in enumerate(product_data):
                try:
                    product_name = item.get('productName', '')
                    detail_url = item.get('detailUrl', '')

                    # URL 중복 체크
                    if detail_url in processed_urls:
                        scrape_logger.info(f"중복 URL, 건너뜀: {detail_url[:50]}...")
                        continue
                    processed_urls.add(detail_url)

                    scrape_logger.info(f"상품 {idx + 1}/{total_products} 처리 중...")
                    yield {"type": "status", "message": f"상품 {idx + 1}/{total_products} 처리 중..."}
                    scrape_logger.info(f"상품명: {product_name[:50] if product_name else '(알수없음)'}...")

                    # 상세 페이지로 직접 이동 (클릭 대신 URL 사용)
                    if not detail_url:
                        scrape_logger.warning("상세 URL 없음, 건너뜀")
                        continue

                    scrape_logger.info(f"상세 페이지로 이동: {detail_url[:60]}...")
                    await self.page.goto(detail_url, wait_until='domcontentloaded', timeout=15000)
                    await asyncio.sleep(2)

                    # 수령인 추출 (DeliveryContent_name 클래스)
                    recipient = ""
                    recipient_elem = await self.page.query_selector('strong[class*="DeliveryContent_name"]')
                    if recipient_elem:
                        recipient_text = await recipient_elem.inner_text()
                        # "배송지명" 텍스트 제거
                        recipient = recipient_text.replace("배송지명", "").strip()
                        # 괄호와 그 내용 제거 (예: "뭉티기짜글이(뭉티기짜글이)" -> "뭉티기짜글이")
                        recipient = re.sub(r'\([^)]*\)', '', recipient).strip()
                    scrape_logger.info(f"수령인: {recipient}")

                    # 배송조회 버튼 클릭 (AssignmentButtonGroup_text 클래스)
                    courier = ""
                    tracking_number = ""

                    delivery_btn = await self.page.query_selector('span[class*="AssignmentButtonGroup_text"]')
                    if delivery_btn:
                        btn_text = await delivery_btn.inner_text()
                        if "배송조회" in btn_text:
                            scrape_logger.info("배송조회 버튼 발견, 클릭 중...")
                            try:
                                # 부모 button 찾아서 클릭
                                parent_btn = await delivery_btn.evaluate_handle('el => el.closest("button")')
                                if parent_btn:
                                    await parent_btn.click(force=True, timeout=10000)
                                else:
                                    await delivery_btn.click(force=True, timeout=10000)
                                await asyncio.sleep(3)
                                scrape_logger.info(f"배송조회 페이지 이동: {self.page.url[:60]}...")

                                # 택배사 추출 (Courier_company 클래스)
                                courier_elem = await self.page.query_selector('span[class*="Courier_company"]')
                                if courier_elem:
                                    courier = await courier_elem.inner_text()
                                    courier = courier.strip()
                                scrape_logger.info(f"택배사: {courier}")

                                # 송장번호 추출 (Courier_number 클래스)
                                tracking_elem = await self.page.query_selector('span[class*="Courier_number"]')
                                if tracking_elem:
                                    tracking_number = await tracking_elem.inner_text()
                                    tracking_number = tracking_number.strip()
                                scrape_logger.info(f"송장번호: {tracking_number}")

                            except Exception as btn_err:
                                scrape_logger.warning(f"배송조회 버튼 클릭 실패: {btn_err}")
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

                    # URL 기반 순회이므로 목록 페이지로 돌아갈 필요 없음

                except Exception as e:
                    scrape_logger.warning(f"상품 {idx + 1} 처리 오류: {e}")
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
