"""
Wing Web Automation Router
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from pydantic import BaseModel
from loguru import logger
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..services.wing_web_automation import WingWebAutomation
from ..services.wing_web_automation_v2 import WingWebAutomationV2
from ..services.wing_web_automation_v3 import WingWebAutomationV3
from ..config import settings
from ..database import SessionLocal, get_db
from ..models.automation_log import AutomationExecutionLog
from ..models.coupang_account import CoupangAccount


router = APIRouter(prefix="/wing-web", tags=["Wing Web Automation"])


def get_credentials_from_db(db: Session) -> tuple[Optional[str], Optional[str]]:
    """
    데이터베이스에서 활성화된 계정 정보 가져오기

    Returns:
        (username, password) tuple or (None, None) if not found
    """
    try:
        # 활성화된 계정 중 가장 최근에 사용된 계정 가져오기
        account = db.query(CoupangAccount)\
            .filter(CoupangAccount.is_active == True)\
            .order_by(CoupangAccount.last_used_at.desc())\
            .first()

        if account and account.wing_username:
            logger.info(f"데이터베이스에서 계정 정보를 불러왔습니다: {account.name} ({account.wing_username})")
            # 데이터베이스에서 암호화된 비밀번호를 복호화하여 반환
            password = account.wing_password if account.wing_password else settings.COUPANG_WING_PASSWORD

            # 계정 마지막 사용 시간 업데이트
            account.last_used_at = datetime.utcnow()
            db.commit()

            return account.wing_username, password

        return None, None
    except Exception as e:
        logger.error(f"데이터베이스에서 계정 정보를 가져오는 중 오류 발생: {str(e)}")
        return None, None


class WebAutomationRequest(BaseModel):
    """Request model for web automation"""
    username: Optional[str] = None
    password: Optional[str] = None
    headless: bool = True


class WebAutomationResponse(BaseModel):
    """Response model for web automation"""
    success: bool
    message: str
    statistics: dict


@router.post("/auto-answer", response_model=WebAutomationResponse)
async def auto_answer_inquiries(request: WebAutomationRequest):
    """
    Automatically answer all inquiries on Coupang Wing website

    This endpoint will:
    1. Login to Coupang Wing
    2. Navigate to product inquiries page
    3. Read all inquiries
    4. Generate answers using ChatGPT
    5. Submit answers automatically

    Args:
        request: WebAutomationRequest with optional credentials and headless mode

    Returns:
        WebAutomationResponse with results
    """
    try:
        # Get credentials from request or environment
        username = request.username or settings.COUPANG_WING_USERNAME
        password = request.password or settings.COUPANG_WING_PASSWORD

        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="Username and password are required. Please provide them in the request or set COUPANG_WING_USERNAME and COUPANG_WING_PASSWORD in .env file"
            )

        logger.info(f"Starting web automation (headless={request.headless})...")

        # Create automation instance
        automation = WingWebAutomation(
            username=username,
            password=password,
            headless=request.headless
        )

        # Run full automation
        results = automation.run_full_automation()

        return WebAutomationResponse(
            success=results['success'],
            message=results['message'],
            statistics=results.get('statistics', {})
        )

    except Exception as e:
        logger.error(f"Error in auto_answer_inquiries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-answer-v2", response_model=WebAutomationResponse)
async def auto_answer_inquiries_v2(request: WebAutomationRequest, http_request: Request):
    """
    자동 답변 V2 - 실제 HTML 구조 기반

    개선사항:
    - 시간대별 탭 자동 전환 (72시간~30일, 24~72시간, 24시간 이내)
    - 모든 탭 확인 후 문의 없으면 자동 종료
    - 실제 쿠팡윙 HTML 구조에 맞춤
    - 더 정확한 요소 탐색
    - 상세한 로깅

    Args:
        request: 로그인 정보 및 headless 모드 설정

    Returns:
        처리 결과 및 통계
    """
    db = SessionLocal()
    execution_log = None
    start_time = datetime.utcnow()

    try:
        # 먼저 요청에서 계정 정보 확인
        username = request.username
        password = request.password

        # 요청에 없으면 데이터베이스에서 가져오기
        if not username or not password:
            db_username, db_password = get_credentials_from_db(db)
            username = username or db_username
            password = password or db_password

        # 그래도 없으면 환경변수에서 가져오기
        if not username or not password:
            username = username or settings.COUPANG_WING_USERNAME
            password = password or settings.COUPANG_WING_PASSWORD

        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="아이디와 비밀번호가 필요합니다. 쿠팡 계정을 먼저 등록하거나 .env 파일에 COUPANG_WING_USERNAME과 COUPANG_WING_PASSWORD를 설정하세요."
            )

        # Create initial log entry
        execution_log = AutomationExecutionLog(
            execution_type="auto_answer_v2",
            status="running",
            started_at=start_time,
            username=username,
            headless_mode=request.headless,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent")
        )
        db.add(execution_log)
        db.commit()
        db.refresh(execution_log)

        logger.info(f"V2 자동화 시작 (headless={request.headless}, log_id={execution_log.id})...")

        # V2 자동화 인스턴스 생성
        automation = WingWebAutomationV2(
            username=username,
            password=password,
            headless=request.headless
        )

        # 전체 자동화 실행
        results = automation.run_full_automation()

        # Update log with results
        end_time = datetime.utcnow()
        duration_seconds = int((end_time - start_time).total_seconds())

        execution_log.status = "success" if results.get('success', False) else "failed"
        execution_log.completed_at = end_time
        execution_log.duration_seconds = duration_seconds
        execution_log.total_inquiries = results.get('total_inquiries', 0)
        execution_log.answered = results.get('answered', 0)
        execution_log.failed = results.get('failed', 0)
        execution_log.skipped = results.get('skipped', 0)
        execution_log.details = results

        db.commit()
        logger.success(f"V2 자동화 완료 (log_id={execution_log.id}, duration={duration_seconds}s)")

        return WebAutomationResponse(
            success=results.get('success', False),
            message=results.get('message', ''),
            statistics={
                "total_inquiries": results.get('total_inquiries', 0),
                "answered": results.get('answered', 0),
                "failed": results.get('failed', 0),
                "skipped": results.get('skipped', 0)
            }
        )

    except Exception as e:
        logger.error(f"V2 자동화 오류: {str(e)}")

        # Update log with error
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


@router.post("/auto-answer-v3", response_model=WebAutomationResponse)
async def auto_answer_inquiries_v3(request: WebAutomationRequest):
    """
    자동 답변 V3 - 모든 탭에서 미답변이 없을 때까지 반복

    V3 개선사항:
    - ✅ 모든 탭에서 미답변이 없을 때까지 무한 반복
    - ✅ 사용자 제공 HTML 구조에 정확히 매칭
    - ✅ replying-no-comments 클래스로 미답변만 정확히 식별
    - ✅ 시간대별 탭 자동 순회 (72시간~30일 이내 → 24~72시간 → 24시간 이내)
    - ✅ ChatGPT API로 답변 자동 생성
    - ✅ 답변 입력 및 저장 자동화
    - ✅ 상세한 로깅 및 에러 핸들링
    - ✅ 최대 반복 횟수로 무한루프 방지

    HTML 구조:
    - 문의 셀: <td class="replying-no-comments">
    - 상품명: <div class="text-wrapper product-name"><a><span title="상품명">
    - 문의내용: <span class="inquiry-content">고객 문의 내용</span>
    - 답변버튼: <button>답변하기</button>
    - 답변입력: <textarea class="input-textarea">
    - 저장버튼: <button>저장하기</button>

    Args:
        request: 로그인 정보 및 headless 모드 설정

    Returns:
        처리 결과 및 통계
    """
    db = SessionLocal()
    try:
        # 먼저 요청에서 계정 정보 확인
        username = request.username
        password = request.password

        # 요청에 없으면 데이터베이스에서 가져오기
        if not username or not password:
            db_username, db_password = get_credentials_from_db(db)
            username = username or db_username
            password = password or db_password

        # 그래도 없으면 환경변수에서 가져오기
        if not username or not password:
            username = username or settings.COUPANG_WING_USERNAME
            password = password or settings.COUPANG_WING_PASSWORD

        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="아이디와 비밀번호가 필요합니다. 쿠팡 계정을 먼저 등록하거나 .env 파일에 COUPANG_WING_USERNAME과 COUPANG_WING_PASSWORD를 설정하세요."
            )

        logger.info(f"V3 자동화 시작 (headless={request.headless})...")
        logger.info("📌 모든 탭에서 미답변이 없을 때까지 반복 실행합니다.")

        # V3 자동화 인스턴스 생성
        automation = WingWebAutomationV3(
            username=username,
            password=password,
            headless=request.headless,
            max_rounds=100  # 최대 100회 반복
        )

        # 전체 자동화 실행 (무한 반복)
        results = automation.run_full_automation_loop()

        return WebAutomationResponse(
            success=results.get('success', False),
            message=results.get('message', ''),
            statistics=results.get('statistics', {})
        )

    except Exception as e:
        logger.error(f"V3 자동화 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()


@router.post("/test-login")
async def test_login(request: WebAutomationRequest, http_request: Request):
    """
    Test login to Coupang Wing

    Args:
        request: WebAutomationRequest with credentials

    Returns:
        Login test result
    """
    db = SessionLocal()
    execution_log = None
    start_time = datetime.utcnow()

    try:
        username = request.username or settings.COUPANG_WING_USERNAME
        password = request.password or settings.COUPANG_WING_PASSWORD

        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="Username and password are required"
            )

        # Create initial log entry
        execution_log = AutomationExecutionLog(
            execution_type="test_login",
            status="running",
            started_at=start_time,
            username=username,
            headless_mode=request.headless,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent")
        )
        db.add(execution_log)
        db.commit()
        db.refresh(execution_log)

        logger.info(f"Testing login (log_id={execution_log.id})...")

        automation = WingWebAutomation(
            username=username,
            password=password,
            headless=request.headless
        )

        try:
            if not automation.setup_driver():
                # Update log with failure
                end_time = datetime.utcnow()
                execution_log.status = "failed"
                execution_log.completed_at = end_time
                execution_log.duration_seconds = int((end_time - start_time).total_seconds())
                execution_log.error_message = "Failed to setup WebDriver"
                db.commit()

                return {"success": False, "message": "Failed to setup WebDriver"}

            if automation.login():
                # Update log with success
                end_time = datetime.utcnow()
                execution_log.status = "success"
                execution_log.completed_at = end_time
                execution_log.duration_seconds = int((end_time - start_time).total_seconds())
                db.commit()

                logger.success(f"Login test successful (log_id={execution_log.id})")
                return {"success": True, "message": "Login successful"}
            else:
                # Update log with failure
                end_time = datetime.utcnow()
                execution_log.status = "failed"
                execution_log.completed_at = end_time
                execution_log.duration_seconds = int((end_time - start_time).total_seconds())
                execution_log.error_message = "Login failed"
                db.commit()

                return {"success": False, "message": "Login failed"}
        finally:
            automation.cleanup()

    except Exception as e:
        logger.error(f"Error in test_login: {str(e)}")

        # Update log with error
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


@router.get("/execution-logs")
async def get_execution_logs(
    limit: int = 50,
    execution_type: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Get automation execution logs

    Args:
        limit: Maximum number of logs to return (default: 50)
        execution_type: Filter by execution type (test_login, auto_answer_v2, etc.)
        status: Filter by status (success, failed, running)

    Returns:
        List of execution logs
    """
    db = SessionLocal()
    try:
        query = db.query(AutomationExecutionLog)

        if execution_type:
            query = query.filter(AutomationExecutionLog.execution_type == execution_type)

        if status:
            query = query.filter(AutomationExecutionLog.status == status)

        logs = query.order_by(AutomationExecutionLog.started_at.desc()).limit(limit).all()

        return {
            "success": True,
            "count": len(logs),
            "logs": [log.to_dict() for log in logs]
        }

    except Exception as e:
        logger.error(f"Error fetching execution logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/execution-logs/{log_id}")
