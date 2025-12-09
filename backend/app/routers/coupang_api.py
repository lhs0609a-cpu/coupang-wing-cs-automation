"""
Coupang Open API Router
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from loguru import logger
from typing import Optional, List
from datetime import datetime, timedelta
import requests
from ..services.coupang_api_client import CoupangAPIClient
from ..services.ai_response_generator import AIResponseGenerator
from ..config import settings
from ..database import SessionLocal
from ..models.automation_log import AutomationExecutionLog


router = APIRouter(prefix="/coupang-api", tags=["Coupang Open API"])


class CoupangAPICredentials(BaseModel):
    """쿠팡 API 인증 정보"""
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    vendor_id: Optional[str] = None
    wing_username: Optional[str] = None


def _create_client(credentials: Optional[CoupangAPICredentials] = None) -> CoupangAPIClient:
    """
    Coupang API 클라이언트 생성 헬퍼 함수

    Args:
        credentials: API 인증 정보 (없으면 환경 변수 사용)

    Returns:
        CoupangAPIClient 인스턴스
    """
    if credentials and credentials.access_key and credentials.secret_key and credentials.vendor_id:
        return CoupangAPIClient(
            access_key=credentials.access_key,
            secret_key=credentials.secret_key,
            vendor_id=credentials.vendor_id
        )
    return CoupangAPIClient()


class InquiryReplyRequest(BaseModel):
    """문의 답변 요청"""
    inquiry_id: int
    content: Optional[str] = None  # None이면 ChatGPT가 자동 생성
    reply_by: Optional[str] = None  # None이면 설정값 사용
    credentials: Optional[CoupangAPICredentials] = None  # API 인증 정보


class AutoAnswerRequest(BaseModel):
    """자동 답변 요청"""
    start_date: Optional[str] = None  # None이면 오늘-7일
    end_date: Optional[str] = None  # None이면 오늘
    answered_type: str = "NOANSWER"  # NOANSWER, ALL, ANSWERED
    reply_by: Optional[str] = None  # None이면 설정값 사용
    auto_generate: bool = True  # ChatGPT로 자동 생성 여부
    credentials: Optional[CoupangAPICredentials] = None  # API 인증 정보
    account_id: Optional[int] = None  # Coupang 계정 ID (DB에서 조회)


@router.post("/test-connection")
async def test_connection(credentials: Optional[CoupangAPICredentials] = None):
    """
    Coupang API 연결 테스트

    Args:
        credentials: 쿠팡 API 인증 정보 (없으면 환경 변수 사용)

    Returns:
        연결 상태
    """
    try:
        # API 클라이언트 생성
        client = _create_client(credentials)

        # 오늘 날짜로 테스트 조회
        today = datetime.now().strftime("%Y-%m-%d")

        result = client.get_online_inquiries(
            start_date=today,
            end_date=today,
            answered_type="ALL",
            page_size=1
        )

        if result.get("code") == 200:
            return {
                "success": True,
                "message": "Coupang API 연결 성공",
                "data": {
                    "vendor_id": client.vendor_id,
                    "api_working": True
                }
            }
        else:
            # API 호출은 성공했지만 에러 응답을 받은 경우
            return {
                "success": False,
                "message": f"Coupang API 오류: {result.get('message', 'Unknown error')}",
                "data": {
                    "vendor_id": client.vendor_id,
                    "api_working": False,
                    "error_code": result.get("code")
                }
            }
    except Exception as e:
        error_msg = str(e)

        # HTTP 에러인 경우 상태 코드 확인
        if isinstance(e, requests.exceptions.HTTPError):
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else 500

            if status_code == 403:
                logger.warning(f"Coupang API 권한 부족: {error_msg}")
                return {
                    "success": False,
                    "message": "Coupang API 권한이 활성화되지 않았습니다. Wing 관리자 페이지에서 'Open API > 상품별 고객문의 조회' 권한을 활성화해주세요.",
                    "data": {
                        "vendor_id": client.vendor_id if 'client' in locals() else None,
                        "api_working": False,
                        "error_code": 403,
                        "error_type": "권한 부족"
                    }
                }
            elif status_code == 401:
                logger.error(f"Coupang API 인증 실패: {error_msg}")
                return {
                    "success": False,
                    "message": "Coupang API 인증 실패. Access Key 또는 Secret Key가 올바르지 않습니다.",
                    "data": {
                        "vendor_id": client.vendor_id if 'client' in locals() else None,
                        "api_working": False,
                        "error_code": 401,
                        "error_type": "인증 실패"
                    }
                }

        # 기타 에러
        logger.error(f"Coupang API 연결 실패: {error_msg}")
        return {
            "success": False,
            "message": f"API 연결 실패: {error_msg}",
            "data": {
                "vendor_id": client.vendor_id if 'client' in locals() else None,
                "api_working": False,
                "error_type": "연결 오류"
            }
        }


@router.get("/inquiries/online")
async def get_online_inquiries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    answered_type: str = "NOANSWER",
    page_num: int = 1,
    page_size: int = 50
):
    """
    상품별 고객문의 조회

    Args:
        start_date: 조회시작일 (yyyy-MM-dd), None이면 오늘-7일
        end_date: 조회종료일 (yyyy-MM-dd), None이면 오늘
        answered_type: 답변상태 (ALL, ANSWERED, NOANSWER)
        page_num: 페이지 번호
        page_size: 페이지 크기 (최대 50)

    Returns:
        고객문의 목록
    """
    try:
        # 기본 날짜 설정
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

        client = CoupangAPIClient()
        result = client.get_online_inquiries(
            start_date=start_date,
            end_date=end_date,
            answered_type=answered_type,
            page_num=page_num,
            page_size=page_size
        )

        if result.get("code") != 200:
            raise HTTPException(
                status_code=result.get("code", 500),
                detail=result.get("message", "Unknown error")
            )

        return {
            "success": True,
            "data": result.get("data", {}),
            "message": f"{start_date} ~ {end_date} 기간 문의 조회 완료"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"상품별 고객문의 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inquiries/online/{inquiry_id}/reply")
async def reply_to_online_inquiry(inquiry_id: int, request: InquiryReplyRequest):
    """
    상품별 고객문의 답변

    Args:
        inquiry_id: 문의 ID
        request: 답변 요청 (content가 없으면 ChatGPT 자동 생성)

    Returns:
        답변 결과
    """
    try:
        client = CoupangAPIClient()

        # reply_by 설정: wing_username 우선, 그 다음 환경변수, 마지막으로 vendor_id
        reply_by = None
        if request.credentials and request.credentials.wing_username:
            reply_by = request.credentials.wing_username
        elif request.reply_by:
            reply_by = request.reply_by
        elif settings.COUPANG_WING_ID:
            reply_by = settings.COUPANG_WING_ID
        else:
            reply_by = "A00492891"  # fallback

        logger.info(f"온라인 문의 답변 reply_by 설정: '{reply_by}'")

        # 문의 내용 조회 (답변 생성을 위해)
        if not request.content:
            # ChatGPT로 답변 생성
            # 먼저 문의 내용을 가져와야 함
            today = datetime.now().strftime("%Y-%m-%d")
            inquiries = client.get_online_inquiries(
                start_date=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                end_date=today,
                answered_type="ALL",
                page_size=50
            )

            # 해당 inquiry_id 찾기
            inquiry_content = None
            if inquiries.get("code") == 200:
                for inq in inquiries.get("data", {}).get("content", []):
                    if inq.get("inquiryId") == inquiry_id:
                        inquiry_content = inq.get("content")
                        break

            if not inquiry_content:
                raise HTTPException(
                    status_code=404,
                    detail=f"문의 ID {inquiry_id}를 찾을 수 없습니다"
                )

            # AI로 답변 생성
            ai_generator = AIResponseGenerator()
            generated_answer = ai_generator.generate_response_from_text(inquiry_content)
            content = generated_answer.get("response_text", "") if generated_answer else ""

            if not content:
                raise HTTPException(
                    status_code=500,
                    detail="ChatGPT 답변 생성 실패"
                )
        else:
            content = request.content

        # 답변 제출
        result = client.reply_to_online_inquiry(
            inquiry_id=inquiry_id,
            content=content,
            reply_by=reply_by
        )

        if result.get("code") != "200":
            raise HTTPException(
                status_code=int(result.get("code", 500)),
                detail=result.get("message", "Unknown error")
            )

        return {
            "success": True,
            "message": f"문의 {inquiry_id}에 답변 완료",
            "data": {
                "inquiry_id": inquiry_id,
                "content": content,
                "reply_by": reply_by
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"상품별 고객문의 답변 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inquiries/auto-answer")
async def auto_answer_inquiries(request: AutoAnswerRequest, http_request: Request):
    """
    고객문의 자동 답변 (ChatGPT 통합)

    미답변 문의를 조회하여 ChatGPT로 답변을 생성하고 자동으로 제출합니다.

    Args:
        request: 자동 답변 설정

    Returns:
        자동 답변 결과
    """
    db = SessionLocal()
    execution_log = None
    start_time = datetime.utcnow()

    try:
        # 기본 날짜 설정 (쿠팡 API는 최대 7일까지만 조회 가능하므로 3일로 설정)
        end_date = request.end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = request.start_date or (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

        # 날짜 범위가 7일을 초과하는지 검증
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        date_diff = (end_date_obj - start_date_obj).days

        if date_diff > 6:  # 7일 초과 (0~6일 = 7일)
            logger.warning(f"날짜 범위가 {date_diff + 1}일로 7일을 초과합니다. start_date를 조정합니다.")
            start_date_obj = end_date_obj - timedelta(days=6)
            start_date = start_date_obj.strftime("%Y-%m-%d")
            logger.info(f"조정된 날짜 범위: {start_date} ~ {end_date}")

        # account_id로 DB에서 계정 정보 가져오기
        selected_account = None
        if request.account_id:
            from ..models.coupang_account import CoupangAccount
            selected_account = db.query(CoupangAccount).filter(CoupangAccount.id == request.account_id).first()
            if selected_account:
                logger.info(f"계정 ID {request.account_id}로 계정 조회: {selected_account.name} (vendor: {selected_account.vendor_id})")
                # credentials 객체 생성
                request.credentials = CoupangAPICredentials(
                    access_key=selected_account.access_key,
                    secret_key=selected_account.secret_key,
                    vendor_id=selected_account.vendor_id,
                    wing_username=selected_account.wing_username
                )
            else:
                logger.warning(f"계정 ID {request.account_id}를 찾을 수 없습니다. 환경 변수 사용")

        # reply_by 설정: wing_username 우선, 그 다음 환경변수, 마지막으로 vendor_id
        reply_by = None
        if request.credentials and request.credentials.wing_username:
            reply_by = request.credentials.wing_username
        elif request.reply_by:
            reply_by = request.reply_by
        elif settings.COUPANG_WING_ID:
            reply_by = settings.COUPANG_WING_ID
        elif request.credentials and request.credentials.vendor_id:
            reply_by = request.credentials.vendor_id
        else:
            reply_by = "lhs0609"  # default wing username

        logger.info(f"자동 답변 reply_by 설정: '{reply_by}' (from credentials.wing_username or COUPANG_WING_ID)")

        # 실행 로그 생성
        execution_log = AutomationExecutionLog(
            execution_type="auto_answer_api",
            status="running",
            started_at=start_time,
            username=reply_by,
            headless_mode=True,  # API는 항상 headless
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent")
        )
        db.add(execution_log)
        db.commit()
        db.refresh(execution_log)

        logger.info(f"자동 답변 시작 (log_id={execution_log.id}): {start_date} ~ {end_date}")

        # 선택된 계정으로 클라이언트 생성
        client = _create_client(request.credentials)
        ai_generator = AIResponseGenerator() if request.auto_generate else None

        # 미답변 문의 조회
        inquiries_response = client.get_online_inquiries(
            start_date=start_date,
            end_date=end_date,
            answered_type=request.answered_type,
            page_size=50
        )

        if inquiries_response.get("code") != 200:
            raise HTTPException(
                status_code=inquiries_response.get("code", 500),
                detail=inquiries_response.get("message", "문의 조회 실패")
            )

        inquiries = inquiries_response.get("data", {}).get("content", [])
        total_inquiries = len(inquiries)

        logger.info(f"총 {total_inquiries}개의 문의 발견")

        # 통계
        stats = {
            "total_inquiries": total_inquiries,
            "answered": 0,
            "failed": 0,
            "skipped": 0
        }

        results = []

        for inquiry in inquiries:
            inquiry_id = inquiry.get("inquiryId")
            inquiry_content = inquiry.get("content")

            try:
                # 이미 답변이 있는지 확인
                if inquiry.get("commentDtoList"):
                    logger.info(f"문의 {inquiry_id}: 이미 답변 있음, 건너뜀")
                    stats["skipped"] += 1
                    continue

                # AI로 답변 생성
                if request.auto_generate and ai_generator:
                    generated = ai_generator.generate_response_from_text(inquiry_content)
                    answer_content = generated.get("response_text", "") if generated else ""
                else:
                    # 수동 답변이 필요한 경우
                    logger.warning(f"문의 {inquiry_id}: 자동 생성 비활성화, 건너뜀")
                    stats["skipped"] += 1
                    continue

                if not answer_content:
                    logger.error(f"문의 {inquiry_id}: 답변 생성 실패")
                    stats["failed"] += 1
                    continue

                # 답변 제출
                logger.info(f"문의 {inquiry_id}: reply_by 값 = '{reply_by}'")
                reply_result = client.reply_to_online_inquiry(
                    inquiry_id=inquiry_id,
                    content=answer_content,
                    reply_by=reply_by
                )

                if reply_result.get("code") in [200, "200"]:
                    logger.success(f"문의 {inquiry_id}: 답변 완료")
                    stats["answered"] += 1
                    results.append({
                        "inquiry_id": inquiry_id,
                        "status": "success",
                        "content": answer_content
                    })
                else:
                    logger.error(f"문의 {inquiry_id}: 답변 제출 실패 - {reply_result.get('message')}")
                    stats["failed"] += 1
                    results.append({
                        "inquiry_id": inquiry_id,
                        "status": "failed",
                        "error": reply_result.get("message")
                    })

            except Exception as e:
                logger.error(f"문의 {inquiry_id} 처리 중 오류: {str(e)}")
                stats["failed"] += 1
                results.append({
                    "inquiry_id": inquiry_id,
                    "status": "error",
                    "error": str(e)
                })

        # 실행 로그 업데이트
        end_time = datetime.utcnow()
        execution_log.status = "success"
        execution_log.completed_at = end_time
        execution_log.duration_seconds = int((end_time - start_time).total_seconds())
        execution_log.total_inquiries = stats["total_inquiries"]
        execution_log.answered_count = stats["answered"]
        execution_log.failed_count = stats["failed"]
        execution_log.skipped_count = stats["skipped"]
        db.commit()

        logger.success(f"자동 답변 완료 (log_id={execution_log.id}): {stats}")

        return {
            "success": True,
            "message": f"자동 답변 완료: {stats['answered']}/{total_inquiries}개 답변",
            "statistics": stats,
            "results": results
        }

    except Exception as e:
        logger.error(f"자동 답변 중 오류: {str(e)}")

        # 실행 로그 업데이트
        if execution_log:
            end_time = datetime.utcnow()
            execution_log.status = "failed"
            execution_log.completed_at = end_time
            execution_log.duration_seconds = int((end_time - start_time).total_seconds())
            execution_log.error_message = str(e)
            db.commit()

        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()


@router.get("/call-center-inquiries")
async def get_call_center_inquiries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: str = "NO_ANSWER",
    page_num: int = 1,
    page_size: int = 50
):
    """
    쿠팡 고객센터 문의 조회

    Args:
        start_date: 조회시작일 (yyyy-MM-dd)
        end_date: 조회종료일 (yyyy-MM-dd)
        status: 문의 상태 (partnerCounselingStatus: 'NO_ANSWER', 'TRANSFER', 'ANSWER', 'NONE')
               NO_ANSWER = 미답변 (판매자의 답변이 필요한 상태)
               TRANSFER = 미확인 (판매자의 확인이 필요한 상태)
        page_num: 페이지 번호
        page_size: 페이지 크기

    Returns:
        고객센터 문의 목록
    """
    try:
        # 기본 날짜 설정
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

        client = CoupangAPIClient()
        result = client.get_call_center_inquiries(
            start_date=start_date,
            end_date=end_date,
            status=status,
            page_num=page_num,
            page_size=page_size
        )

        return {
            "success": True,
            "data": result,
            "message": f"{start_date} ~ {end_date} 기간 고객센터 문의 조회 완료"
        }

    except Exception as e:
        logger.error(f"고객센터 문의 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/call-center-inquiries/auto-answer")
async def auto_answer_call_center_inquiries(http_request: Request, request: AutoAnswerRequest = None):
    """
    고객센터 문의 자동 답변 (ChatGPT 통합)

    진행 중인 고객센터 문의를 조회하여 ChatGPT로 답변을 생성하고 자동으로 제출합니다.

    Args:
        request: 자동 답변 설정 (credentials 포함)

    Returns:
        자동 답변 결과
    """
    db = SessionLocal()
    execution_log = None
    start_time = datetime.utcnow()

    try:
        # request가 None이면 기본값 사용
        if request is None:
            request = AutoAnswerRequest()

        # 기본 날짜 설정 (3일)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

        # account_id로 DB에서 계정 정보 가져오기
        selected_account = None
        if request.account_id:
            from ..models.coupang_account import CoupangAccount
            selected_account = db.query(CoupangAccount).filter(CoupangAccount.id == request.account_id).first()
            if selected_account:
                logger.info(f"계정 ID {request.account_id}로 계정 조회: {selected_account.name} (vendor: {selected_account.vendor_id})")
                # credentials 객체 생성
                request.credentials = CoupangAPICredentials(
                    access_key=selected_account.access_key,
                    secret_key=selected_account.secret_key,
                    vendor_id=selected_account.vendor_id,
                    wing_username=selected_account.wing_username
                )
            else:
                logger.warning(f"계정 ID {request.account_id}를 찾을 수 없습니다. 환경 변수 사용")

        # reply_by 설정: wing_username 우선, 그 다음 환경변수, 마지막으로 vendor_id
        reply_by = None
        if request.credentials and request.credentials.wing_username:
            reply_by = request.credentials.wing_username
        elif request.reply_by:
            reply_by = request.reply_by
        elif settings.COUPANG_WING_ID:
            reply_by = settings.COUPANG_WING_ID
        elif request.credentials and request.credentials.vendor_id:
            reply_by = request.credentials.vendor_id
        else:
            reply_by = "lhs0609"  # default wing username

        logger.info(f"고객센터 자동 답변 reply_by 설정: '{reply_by}' (from credentials.wing_username or COUPANG_WING_ID)")

        # 실행 로그 생성
        execution_log = AutomationExecutionLog(
            execution_type="auto_answer_callcenter",
            status="running",
            started_at=start_time,
            username=reply_by,
            headless_mode=True,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent")
        )
        db.add(execution_log)
        db.commit()
        db.refresh(execution_log)

        logger.info(f"고객센터 자동 답변 시작 (log_id={execution_log.id}): {start_date} ~ {end_date}")

        # 선택된 계정으로 클라이언트 생성
        client = _create_client(request.credentials)
        ai_generator = AIResponseGenerator()

        # 1. 답변이 필요한 문의 조회 (NO_ANSWER)
        no_answer_response = client.get_call_center_inquiries(
            start_date=start_date,
            end_date=end_date,
            status="NO_ANSWER",  # 답변이 필요한 문의
            page_size=50
        )

        if no_answer_response.get("code") != 200:
            raise HTTPException(
                status_code=no_answer_response.get("code", 500),
                detail=no_answer_response.get("message", "고객센터 문의 조회 실패")
            )

        # 2. 확인완료가 필요한 문의 조회 (TRANSFER)
        transfer_response = client.get_call_center_inquiries(
            start_date=start_date,
            end_date=end_date,
            status="TRANSFER",  # 확인완료가 필요한 문의
            page_size=50
        )

        if transfer_response.get("code") != 200:
            raise HTTPException(
                status_code=transfer_response.get("code", 500),
                detail=transfer_response.get("message", "고객센터 문의 조회 실패")
            )

        no_answer_inquiries = no_answer_response.get("data", {}).get("content", [])
        transfer_inquiries = transfer_response.get("data", {}).get("content", [])

        total_inquiries = len(no_answer_inquiries) + len(transfer_inquiries)

        logger.info(f"총 {total_inquiries}개의 고객센터 문의 발견 (답변 필요: {len(no_answer_inquiries)}개, 확인 필요: {len(transfer_inquiries)}개)")

        # 통계
        stats = {
            "total_inquiries": total_inquiries,
            "answered": 0,
            "confirmed": 0,
            "failed": 0,
            "skipped": 0
        }

        results = []

        # NO_ANSWER 문의 처리 (답변 작성)
        logger.info(f"===== NO_ANSWER 문의 처리 시작 ({len(no_answer_inquiries)}개) =====")
        for inquiry in no_answer_inquiries:
            inquiry_id = inquiry.get("inquiryId")
            inquiry_content = inquiry.get("content", "")
            cs_status = inquiry.get("csPartnerCounselingStatus", "")

            try:
                # 이미 답변 완료된 문의인지 확인
                if cs_status == "answered":
                    logger.info(f"고객센터 문의 {inquiry_id}: 이미 답변 완료, 건너뜀")
                    stats["skipped"] += 1
                    continue

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
                                logger.info(f"고객센터 문의 {inquiry_id}: 특수 양식 요구 케이스 감지, 건너뜀")
                                break

                        break

                if parent_answer_id == 0:
                    logger.warning(f"고객센터 문의 {inquiry_id}: parentAnswerId를 찾을 수 없음, 건너뜀")
                    stats["skipped"] += 1
                    continue

                # AI로 답변 생성
                if is_special_case:
                    # 특수 케이스: 링크 답변 요구 시 안내 답변 생성
                    logger.info(f"고객센터 문의 {inquiry_id}: 특수 양식 케이스, 안내 답변 생성")
                    answer_content = """안녕하세요, 고객님.

