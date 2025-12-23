"""
Auto Mode Service - 실시간 자동모드 통합 서비스
주기적으로 문의를 수집하고 AI 답변을 생성하여 자동 제출합니다.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import threading
import uuid
import time

from .coupang_api_client import CoupangAPIClient
from .ai_response_generator import AIResponseGenerator
from ..models import CoupangAccount


# 전역 세션 관리자
class AutoModeSessionManager:
    """자동모드 세션 관리자 - 싱글톤"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.sessions: Dict[str, Dict] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self._stop_flags: Dict[str, threading.Event] = {}
        logger.info("AutoModeSessionManager 초기화됨")

    def create_session(
        self,
        account_id: int,
        account_name: str,
        vendor_id: str,
        interval_minutes: int,
        inquiry_types: List[str],
        account: CoupangAccount
    ) -> str:
        """새 자동모드 세션 생성"""
        session_id = str(uuid.uuid4())[:8]

        self.sessions[session_id] = {
            "session_id": session_id,
            "account_id": account_id,
            "account_name": account_name,
            "vendor_id": vendor_id,
            "interval_minutes": interval_minutes,
            "inquiry_types": inquiry_types,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "next_run": datetime.now().isoformat(),
            "stats": {
                "total_collected": 0,
                "total_answered": 0,
                "total_submitted": 0,
                "total_confirmed": 0,
                "total_failed": 0,
                "run_count": 0
            },
            "recent_logs": [],
            "account": account  # 계정 정보 저장 (스레드에서 사용)
        }

        # 중지 플래그 생성
        self._stop_flags[session_id] = threading.Event()

        # 백그라운드 스레드 시작
        thread = threading.Thread(
            target=self._run_session_loop,
            args=(session_id,),
            daemon=True
        )
        self.threads[session_id] = thread
        thread.start()

        logger.info(f"자동모드 세션 생성됨: {session_id} (계정: {account_name})")
        return session_id

    def _run_session_loop(self, session_id: str):
        """세션 실행 루프 (백그라운드 스레드)"""
        service = AutoModeService()
        stop_flag = self._stop_flags.get(session_id)

        while not stop_flag.is_set():
            session = self.sessions.get(session_id)
            if not session or session["status"] != "running":
                break

            try:
                account = session["account"]
                inquiry_types = session["inquiry_types"]

                # 실행 로그 추가
                self._add_log(session_id, "자동 수집 시작...", "info")

                # 사이클 실행
                result = service.run_full_cycle(
                    account=account,
                    inquiry_types=inquiry_types,
                    auto_submit=True,
                    wing_id=account.wing_username or account.vendor_id or "auto"
                )

                # 통계 업데이트
                session["stats"]["total_collected"] += result.get("collected", 0)
                session["stats"]["total_answered"] += result.get("answered", 0)
                session["stats"]["total_submitted"] += result.get("submitted", 0)
                session["stats"]["total_confirmed"] += result.get("details", {}).get("callcenter", {}).get("confirmed", 0)
                session["stats"]["total_failed"] += result.get("failed", 0)
                session["stats"]["run_count"] += 1

                # 실행 시간 업데이트
                session["last_run"] = datetime.now().isoformat()
                next_run = datetime.now() + timedelta(minutes=session["interval_minutes"])
                session["next_run"] = next_run.isoformat()

                # 결과 로그
                collected = result.get("collected", 0)
                submitted = result.get("submitted", 0)
                confirmed = result.get("details", {}).get("callcenter", {}).get("confirmed", 0)

                if collected == 0:
                    self._add_log(session_id, "처리할 미답변 문의가 없습니다", "info")
                else:
                    log_msg = f"수집: {collected}, 제출: {submitted}"
                    if confirmed > 0:
                        log_msg += f", 확인완료: {confirmed}"
                    self._add_log(session_id, log_msg, "success")

            except Exception as e:
                logger.error(f"세션 {session_id} 실행 오류: {str(e)}")
                self._add_log(session_id, f"오류: {str(e)}", "error")

            # 다음 실행까지 대기 (1초 단위로 체크하여 빠른 중지 가능)
            interval_seconds = session["interval_minutes"] * 60
            for _ in range(interval_seconds):
                if stop_flag.is_set():
                    break
                time.sleep(1)

        logger.info(f"세션 {session_id} 루프 종료")

    def _add_log(self, session_id: str, message: str, log_type: str = "info"):
        """세션에 로그 추가"""
        session = self.sessions.get(session_id)
        if session:
            log_entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "message": message,
                "type": log_type
            }
            session["recent_logs"].insert(0, log_entry)
            session["recent_logs"] = session["recent_logs"][:20]  # 최근 20개만 유지

    def stop_session(self, session_id: str) -> bool:
        """세션 중지"""
        if session_id not in self.sessions:
            return False

        # 중지 플래그 설정
        if session_id in self._stop_flags:
            self._stop_flags[session_id].set()

        # 상태 업데이트
        self.sessions[session_id]["status"] = "stopped"
        self._add_log(session_id, "자동모드가 중지되었습니다", "info")

        logger.info(f"세션 {session_id} 중지됨")
        return True

    def start_session(self, session_id: str) -> bool:
        """중지된 세션 재시작"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        if session["status"] == "running":
            return True  # 이미 실행 중

        # 새 중지 플래그 생성
        self._stop_flags[session_id] = threading.Event()
        session["status"] = "running"

        # 새 스레드 시작
        thread = threading.Thread(
            target=self._run_session_loop,
            args=(session_id,),
            daemon=True
        )
        self.threads[session_id] = thread
        thread.start()

        self._add_log(session_id, "자동모드가 재시작되었습니다", "success")
        logger.info(f"세션 {session_id} 재시작됨")
        return True

    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        if session_id not in self.sessions:
            return False

        # 먼저 중지
        self.stop_session(session_id)

        # 세션 제거
        del self.sessions[session_id]
        if session_id in self._stop_flags:
            del self._stop_flags[session_id]
        if session_id in self.threads:
            del self.threads[session_id]

        logger.info(f"세션 {session_id} 삭제됨")
        return True

    def get_session(self, session_id: str) -> Optional[Dict]:
        """세션 정보 조회"""
        session = self.sessions.get(session_id)
        if session:
            # account 객체는 직렬화 불가하므로 제외
            return {k: v for k, v in session.items() if k != "account"}
        return None

    def get_all_sessions(self) -> List[Dict]:
        """모든 세션 목록 조회"""
        result = []
        for session_id, session in self.sessions.items():
            # account 객체는 직렬화 불가하므로 제외
            session_data = {k: v for k, v in session.items() if k != "account"}
            result.append(session_data)
        return result

    def get_sessions_by_account(self, account_id: int) -> List[Dict]:
        """특정 계정의 세션 목록 조회"""
        result = []
        for session_id, session in self.sessions.items():
            if session["account_id"] == account_id:
                session_data = {k: v for k, v in session.items() if k != "account"}
                result.append(session_data)
        return result


# 싱글톤 인스턴스 getter
def get_session_manager() -> AutoModeSessionManager:
    return AutoModeSessionManager()


class AutoModeService:
    """
    자동모드 통합 서비스
    문의 수집 -> AI 답변 생성 -> 자동 제출까지 원스톱 처리
    """

    def __init__(self):
        self.ai_generator = AIResponseGenerator()

    def run_full_cycle(
        self,
        account: CoupangAccount,
        inquiry_types: List[str] = ["online", "callcenter"],
        auto_submit: bool = True,
        wing_id: str = "system"
    ) -> Dict:
        """
        자동모드 전체 사이클 실행

        Args:
            account: 쿠팡 계정 정보
            inquiry_types: 수집할 문의 유형 리스트 ["online", "callcenter"]
            auto_submit: 자동 제출 여부
            wing_id: 답변 작성자 Wing ID

        Returns:
            처리 결과 딕셔너리
        """
        results = {
            "collected": 0,
            "answered": 0,
            "submitted": 0,
            "failed": 0,
            "details": {
                "online": {"collected": 0, "answered": 0, "submitted": 0, "failed": 0, "items": []},
                "callcenter": {"collected": 0, "answered": 0, "submitted": 0, "failed": 0, "items": []}
            },
            "errors": []
        }

        try:
            # API 클라이언트 초기화
            api_client = CoupangAPIClient(
                access_key=account.access_key,
                secret_key=account.secret_key,
                vendor_id=account.vendor_id
            )

            # 조회 기간 설정 (쿠팡 API 제한: 최대 7일)
            # 고객센터 API는 최대 7일까지만 조회 가능
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
            logger.info(f"조회 기간: {start_date} ~ {end_date}")

            # Wing ID 설정 (wing_username 사용)
            reply_by = wing_id if wing_id != "system" else (account.wing_username or account.vendor_id or "auto")
            logger.info(f"reply_by 설정: {reply_by} (wing_id={wing_id}, wing_username={account.wing_username})")

            # 각 문의 유형별 처리
            for inquiry_type in inquiry_types:
                try:
                    type_result = self._process_inquiry_type(
                        api_client=api_client,
                        inquiry_type=inquiry_type,
                        start_date=start_date,
                        end_date=end_date,
                        reply_by=reply_by,
                        auto_submit=auto_submit
                    )

                    results["collected"] += type_result["collected"]
                    results["answered"] += type_result["answered"]
                    results["submitted"] += type_result["submitted"]
                    results["failed"] += type_result["failed"]
                    results["details"][inquiry_type] = type_result
                    results["errors"].extend(type_result.get("errors", []))

                except Exception as e:
                    error_msg = f"[{inquiry_type}] 처리 오류: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

        except Exception as e:
            error_msg = f"자동모드 사이클 오류: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

        return results

    def _process_inquiry_type(
        self,
        api_client: CoupangAPIClient,
        inquiry_type: str,
        start_date: str,
        end_date: str,
        reply_by: str,
        auto_submit: bool
    ) -> Dict:
        """
        특정 유형의 문의 처리

        Args:
            api_client: 쿠팡 API 클라이언트
            inquiry_type: 문의 유형 (online/callcenter)
            start_date: 조회 시작일
            end_date: 조회 종료일
            reply_by: 응답자 Wing ID
            auto_submit: 자동 제출 여부

        Returns:
            처리 결과 딕셔너리
        """
        result = {
            "collected": 0,
            "answered": 0,
            "submitted": 0,
            "failed": 0,
            "confirmed": 0,
            "items": [],
            "errors": []
        }

        try:
            if inquiry_type == "online":
                # 온라인 문의 처리
                response = api_client.get_online_inquiries(
                    start_date=start_date,
                    end_date=end_date,
                    answered_type="NOANSWER"
                )

                inquiries = []
                if response.get("code") == 200:
                    inquiries = response.get("data", {}).get("content", [])

                result["collected"] = len(inquiries)
                logger.info(f"[online] {len(inquiries)}개 미답변 문의 수집됨")

                for inquiry in inquiries:
                    item_result = self._process_online_inquiry(
                        api_client=api_client,
                        inquiry=inquiry,
                        reply_by=reply_by,
                        auto_submit=auto_submit
                    )
                    result["items"].append(item_result)

                    if item_result["status"] == "submitted":
                        result["answered"] += 1
                        result["submitted"] += 1
                    elif item_result["status"] == "answered":
                        result["answered"] += 1
                    else:
                        result["failed"] += 1

            else:  # callcenter
                # 고객센터 문의 처리 - NO_ANSWER와 TRANSFER 모두 조회
                logger.info(f"[callcenter] API 조회 시작: {start_date} ~ {end_date}")

                no_answer_response = api_client.get_call_center_inquiries(
                    start_date=start_date,
                    end_date=end_date,
                    status="NO_ANSWER"
                )
                logger.info(f"[callcenter] NO_ANSWER 응답 code: {no_answer_response.get('code')}")

                transfer_response = api_client.get_call_center_inquiries(
                    start_date=start_date,
                    end_date=end_date,
                    status="TRANSFER"
                )
                logger.info(f"[callcenter] TRANSFER 응답 code: {transfer_response.get('code')}")

                no_answer_inquiries = []
                transfer_inquiries = []

                if no_answer_response.get("code") == 200:
                    no_answer_inquiries = no_answer_response.get("data", {}).get("content", [])
                else:
                    logger.warning(f"[callcenter] NO_ANSWER 조회 실패: {no_answer_response}")

                if transfer_response.get("code") == 200:
                    transfer_inquiries = transfer_response.get("data", {}).get("content", [])
                else:
                    logger.warning(f"[callcenter] TRANSFER 조회 실패: {transfer_response}")

                result["collected"] = len(no_answer_inquiries) + len(transfer_inquiries)
                logger.info(f"[callcenter] 답변 필요: {len(no_answer_inquiries)}개, 확인 필요: {len(transfer_inquiries)}개")

                # NO_ANSWER 문의 처리 (답변 작성)
                for inquiry in no_answer_inquiries:
                    item_result = self._process_callcenter_inquiry(
                        api_client=api_client,
                        inquiry=inquiry,
                        reply_by=reply_by,
                        auto_submit=auto_submit
                    )
                    result["items"].append(item_result)

                    if item_result["status"] == "submitted":
                        result["answered"] += 1
                        result["submitted"] += 1
                    elif item_result["status"] == "answered":
                        result["answered"] += 1
                    else:
                        result["failed"] += 1

                # TRANSFER 문의 처리 (확인완료)
                for inquiry in transfer_inquiries:
                    item_result = self._process_transfer_inquiry(
                        api_client=api_client,
                        inquiry=inquiry,
                        reply_by=reply_by
                    )
                    result["items"].append(item_result)

                    if item_result["status"] == "confirmed":
                        result["confirmed"] += 1
                    else:
                        result["failed"] += 1

        except Exception as e:
            error_msg = f"[{inquiry_type}] 수집 오류: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

        return result

    def _process_online_inquiry(
        self,
        api_client: CoupangAPIClient,
        inquiry: Dict,
        reply_by: str,
        auto_submit: bool
    ) -> Dict:
        """
        온라인(상품별) 문의 처리

        Args:
            api_client: 쿠팡 API 클라이언트
            inquiry: 문의 데이터
            reply_by: 응답자 Wing ID
            auto_submit: 자동 제출 여부

        Returns:
            처리 결과
        """
        inquiry_id = inquiry.get("inquiryId")

        try:
            # 이미 답변이 있는지 확인
            if inquiry.get("commentDtoList"):
                logger.info(f"[online] 문의 {inquiry_id}: 이미 답변 있음, 건너뜀")
                return {
                    "inquiry_id": inquiry_id,
                    "status": "skipped",
                    "error": "이미 답변 있음"
                }

            question = inquiry.get("content", "")
            product_name = inquiry.get("productTitle", "")
            customer_name = inquiry.get("customerName", "고객")

            if not question:
                return {
                    "inquiry_id": inquiry_id,
                    "status": "failed",
                    "error": "문의 내용이 비어있습니다"
                }

            # AI 답변 생성
            ai_result = self.ai_generator.generate_response_from_text(
                inquiry_text=question,
                customer_name=customer_name,
                product_name=product_name
            )

            if not ai_result or not ai_result.get("response_text"):
                return {
                    "inquiry_id": inquiry_id,
                    "status": "failed",
                    "error": "AI 답변 생성 실패"
                }

            response_text = ai_result["response_text"]

            if auto_submit:
                submit_result = api_client.reply_to_online_inquiry(
                    inquiry_id=inquiry_id,
                    content=response_text,
                    reply_by=reply_by
                )

                if submit_result.get("code") in [200, "200"]:
                    logger.success(f"[online] 문의 {inquiry_id} 답변 제출 성공")
                    return {
                        "inquiry_id": inquiry_id,
                        "status": "submitted",
                        "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                    }
                else:
                    error_msg = submit_result.get("message", "알 수 없는 오류")
                    logger.error(f"[online] 문의 {inquiry_id} 제출 실패: {error_msg}")
                    return {
                        "inquiry_id": inquiry_id,
                        "status": "failed",
                        "error": f"제출 실패: {error_msg}"
                    }
            else:
                return {
                    "inquiry_id": inquiry_id,
                    "status": "answered",
                    "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                }

        except Exception as e:
            logger.error(f"[online] 문의 {inquiry_id} 처리 오류: {str(e)}")
            return {
                "inquiry_id": inquiry_id,
                "status": "failed",
                "error": str(e)
            }

    def _process_callcenter_inquiry(
        self,
        api_client: CoupangAPIClient,
        inquiry: Dict,
        reply_by: str,
        auto_submit: bool
    ) -> Dict:
        """
        고객센터 문의 처리 (NO_ANSWER 상태)

        Args:
            api_client: 쿠팡 API 클라이언트
            inquiry: 문의 데이터
            reply_by: 응답자 Wing ID
            auto_submit: 자동 제출 여부

        Returns:
            처리 결과
        """
        inquiry_id = inquiry.get("inquiryId")

        try:
            # 이미 답변 완료된 문의인지 확인
            cs_status = inquiry.get("csPartnerCounselingStatus", "")
            if cs_status == "answered":
                logger.info(f"[callcenter] 문의 {inquiry_id}: 이미 답변 완료, 건너뜀")
                return {
                    "inquiry_id": inquiry_id,
                    "status": "skipped",
                    "error": "이미 답변 완료"
                }

            # replies 배열에서 parentAnswerId 추출
            # partnerTransferStatus가 "requestAnswer"이고 needAnswer가 true인 reply의 answerId를 찾음
            replies = inquiry.get("replies", [])
            parent_answer_id = 0
            is_special_case = False

            for reply in replies:
                if reply.get("partnerTransferStatus") == "requestAnswer" and reply.get("needAnswer") == True:
                    parent_answer_id = reply.get("answerId", 0)

                    # 특수 케이스 체크: 링크를 통한 답변 요구 케이스
                    reply_content = reply.get("content", "")
                    special_keywords = [
                        "링크를 클릭",
                        "아래 링크를 클릭",
                        "[판매자님 회신필요 사항]",
                        "링크를 통해 답변",
                        "coupa.ng",
                        "응답 제출을 위해"
                    ]

                    for keyword in special_keywords:
                        if keyword in reply_content:
                            is_special_case = True
                            logger.info(f"[callcenter] 문의 {inquiry_id}: 특수 양식 요구 케이스, 건너뜀")
                            break

                    break

            if parent_answer_id == 0:
                logger.warning(f"[callcenter] 문의 {inquiry_id}: parentAnswerId를 찾을 수 없음, 건너뜀")
                return {
                    "inquiry_id": inquiry_id,
                    "status": "skipped",
                    "error": "parentAnswerId를 찾을 수 없음"
                }

            if is_special_case:
                return {
                    "inquiry_id": inquiry_id,
                    "status": "skipped",
                    "error": "특수 양식 요구 케이스"
                }

            # 문의 내용 추출
            inquiry_content = inquiry.get("content", "")
            customer_name = inquiry.get("buyerName", "고객")

            if not inquiry_content:
                return {
                    "inquiry_id": inquiry_id,
                    "status": "failed",
                    "error": "문의 내용이 비어있습니다"
                }

            # AI 답변 생성
            ai_result = self.ai_generator.generate_response_from_text(
                inquiry_text=inquiry_content,
                customer_name=customer_name
            )

            if not ai_result or not ai_result.get("response_text"):
                return {
                    "inquiry_id": inquiry_id,
                    "status": "failed",
                    "error": "AI 답변 생성 실패"
                }

            response_text = ai_result["response_text"]

            if auto_submit:
                submit_result = api_client.reply_to_call_center_inquiry(
                    inquiry_id=str(inquiry_id),
                    content=response_text,
                    reply_by=reply_by,
                    parent_answer_id=parent_answer_id
                )

                if submit_result.get("code") in [200, "200"]:
                    logger.success(f"[callcenter] 문의 {inquiry_id} 답변 제출 성공")
                    return {
                        "inquiry_id": inquiry_id,
                        "status": "submitted",
                        "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                    }
                else:
                    error_msg = submit_result.get("message", "알 수 없는 오류")
                    logger.error(f"[callcenter] 문의 {inquiry_id} 제출 실패: {error_msg}")
                    return {
                        "inquiry_id": inquiry_id,
                        "status": "failed",
                        "error": f"제출 실패: {error_msg}"
                    }
            else:
                return {
                    "inquiry_id": inquiry_id,
                    "status": "answered",
                    "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                }

        except Exception as e:
            logger.error(f"[callcenter] 문의 {inquiry_id} 처리 오류: {str(e)}")
            return {
                "inquiry_id": inquiry_id,
                "status": "failed",
                "error": str(e)
            }

    def _process_transfer_inquiry(
        self,
        api_client: CoupangAPIClient,
        inquiry: Dict,
        reply_by: str
    ) -> Dict:
        """
        고객센터 TRANSFER 문의 처리 (확인완료)

        Args:
            api_client: 쿠팡 API 클라이언트
            inquiry: 문의 데이터
            reply_by: 응답자 Wing ID

        Returns:
            처리 결과
        """
        inquiry_id = inquiry.get("inquiryId")

        try:
            logger.info(f"[callcenter] TRANSFER 문의 {inquiry_id} 확인완료 시도, confirm_by={reply_by}")
            logger.debug(f"[callcenter] 문의 데이터: {inquiry}")

            # 확인완료 (confirm) 수행
            confirm_result = api_client.confirm_call_center_inquiry(
                inquiry_id=str(inquiry_id),
                confirm_by=reply_by
            )

            logger.info(f"[callcenter] 문의 {inquiry_id} confirm 응답: {confirm_result}")

            if confirm_result.get("code") in [200, "200"]:
                logger.success(f"[callcenter] 문의 {inquiry_id} 확인완료 처리 성공")
                return {
                    "inquiry_id": inquiry_id,
                    "status": "confirmed"
                }
            else:
                error_msg = confirm_result.get("message", "알 수 없는 오류")
                error_code = confirm_result.get("code", "unknown")
                logger.error(f"[callcenter] 문의 {inquiry_id} 확인완료 실패: code={error_code}, msg={error_msg}")
                return {
                    "inquiry_id": inquiry_id,
                    "status": "failed",
                    "error": f"확인완료 실패 (code={error_code}): {error_msg}"
                }

        except Exception as e:
            logger.error(f"[callcenter] 문의 {inquiry_id} 확인완료 처리 오류: {str(e)}")
            import traceback
            logger.error(f"[callcenter] 스택 트레이스: {traceback.format_exc()}")
            return {
                "inquiry_id": inquiry_id,
                "status": "failed",
                "error": str(e)
            }