async def get_execution_log_detail(log_id: int):
    """
    Get detailed information about a specific execution log

    Args:
        log_id: ID of the execution log

    Returns:
        Detailed execution log information
    """
    db = SessionLocal()
    try:
        log = db.query(AutomationExecutionLog).filter(AutomationExecutionLog.id == log_id).first()

        if not log:
            raise HTTPException(status_code=404, detail="Execution log not found")

        return {
            "success": True,
            "log": log.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution log detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/status")
async def get_automation_status():
    """
    Get automation service status

    Returns:
        Service status information
    """
    return {
        "service": "Wing Web Automation",
        "status": "available",
        "versions": {
            "v1": "Basic automation",
            "v2": "Tab-based automation (one pass)",
            "v3": "Loop automation (until all answered) - RECOMMENDED"
        },
        "features": [
            "Automatic login to Coupang Wing",
            "Multi-tab inquiry scanning (72시간~30일, 24~72시간, 24시간 이내)",
            "Read unanswered product inquiries",
            "Generate answers using ChatGPT",
            "Submit answers automatically",
            "Loop until all inquiries are answered (V3)"
        ],
        "requirements": [
            "COUPANG_WING_USERNAME",
            "COUPANG_WING_PASSWORD",
            "OPENAI_API_KEY"
        ],
        "endpoints": {
            "/wing-web/auto-answer": "V1 - Basic automation",
            "/wing-web/auto-answer-v2": "V2 - Single pass through all tabs",
            "/wing-web/auto-answer-v3": "V3 - Loop until all answered (RECOMMENDED)",
            "/wing-web/test-login": "Test login credentials",
            "/wing-web/execution-logs": "Get automation execution logs",
            "/wing-web/status": "Service status"
        }
    }
