"""
Auto Mode API Router - 실시간 자동모드 API
주기적으로 문의를 수집하고 AI 답변을 생성하여 자동 제출하는 기능
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from loguru import logger

from ..database import get_db
from ..services.auto_mode_service import AutoModeService, get_session_manager
from ..models import CoupangAccount

router = APIRouter(prefix="/auto-mode", tags=["auto-mode"])


class AutoModeCycleRequest(BaseModel):
    """자동모드 사이클 실행 요청"""
    account_id: int
    inquiry_types: List[str] = ["online", "callcenter"]
    auto_submit: bool = True
    wing_id: Optional[str] = "system"


class AutoModeCycleResponse(BaseModel):
    """자동모드 사이클 실행 결과"""
    success: bool
    message: str
    collected: int = 0
    answered: int = 0
    submitted: int = 0
    failed: int = 0
    details: Optional[dict] = None
    errors: Optional[List[str]] = None
    executed_at: datetime


class CreateSessionRequest(BaseModel):
    """세션 생성 요청"""
    account_id: int
    interval_minutes: int = 5
    inquiry_types: List[str] = ["online", "callcenter"]


class SessionResponse(BaseModel):
    """세션 정보 응답"""
    session_id: str
    account_id: int
    account_name: str
    vendor_id: str
    interval_minutes: int
    inquiry_types: List[str]
    status: str
    created_at: str
    last_run: Optional[str]
    next_run: Optional[str]
    stats: dict
    recent_logs: List[dict]


# ============== 세션 관리 API ==============

@router.post("/sessions", response_model=SessionResponse)
def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
):
    """
    새 자동모드 세션 생성 및 시작

    백그라운드에서 주기적으로 실행됩니다.
    화면을 닫아도 계속 실행됩니다.
    """
    logger.info(f"세션 생성 요청 - 계정 ID: {request.account_id}")

    # 계정 확인
    account = db.query(CoupangAccount).filter(
        CoupangAccount.id == request.account_id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다")

    if not account.access_key or not account.secret_key or not account.vendor_id:
        raise HTTPException(
            status_code=400,
            detail="계정의 API 인증 정보가 불완전합니다"
        )

    # 세션 관리자에서 세션 생성
    manager = get_session_manager()
    session_id = manager.create_session(
        account_id=account.id,
        account_name=account.name,
        vendor_id=account.vendor_id,
        interval_minutes=request.interval_minutes,
        inquiry_types=request.inquiry_types,
        account=account
    )

    session = manager.get_session(session_id)
    return session


@router.get("/sessions", response_model=List[SessionResponse])
def get_all_sessions():
    """모든 실행 중인 자동모드 세션 목록 조회"""
    manager = get_session_manager()
    return manager.get_all_sessions()


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    """특정 세션 정보 조회"""
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    return session


@router.post("/sessions/{session_id}/stop")
def stop_session(session_id: str):
    """세션 중지"""
    manager = get_session_manager()

    if manager.stop_session(session_id):
        return {"success": True, "message": "세션이 중지되었습니다"}
    else:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")


@router.post("/sessions/{session_id}/start")
def start_session(session_id: str):
    """중지된 세션 재시작"""
    manager = get_session_manager()

    if manager.start_session(session_id):
        return {"success": True, "message": "세션이 시작되었습니다"}
    else:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """세션 삭제"""
    manager = get_session_manager()

    if manager.delete_session(session_id):
        return {"success": True, "message": "세션이 삭제되었습니다"}
    else:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")


# ============== 기존 단일 사이클 API ==============

@router.post("/cycle", response_model=AutoModeCycleResponse)
def run_auto_cycle(
    request: AutoModeCycleRequest,
    db: Session = Depends(get_db)
):
    """
    자동모드 단일 사이클 실행 (세션 없이 1회 실행)

    1. 선택된 계정으로 미답변 문의 수집 (online + callcenter)
    2. AI 답변 생성
    3. 자동 제출
    """
    logger.info(f"자동모드 사이클 시작 - 계정 ID: {request.account_id}")

    try:
        account = db.query(CoupangAccount).filter(
            CoupangAccount.id == request.account_id
        ).first()

        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다")

        if not account.access_key or not account.secret_key or not account.vendor_id:
            raise HTTPException(
                status_code=400,
                detail="계정의 API 인증 정보가 불완전합니다"
            )

        service = AutoModeService()
        result = service.run_full_cycle(
            account=account,
            inquiry_types=request.inquiry_types,
            auto_submit=request.auto_submit,
            wing_id=request.wing_id or "system"
        )

        success = len(result.get("errors", [])) == 0
        message = "자동모드 사이클이 성공적으로 완료되었습니다" if success else "일부 오류가 발생했습니다"

        logger.info(
            f"자동모드 사이클 완료 - "
            f"수집: {result['collected']}, "
            f"답변: {result['answered']}, "
            f"제출: {result['submitted']}, "
            f"실패: {result['failed']}"
        )

        return AutoModeCycleResponse(
            success=success,
            message=message,
            collected=result["collected"],
            answered=result["answered"],
            submitted=result["submitted"],
            failed=result["failed"],
            details=result.get("details"),
            errors=result.get("errors") if result.get("errors") else None,
            executed_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동모드 사이클 오류: {str(e)}")
        return AutoModeCycleResponse(
            success=False,
            message=f"실행 중 오류 발생: {str(e)}",
            errors=[str(e)],
            executed_at=datetime.utcnow()
        )


@router.get("/status")
def get_auto_mode_status():
    """자동모드 상태 조회"""
    manager = get_session_manager()
    sessions = manager.get_all_sessions()
    running_count = sum(1 for s in sessions if s["status"] == "running")

    return {
        "status": "ready",
        "message": "자동모드 API가 정상 작동 중입니다",
        "active_sessions": running_count,
        "total_sessions": len(sessions),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/test/{account_id}")
def test_account_connection(
    account_id: int,
    db: Session = Depends(get_db)
):
    """계정 연결 테스트"""
    try:
        account = db.query(CoupangAccount).filter(
            CoupangAccount.id == account_id
        ).first()

        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다")

        from ..services.coupang_api_client import CoupangAPIClient
        from datetime import timedelta

        client = CoupangAPIClient(
            access_key=account.access_key,
            secret_key=account.secret_key,
            vendor_id=account.vendor_id
        )

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')  # API는 7일 이내만 허용

        result = client.get_online_inquiries(
            start_date=start_date,
            end_date=end_date,
            answered_type="ALL",
            page_size=1
        )

        # API는 성공 시 code: 200 또는 code: "SUCCESS" 반환
        if result.get("code") in [200, "200", "SUCCESS"]:
            total = result.get("data", {}).get("pagination", {}).get("totalElements", 0)
            return {
                "success": True,
                "message": f"API 연결 성공 (미답변 문의: {total}건)",
                "account_name": account.name,
                "vendor_id": account.vendor_id
            }
        else:
            return {
                "success": False,
                "message": f"API 오류: {result.get('message', '알 수 없는 오류')}",
                "account_name": account.name
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"연결 테스트 오류: {str(e)}")
        return {
            "success": False,
            "message": f"연결 테스트 실패: {str(e)}"
        }
