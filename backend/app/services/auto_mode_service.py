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
from ..models import CoupangAccount, AutoModeSession, Inquiry, Response
from ..database import SessionLocal


# 전역 세션 관리자
class AutoModeSessionManager:
    """자동모드 세션 관리자 - 싱글톤 (DB 영구 저장 지원)"""
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
        self._db_loaded = False
        logger.info("AutoModeSessionManager 초기화됨")

    def load_sessions_from_db(self, auto_restart: bool = False):
        """DB에서 저장된 세션 로드 및 복원

        Args:
            auto_restart: True이면 running 상태였던 세션을 자동 재시작
        """
        if self._db_loaded:
            return

        sessions_to_restart = []

        try:
            db = SessionLocal()
            try:
                # 활성화된 세션만 로드
                db_sessions = db.query(AutoModeSession).filter(
                    AutoModeSession.is_active == True
                ).all()

                for db_session in db_sessions:
                    # 계정 정보 로드
                    account = db.query(CoupangAccount).filter(
                        CoupangAccount.id == db_session.account_id
                    ).first()

                    if not account:
                        logger.warning(f"세션 {db_session.session_id}: 계정을 찾을 수 없음, 건너뜀")
                        continue

                    # 서버 재시작 전 running 상태였는지 확인
                    was_running = db_session.status == "running"

                    # 메모리에 세션 복원
                    self.sessions[db_session.session_id] = {
                        "session_id": db_session.session_id,
                        "account_id": db_session.account_id,
                        "account_name": db_session.account_name,
                        "vendor_id": db_session.vendor_id,
                        "interval_minutes": db_session.interval_minutes,
                        "inquiry_types": db_session.inquiry_types or ["online", "callcenter"],
                        "status": "stopped",  # 초기 상태는 중지
                        "created_at": db_session.created_at.isoformat() if db_session.created_at else datetime.now().isoformat(),
                        "last_run": db_session.last_run.isoformat() if db_session.last_run else None,
                        "next_run": None,
                        "stats": {
                            "total_collected": db_session.total_collected or 0,
                            "total_answered": db_session.total_answered or 0,
                            "total_submitted": db_session.total_submitted or 0,
                            "total_confirmed": db_session.total_confirmed or 0,
                            "total_failed": db_session.total_failed or 0,
                            "run_count": db_session.run_count or 0
                        },
                        "recent_logs": [],
                        "account": account,
                        "db_id": db_session.id
                    }

                    logger.info(f"DB에서 세션 복원: {db_session.session_id} (계정: {db_session.account_name})")

                    # 자동 재시작 대상 기록
                    if auto_restart and was_running:
                        sessions_to_restart.append(db_session.session_id)

                self._db_loaded = True
                logger.info(f"DB에서 {len(db_sessions)}개 세션 로드 완료")

                # 자동 재시작 처리
                if sessions_to_restart:
                    logger.info(f"{len(sessions_to_restart)}개 세션 자동 재시작 시작...")
                    for session_id in sessions_to_restart:
                        self.start_session(session_id)
                        self._add_log(session_id, "서버 재시작으로 자동 복원됨", "info")
                    logger.info(f"{len(sessions_to_restart)}개 세션 자동 재시작 완료")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"DB에서 세션 로드 실패: {str(e)}")

    def _save_session_to_db(self, session_id: str):
        """세션을 DB에 저장"""
        session = self.sessions.get(session_id)
        if not session:
            return

        try:
            db = SessionLocal()
            try:
                # 기존 세션 찾기
                db_session = db.query(AutoModeSession).filter(
                    AutoModeSession.session_id == session_id
                ).first()

                if db_session:
                    # 업데이트
                    db_session.status = session["status"]
                    db_session.total_collected = session["stats"]["total_collected"]
                    db_session.total_answered = session["stats"]["total_answered"]
                    db_session.total_submitted = session["stats"]["total_submitted"]
                    db_session.total_confirmed = session["stats"]["total_confirmed"]
                    db_session.total_failed = session["stats"]["total_failed"]
                    db_session.run_count = session["stats"]["run_count"]
                    if session.get("last_run"):
                        db_session.last_run = datetime.fromisoformat(session["last_run"])
                    db_session.updated_at = datetime.utcnow()
                else:
                    # 새로 생성
                    db_session = AutoModeSession(
                        session_id=session_id,
                        account_id=session["account_id"],
                        account_name=session["account_name"],
                        vendor_id=session["vendor_id"],
                        interval_minutes=session["interval_minutes"],
                        inquiry_types=session["inquiry_types"],
                        status=session["status"],
                        is_active=True,
                        total_collected=session["stats"]["total_collected"],
                        total_answered=session["stats"]["total_answered"],
                        total_submitted=session["stats"]["total_submitted"],
                        total_confirmed=session["stats"]["total_confirmed"],
                        total_failed=session["stats"]["total_failed"],
                        run_count=session["stats"]["run_count"]
                    )
                    db.add(db_session)

                db.commit()
                logger.debug(f"세션 {session_id} DB 저장 완료")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"세션 {session_id} DB 저장 실패: {str(e)}")

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
        # DB에서 세션 로드 (아직 안했다면)
        self.load_sessions_from_db()

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
            "inquiry_history": [],  # 상세 문의 처리 히스토리
            "account": account  # 계정 정보 저장 (스레드에서 사용)
        }

        # DB에 저장
        self._save_session_to_db(session_id)

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

                # DB에 통계 저장
                self._save_session_to_db(session_id)

                # 결과 로그
                collected = result.get("collected", 0)
                submitted = result.get("submitted", 0)
                confirmed = result.get("details", {}).get("callcenter", {}).get("confirmed", 0)

                # 상세 문의 히스토리 저장
                for inquiry_type, type_details in result.get("details", {}).items():
                    for item in type_details.get("items", []):
                        self._add_inquiry_history(session_id, item)

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

    def _add_inquiry_history(self, session_id: str, history_entry: dict):
        """세션에 문의 처리 히스토리 추가"""
        session = self.sessions.get(session_id)
        if session:
            if "inquiry_history" not in session:
                session["inquiry_history"] = []

            # 타임스탬프 추가
            history_entry["timestamp"] = datetime.now().isoformat()
            history_entry["time"] = datetime.now().strftime("%H:%M:%S")

            session["inquiry_history"].insert(0, history_entry)
            session["inquiry_history"] = session["inquiry_history"][:50]  # 최근 50개만 유지

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

        # DB 상태 업데이트
        self._save_session_to_db(session_id)

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
        session["next_run"] = datetime.now().isoformat()

        # DB 상태 업데이트
        self._save_session_to_db(session_id)

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

        # DB에서 비활성화 처리
        self._deactivate_session_in_db(session_id)

        # 세션 제거
        del self.sessions[session_id]
        if session_id in self._stop_flags:
            del self._stop_flags[session_id]
        if session_id in self.threads:
            del self.threads[session_id]

        logger.info(f"세션 {session_id} 삭제됨")
        return True

    def _deactivate_session_in_db(self, session_id: str):
        """DB에서 세션 비활성화"""
        try:
            db = SessionLocal()
            try:
                db_session = db.query(AutoModeSession).filter(
                    AutoModeSession.session_id == session_id
                ).first()

                if db_session:
                    db_session.is_active = False
                    db_session.status = "deleted"
                    db_session.updated_at = datetime.utcnow()
                    db.commit()
                    logger.debug(f"세션 {session_id} DB 비활성화 완료")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"세션 {session_id} DB 비활성화 실패: {str(e)}")

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

    def _save_inquiry_and_response(
        self,
        inquiry_id: str,
        vendor_id: str,
        inquiry_type: str,
        inquiry_content: str,
        customer_name: str,
        product_name: str,
        response_text: str,
        status: str,
        submitted_by: str
    ):
        """문의와 답변을 DB에 저장"""
        try:
            db = SessionLocal()
            try:
                # 기존 문의 확인 또는 새로 생성
                existing_inquiry = db.query(Inquiry).filter(
                    Inquiry.coupang_inquiry_id == str(inquiry_id)
                ).first()

                if not existing_inquiry:
                    # 새 문의 생성
                    new_inquiry = Inquiry(
                        coupang_inquiry_id=str(inquiry_id),
                        vendor_id=vendor_id,
                        customer_name=customer_name,
                        product_name=product_name,
                        inquiry_text=inquiry_content,
                        inquiry_category=inquiry_type,
                        inquiry_date=datetime.utcnow(),
                        status="processed" if status == "submitted" else "pending"
                    )
                    db.add(new_inquiry)
                    db.flush()
                    local_inquiry_id = new_inquiry.id
                else:
                    local_inquiry_id = existing_inquiry.id
                    existing_inquiry.status = "processed" if status == "submitted" else "pending"

                # 응답 저장
                new_response = Response(
                    inquiry_id=local_inquiry_id,
                    response_text=response_text,
                    original_response=response_text,
                    confidence_score=85.0,
                    risk_level="low",
                    generation_method="ai",
                    validation_passed=True,
                    status="submitted" if status == "submitted" else "draft",
                    submitted_at=datetime.utcnow() if status == "submitted" else None,
                    submitted_by=submitted_by,
                    submission_status="success" if status == "submitted" else None,
                    auto_approved=True
                )
                db.add(new_response)
                db.commit()

                logger.debug(f"문의 {inquiry_id} 및 답변 DB 저장 완료")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"문의/답변 DB 저장 실패: {str(e)}")

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
                    # DB에 문의와 답변 저장
                    self._save_inquiry_and_response(
                        inquiry_id=str(inquiry_id),
                        vendor_id=api_client.vendor_id,
                        inquiry_type="online",
                        inquiry_content=question,
                        customer_name=customer_name,
                        product_name=product_name,
                        response_text=response_text,
                        status="submitted",
                        submitted_by=reply_by
                    )
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
                            special_keyword_found = keyword
                            logger.info(f"[callcenter] 문의 {inquiry_id}: 특수 양식 요구 케이스 (키워드: {keyword}), 건너뜀")
                            break

                    break

            # 문의 내용 추출 (히스토리용)
            inquiry_content_for_history = inquiry.get("content", "")
            customer_name_for_history = inquiry.get("buyerName", "고객")

            if parent_answer_id == 0:
                logger.warning(f"[callcenter] 문의 {inquiry_id}: parentAnswerId를 찾을 수 없음, 건너뜀")
                return {
                    "inquiry_id": inquiry_id,
                    "status": "skipped",
                    "error": "parentAnswerId를 찾을 수 없음",
                    "inquiry_type": "callcenter",
                    "inquiry_content": inquiry_content_for_history[:200] if inquiry_content_for_history else "",
                    "customer_name": customer_name_for_history
                }

            if is_special_case:
                return {
                    "inquiry_id": inquiry_id,
                    "status": "skipped",
                    "error": f"특수 양식 요구 케이스 (링크 클릭 필요)",
                    "inquiry_type": "callcenter",
                    "inquiry_content": inquiry_content_for_history[:200] if inquiry_content_for_history else "",
                    "customer_name": customer_name_for_history,
                    "special_reply_content": reply_content[:300] if reply_content else "",
                    "skip_reason": f"자동 처리 불가 - 특수 양식 필요 (키워드: {special_keyword_found})"
                }

            # 문의 내용 추출
            inquiry_content = inquiry.get("content", "")
            customer_name = inquiry.get("buyerName", "고객")

            if not inquiry_content:
                return {
                    "inquiry_id": inquiry_id,
                    "status": "failed",
                    "error": "문의 내용이 비어있습니다",
                    "inquiry_type": "callcenter",
                    "customer_name": customer_name
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
                    "error": "AI 답변 생성 실패",
                    "inquiry_type": "callcenter",
                    "inquiry_content": inquiry_content[:300] if inquiry_content else "",
                    "customer_name": customer_name
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
                    # DB에 문의와 답변 저장
                    self._save_inquiry_and_response(
                        inquiry_id=str(inquiry_id),
                        vendor_id=api_client.vendor_id,
                        inquiry_type="callcenter",
                        inquiry_content=inquiry_content,
                        customer_name=customer_name,
                        product_name="",
                        response_text=response_text,
                        status="submitted",
                        submitted_by=reply_by
                    )
                    return {
                        "inquiry_id": inquiry_id,
                        "status": "submitted",
                        "inquiry_type": "callcenter",
                        "inquiry_content": inquiry_content[:300] if inquiry_content else "",
                        "customer_name": customer_name,
                        "response_text": response_text,
                        "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                    }
                else:
                    error_msg = submit_result.get("message", "알 수 없는 오류")
                    logger.error(f"[callcenter] 문의 {inquiry_id} 제출 실패: {error_msg}")
                    return {
                        "inquiry_id": inquiry_id,
                        "status": "failed",
                        "error": f"제출 실패: {error_msg}",
                        "inquiry_type": "callcenter",
                        "inquiry_content": inquiry_content[:300] if inquiry_content else "",
                        "customer_name": customer_name,
                        "response_text": response_text
                    }
            else:
                return {
                    "inquiry_id": inquiry_id,
                    "status": "answered",
                    "inquiry_type": "callcenter",
                    "inquiry_content": inquiry_content[:300] if inquiry_content else "",
                    "customer_name": customer_name,
                    "response_text": response_text,
                    "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                }

        except Exception as e:
            logger.error(f"[callcenter] 문의 {inquiry_id} 처리 오류: {str(e)}")
            return {
                "inquiry_id": inquiry_id,
                "status": "failed",
                "error": str(e),
                "inquiry_type": "callcenter"
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
        inquiry_content = inquiry.get("content", "")
        customer_name = inquiry.get("buyerName", "고객")

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
                    "status": "confirmed",
                    "inquiry_type": "callcenter_transfer",
                    "inquiry_content": inquiry_content[:300] if inquiry_content else "",
                    "customer_name": customer_name,
                    "action": "확인완료 처리"
                }
            else:
                error_msg = confirm_result.get("message", "알 수 없는 오류")
                error_code = confirm_result.get("code", "unknown")
                logger.error(f"[callcenter] 문의 {inquiry_id} 확인완료 실패: code={error_code}, msg={error_msg}")
                return {
                    "inquiry_id": inquiry_id,
                    "status": "failed",
                    "error": f"확인완료 실패 (code={error_code}): {error_msg}",
                    "inquiry_type": "callcenter_transfer",
                    "inquiry_content": inquiry_content[:300] if inquiry_content else "",
                    "customer_name": customer_name
                }

        except Exception as e:
            logger.error(f"[callcenter] 문의 {inquiry_id} 확인완료 처리 오류: {str(e)}")
            import traceback
            logger.error(f"[callcenter] 스택 트레이스: {traceback.format_exc()}")
            return {
                "inquiry_id": inquiry_id,
                "status": "failed",
                "error": str(e),
                "inquiry_type": "callcenter_transfer",
                "inquiry_content": inquiry_content[:300] if inquiry_content else "",
                "customer_name": customer_name
            }
