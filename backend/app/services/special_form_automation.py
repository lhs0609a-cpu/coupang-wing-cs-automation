"""
특수 양식 요구 케이스 자동화 서비스
- coupa.ng 링크 클릭
- 특수 양식 입력
- AI 답변 제출
"""
import asyncio
import re
from typing import Dict, List, Optional, AsyncGenerator, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from loguru import logger

from .wing_playwright_client import WingPlaywrightClient
from .ai_response_generator import AIResponseGenerator

# 한국 시간대
KST = timezone(timedelta(hours=9))


@dataclass
class SpecialFormInquiry:
    """특수 양식 문의 데이터"""
    inquiry_id: str
    inquiry_content: str
    customer_name: str
    special_reply_content: str  # 상담사가 보낸 특수 양식 내용
    special_link: Optional[str] = None  # coupa.ng 링크
    product_name: Optional[str] = None


class SpecialFormAutomation:
    """특수 양식 요구 케이스 자동화"""

    # 특수 케이스 키워드
    SPECIAL_KEYWORDS = [
        "링크를 클릭",
        "아래 링크를 클릭",
        "[판매자님 회신필요 사항]",
        "링크를 통해 답변",
        "coupa.ng",
        "응답 제출을 위해"
    ]

    # coupa.ng 링크 패턴
    LINK_PATTERN = r'https?://coupa\.ng/[^\s<>"\']+|coupa\.ng/[^\s<>"\']+'

    def __init__(
        self,
        account_id: int,
        wing_username: str,
        wing_password: str,
        log_callback: Optional[Callable] = None,
        status_callback: Optional[Callable] = None
    ):
        """
        Args:
            account_id: 쿠팡 계정 ID
            wing_username: Wing 아이디
            wing_password: Wing 비밀번호 (복호화된 상태)
            log_callback: 로그 콜백 함수
            status_callback: 상태 콜백 함수
        """
        self.account_id = account_id
        self.wing_username = wing_username
        self.wing_password = wing_password
        self.client: Optional[WingPlaywrightClient] = None
        self.ai_generator = AIResponseGenerator()
        self._log_callback = log_callback
        self._status_callback = status_callback
        self.is_initialized = False

    def log(self, message: str, level: str = 'info'):
        """로그 메시지 출력"""
        if level == 'error':
            logger.error(f"[SpecialForm] {message}")
        elif level == 'warning':
            logger.warning(f"[SpecialForm] {message}")
        elif level == 'success':
            logger.success(f"[SpecialForm] {message}")
        else:
            logger.info(f"[SpecialForm] {message}")

        if self._log_callback:
            try:
                self._log_callback({
                    'time': datetime.now(KST).strftime("%H:%M:%S"),
                    'level': level,
                    'message': message
                })
            except Exception as e:
                logger.error(f"Log callback error: {e}")

    def update_status(self, status: str, current: int = 0, total: int = 0, **kwargs):
        """상태 업데이트"""
        if self._status_callback:
            try:
                self._status_callback({
                    'status': status,
                    'current': current,
                    'total': total,
                    **kwargs
                })
            except Exception as e:
                logger.error(f"Status callback error: {e}")

    @classmethod
    def is_special_case(cls, content: str) -> bool:
        """특수 케이스인지 확인"""
        for keyword in cls.SPECIAL_KEYWORDS:
            if keyword in content:
                return True
        return False

    @classmethod
    def extract_special_link(cls, content: str) -> Optional[str]:
        """coupa.ng 링크 추출"""
        match = re.search(cls.LINK_PATTERN, content)
        if match:
            link = match.group(0)
            # http:// 접두사 없으면 추가
            if not link.startswith('http'):
                link = 'https://' + link
            return link
        return None

    async def initialize(self, headless: bool = True) -> bool:
        """자동화 초기화"""
        try:
            self.log("특수 양식 자동화 초기화 중...")

            self.client = WingPlaywrightClient(
                account_id=self.account_id,
                log_callback=self._log_callback
            )

            if not await self.client.init_browser(headless=headless):
                self.log("브라우저 초기화 실패", 'error')
                return False

            # 로그인
            login_result = await self.client.login(
                username=self.wing_username,
                password=self.wing_password
            )

            if not login_result.get('success'):
                self.log(f"쿠팡 윙 로그인 실패: {login_result.get('message')}", 'error')
                return False

            self.is_initialized = True
            self.log("특수 양식 자동화 초기화 완료!", 'success')
            return True

        except Exception as e:
            self.log(f"초기화 실패: {e}", 'error')
            return False

    async def process_special_inquiry(
        self,
        inquiry: SpecialFormInquiry,
        ai_response: Optional[str] = None
    ) -> Dict:
        """
        특수 양식 문의 처리

        Args:
            inquiry: 특수 양식 문의 데이터
            ai_response: AI 생성 답변 (없으면 자동 생성)

        Returns:
            처리 결과 딕셔너리
        """
        result = {
            "inquiry_id": inquiry.inquiry_id,
            "status": "pending",
            "message": "",
            "steps": []
        }

        try:
            self.log(f"문의 {inquiry.inquiry_id} 처리 시작...")

            # 1. AI 답변 생성 (없으면)
            if not ai_response:
                self.log("AI 답변 생성 중...")
                ai_result = self.ai_generator.generate_response_from_text(
                    inquiry_text=inquiry.inquiry_content,
                    customer_name=inquiry.customer_name
                )
                if ai_result and ai_result.get("response_text"):
                    ai_response = ai_result["response_text"]
                    result["steps"].append({"step": "ai_response", "status": "success"})
                    self.log(f"AI 답변 생성 완료 ({len(ai_response)}자)")
                else:
                    result["status"] = "failed"
                    result["message"] = "AI 답변 생성 실패"
                    result["steps"].append({"step": "ai_response", "status": "failed"})
                    return result
            else:
                result["steps"].append({"step": "ai_response", "status": "provided"})

            # 2. 특수 링크 추출
            special_link = inquiry.special_link or self.extract_special_link(
                inquiry.special_reply_content
            )

            if not special_link:
                result["status"] = "failed"
                result["message"] = "특수 양식 링크를 찾을 수 없습니다"
                result["steps"].append({"step": "link_extract", "status": "failed"})
                self.log("특수 양식 링크를 찾을 수 없습니다", 'error')
                return result

            self.log(f"특수 링크 발견: {special_link}")
            result["steps"].append({
                "step": "link_extract",
                "status": "success",
                "link": special_link
            })

            # 3. 링크 페이지로 이동
            self.log("특수 양식 페이지로 이동 중...")
            if not await self.client.navigate_to_url(special_link):
                result["status"] = "failed"
                result["message"] = "특수 양식 페이지 이동 실패"
                result["steps"].append({"step": "navigate", "status": "failed"})
                return result

            await asyncio.sleep(3)
            result["steps"].append({"step": "navigate", "status": "success"})

            # 4. 양식 분석 및 입력
            form_result = await self._fill_special_form(ai_response)

            if form_result.get("success"):
                result["status"] = "submitted"
                result["message"] = "특수 양식 답변 제출 완료"
                result["ai_response"] = ai_response
                result["steps"].append({"step": "form_submit", "status": "success"})
                self.log(f"문의 {inquiry.inquiry_id} 답변 제출 완료!", 'success')
            else:
                result["status"] = "failed"
                result["message"] = form_result.get("error", "양식 제출 실패")
                result["steps"].append({
                    "step": "form_submit",
                    "status": "failed",
                    "error": form_result.get("error")
                })
                self.log(f"문의 {inquiry.inquiry_id} 양식 제출 실패: {form_result.get('error')}", 'error')

            return result

        except Exception as e:
            self.log(f"특수 양식 처리 오류: {e}", 'error')
            result["status"] = "error"
            result["message"] = str(e)
            return result

    async def _fill_special_form(self, response_text: str) -> Dict:
        """
        특수 양식 입력 및 제출

        다양한 양식 유형 처리:
        - 텍스트 입력 필드
        - 텍스트 영역
        - 라디오 버튼/체크박스
        - 제출 버튼
        """
        try:
            page = self.client.page

            # 페이지 로딩 대기
            await asyncio.sleep(2)

            # 현재 URL 로깅
            current_url = page.url
            self.log(f"양식 페이지 URL: {current_url}")

            # 1. 텍스트 입력 영역 찾기 (다양한 선택자 시도)
            textarea_selectors = [
                'textarea',
                'textarea[name*="content"]',
                'textarea[name*="answer"]',
                'textarea[name*="reply"]',
                'textarea[name*="message"]',
                'textarea[name*="text"]',
                '[contenteditable="true"]',
                'div.editor',
                'div[contenteditable="true"]',
                'input[type="text"][name*="content"]',
                'input[type="text"][name*="answer"]'
            ]

            textarea = None
            for selector in textarea_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        textarea = elem
                        self.log(f"텍스트 입력 영역 발견: {selector}")
                        break
                except:
                    continue

            if textarea:
                # contenteditable인 경우 다른 방식으로 입력
                is_contenteditable = await textarea.get_attribute('contenteditable')
                if is_contenteditable == 'true':
                    await textarea.click()
                    await page.keyboard.type(response_text)
                else:
                    await textarea.fill('')
                    await asyncio.sleep(0.3)
                    await textarea.fill(response_text)

                self.log(f"답변 입력 완료 ({len(response_text)}자)")
            else:
                self.log("텍스트 입력 영역을 찾을 수 없습니다", 'warning')
                await self.client._save_screenshot("special_form_no_textarea")

            await asyncio.sleep(1)

            # 2. 제출 버튼 찾기
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("제출")',
                'button:has-text("저장")',
                'button:has-text("등록")',
                'button:has-text("확인")',
                'button:has-text("전송")',
                'button:has-text("답변")',
                'a:has-text("제출")',
                'a:has-text("저장")',
                'button.submit',
                'button.btn-primary',
                'button.btn-submit',
                '.submit-btn',
                '#submit',
                '#submitBtn'
            ]

            submit_btn = None
            for selector in submit_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        submit_btn = elem
                        try:
                            btn_text = await elem.inner_text()
                            self.log(f"제출 버튼 발견: {selector} - '{btn_text}'")
                        except:
                            self.log(f"제출 버튼 발견: {selector}")
                        break
                except:
                    continue

            if submit_btn:
                # 제출 버튼 클릭
                await submit_btn.click()
                self.log("제출 버튼 클릭 완료")
                await asyncio.sleep(3)

                # 제출 결과 확인
                new_url = page.url
                if new_url != current_url:
                    self.log("양식 제출 성공 (페이지 이동됨)", 'success')
                    return {"success": True}

                # 성공 메시지 확인
                success_indicators = ['완료', '성공', '감사', '접수', '저장되었습니다', 'success', 'complete', 'saved']
                try:
                    page_text = await page.inner_text('body')
                    for indicator in success_indicators:
                        if indicator.lower() in page_text.lower():
                            self.log(f"양식 제출 성공 ('{indicator}' 감지)", 'success')
                            return {"success": True}
                except:
                    pass

                # 에러 메시지 확인
                try:
                    error_elem = await page.query_selector('.error, .alert-danger, .error-message')
                    if error_elem:
                        error_text = await error_elem.inner_text()
                        self.log(f"에러 메시지: {error_text}", 'error')
                        return {"success": False, "error": f"제출 실패: {error_text}"}
                except:
                    pass

                self.log("제출 결과를 확인할 수 없습니다 (성공으로 가정)", 'warning')
                return {"success": True, "warning": "제출 결과 미확인"}
            else:
                self.log("제출 버튼을 찾을 수 없습니다", 'error')
                await self.client._save_screenshot("special_form_no_submit")
                return {"success": False, "error": "제출 버튼을 찾을 수 없음"}

        except Exception as e:
            self.log(f"양식 처리 오류: {e}", 'error')
            await self.client._save_screenshot("special_form_exception")
            return {"success": False, "error": str(e)}

    async def process_batch(
        self,
        inquiries: List[SpecialFormInquiry]
    ) -> AsyncGenerator[Dict, None]:
        """
        다건의 특수 양식 문의 일괄 처리 (스트리밍)

        Args:
            inquiries: 특수 양식 문의 리스트

        Yields:
            각 문의 처리 결과
        """
        total = len(inquiries)
        self.log(f"총 {total}개 특수 양식 문의 처리 시작")

        yield {
            "type": "status",
            "message": f"총 {total}개 특수 양식 문의 처리 시작",
            "total": total
        }

        self.update_status("processing", 0, total)

        success_count = 0
        failed_count = 0

        for idx, inquiry in enumerate(inquiries):
            try:
                self.update_status("processing", idx + 1, total, inquiry_id=inquiry.inquiry_id)

                yield {
                    "type": "progress",
                    "current": idx + 1,
                    "total": total,
                    "inquiry_id": inquiry.inquiry_id
                }

                result = await self.process_special_inquiry(inquiry)

                if result["status"] == "submitted":
                    success_count += 1
                    yield {"type": "success", "data": result}
                else:
                    failed_count += 1
                    yield {"type": "failed", "data": result}

                # 다음 문의 처리 전 대기 (너무 빠른 연속 요청 방지)
                await asyncio.sleep(2)

            except Exception as e:
                failed_count += 1
                self.log(f"문의 {inquiry.inquiry_id} 처리 중 예외: {e}", 'error')
                yield {
                    "type": "error",
                    "inquiry_id": inquiry.inquiry_id,
                    "error": str(e)
                }

        self.update_status("completed", total, total)

        yield {
            "type": "complete",
            "message": f"처리 완료: 성공 {success_count}개, 실패 {failed_count}개",
            "success": success_count,
            "failed": failed_count,
            "total": total
        }

        self.log(f"일괄 처리 완료: 성공 {success_count}개, 실패 {failed_count}개", 'success')

    async def close(self):
        """리소스 정리"""
        if self.client:
            await self.client.close()
        self.is_initialized = False
        self.log("특수 양식 자동화 종료")
