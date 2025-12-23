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
from ..services.auto_mode_service import AutoModeService
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


@router.post("/cycle", response_model=AutoModeCycleResponse)
def run_auto_cycle(
    request: AutoModeCycleRequest,
    db: Session = Depends(get_db)
):
    """
    자동모드 단일 사이클 실행

    1. 선택된 계정으로 미답변 문의 수집 (online + callcenter)
    2. AI 답변 생성
    3. 자동 제출

    Args:
        request: 사이클 실행 요청 정보
        db: 데이터베이스 세션

    Returns:
        사이클 실행 결과
    """
    logger.info(f"자동모드 사이클 시작 - 계정 ID: {request.account_id}")

    try:
        # 계정 확인
        account = db.query(CoupangAccount).filter(
            CoupangAccount.id == request.account_id
        ).first()

        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다")

        # 계정 정보 유효성 확인
        if not account.access_key or not account.secret_key or not account.vendor_id:
            raise HTTPException(
                status_code=400,
                detail="계정의 API 인증 정보가 불완전합니다"
            )

        # 자동모드 서비스 실행
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
    """
    자동모드 상태 조회

    Returns:
        서버 상태 정보
    """
    return {
        "status": "ready",
        "message": "자동모드 API가 정상 작동 중입니다",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/test/{account_id}")
def test_account_connection(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    계정 연결 테스트

    Args:
        account_id: 테스트할 계정 ID
        db: 데이터베이스 세션

    Returns:
        연결 테스트 결과
    """
    try:
        # 계정 조회
        account = db.query(CoupangAccount).filter(
            CoupangAccount.id == account_id
        ).first()

        if not account:
            raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다")

        # API 클라이언트로 간단한 테스트
        from ..services.coupang_api_client import CoupangAPIClient
        from datetime import datetime, timedelta

        client = CoupangAPIClient(
            access_key=account.access_key,
            secret_key=account.secret_key,
            vendor_id=account.vendor_id
        )

        # 오늘 날짜로 문의 조회 테스트
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        result = client.get_online_inquiries(
            start_date=start_date,
            end_date=end_date,
            answered_type="ALL",
            page_size=1
        )

        if result.get("code") == "SUCCESS":
            return {
                "success": True,
                "message": "API 연결 성공",
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