문의 주신 내용을 확인하였습니다. 해당 문의는 상담사가 요청한 특정 양식을 통해 답변이 필요한 사항입니다.

원활한 처리를 위해 상담사가 제공한 링크를 통해 회신해 주시기 바랍니다. 링크를 통한 답변이 완료되면 보다 신속하게 처리가 가능합니다.

추가로 궁금하신 사항이 있으시면 언제든지 문의해주세요.

감사합니다."""
                else:
                    # 일반 케이스: AI로 답변 생성
                    generated = ai_generator.generate_response_from_text(
                        inquiry_content,
                        customer_name=inquiry.get("buyerName", "고객")
                    )
                    answer_content = generated.get("response_text", "") if generated else ""

                if not answer_content:
                    logger.error(f"고객센터 문의 {inquiry_id}: 답변 생성 실패")
                    stats["failed"] += 1
                    continue

                # 답변 제출
                reply_result = client.reply_to_call_center_inquiry(
                    inquiry_id=inquiry_id,
                    content=answer_content,
                    reply_by=reply_by,
                    parent_answer_id=parent_answer_id
                )

                if reply_result.get("code") in [200, "200"]:
                    # NO_ANSWER 상태 문의는 답변만 필요 (확인 불필요)
                    # TRANSFER 상태 문의만 확인(confirm)이 필요함
                    logger.success(f"고객센터 문의 {inquiry_id}: 답변 완료")
                    stats["answered"] += 1
                    results.append({
                        "inquiry_id": inquiry_id,
                        "status": "success",
                        "content": answer_content
                    })
                else:
                    logger.error(f"고객센터 문의 {inquiry_id}: 답변 제출 실패 - {reply_result.get('message')}")
                    stats["failed"] += 1
                    results.append({
                        "inquiry_id": inquiry_id,
                        "status": "failed",
                        "error": reply_result.get("message")
                    })

            except Exception as e:
                logger.error(f"고객센터 문의 {inquiry_id} 처리 중 오류: {str(e)}")
                stats["failed"] += 1
                results.append({
                    "inquiry_id": inquiry_id,
                    "status": "error",
                    "error": str(e)
                })

        # TRANSFER 문의 처리 (확인완료 버튼 클릭)
        logger.info(f"===== TRANSFER 문의 처리 시작 ({len(transfer_inquiries)}개) =====")
        for inquiry in transfer_inquiries:
            inquiry_id = inquiry.get("inquiryId")
            inquiry_content = inquiry.get("content", "")

            try:
                logger.info(f"고객센터 문의 {inquiry_id}: 확인완료 처리")

                # 확인완료 (confirm) 수행
                confirm_result = client.confirm_call_center_inquiry(
                    inquiry_id=inquiry_id,
                    confirm_by=reply_by
                )

                if confirm_result.get("code") in [200, "200"]:
                    logger.success(f"고객센터 문의 {inquiry_id}: 확인완료 처리 완료")
                    stats["confirmed"] += 1
                    results.append({
                        "inquiry_id": inquiry_id,
                        "status": "confirmed",
                        "type": "TRANSFER"
                    })
                else:
                    logger.error(f"고객센터 문의 {inquiry_id}: 확인완료 실패 - {confirm_result.get('message')}")
                    stats["failed"] += 1
                    results.append({
                        "inquiry_id": inquiry_id,
                        "status": "failed",
                        "error": confirm_result.get("message")
                    })

            except Exception as e:
                logger.error(f"고객센터 문의 {inquiry_id} 확인완료 처리 중 오류: {str(e)}")
                stats["failed"] += 1
                results.append({
                    "inquiry_id": inquiry_id,
                    "status": "error",
                    "error": str(e)
                })

        # 실행 로그 업데이트
        end_time = datetime.utcnow()
        execution_log.status = "success"
        execution_log.completed_at = end_time
        execution_log.duration_seconds = int((end_time - start_time).total_seconds())
        execution_log.total_inquiries = stats["total_inquiries"]
        execution_log.answered_count = stats["answered"]
        execution_log.failed_count = stats["failed"]
        execution_log.skipped_count = stats["skipped"]
        db.commit()

        logger.success(f"고객센터 자동 답변 완료 (log_id={execution_log.id}): {stats}")

        return {
            "success": True,
            "message": f"고객센터 자동화 완료: {stats['answered']}개 답변, {stats['confirmed']}개 확인완료 (총 {total_inquiries}개)",
            "statistics": stats,
            "results": results
        }

    except Exception as e:
        logger.error(f"고객센터 자동 답변 중 오류: {str(e)}")

        # 실행 로그 업데이트
        if execution_log:
            end_time = datetime.utcnow()
            execution_log.status = "failed"
            execution_log.completed_at = end_time
            execution_log.duration_seconds = int((end_time - start_time).total_seconds())
            execution_log.error_message = str(e)
            db.commit()

        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()
