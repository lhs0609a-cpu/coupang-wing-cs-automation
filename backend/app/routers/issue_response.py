"""
Issue Response API Router
쿠팡 판매 문제 대응 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..services.issue_response_service import IssueResponseService

router = APIRouter(prefix="/issue-response", tags=["issue-response"])


# Pydantic Schemas
class AnalyzeRequest(BaseModel):
    """문제 분석 요청"""
    content: str
    coupang_account_id: Optional[int] = None


class GenerateRequest(BaseModel):
    """답변 생성 요청"""
    issue_id: int
    response_type: str = "appeal"  # appeal, statement, report
    additional_context: Optional[str] = ""
    seller_name: Optional[str] = ""


class UpdateStatusRequest(BaseModel):
    """상태 업데이트 요청"""
    status: str  # draft, copied, resolved
    resolution_notes: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """분석 결과 응답"""
    id: int
    issue_type: str
    issue_type_name: str
    issue_subtype: Optional[str]
    severity: str
    summary: Optional[str]
    deadline: Optional[str]
    recommended_actions: List[str]

    class Config:
        from_attributes = True


class GenerateResponse(BaseModel):
    """답변 생성 결과"""
    id: int
    generated_response: str
    response_type: str
    confidence: int
    suggestions: List[str]
    template_used: Optional[str]


# API Endpoints

@router.post("/analyze")
def analyze_issue(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    문제 내용 분석 및 유형 분류

    - 메일/알림 내용을 분석하여 문제 유형 분류
    - AI를 통한 상세 분석 및 권장 조치 제안
    """
    try:
        service = IssueResponseService(db)
        result = service.analyze_issue(
            content=request.content,
            coupang_account_id=request.coupang_account_id
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
def generate_response(
    request: GenerateRequest,
    db: Session = Depends(get_db)
):
    """
    AI 답변 생성

    - 분석된 문제에 대한 답변 생성
    - 가이드라인 및 템플릿 기반 답변 작성
    """
    try:
        service = IssueResponseService(db)
        result = service.generate_response(
            issue_id=request.issue_id,
            response_type=request.response_type,
            additional_context=request.additional_context or "",
            seller_name=request.seller_name or ""
        )
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guides")
def get_all_guides(db: Session = Depends(get_db)):
    """
    모든 가이드라인 조회

    - 지재권 침해, 리셀러, 상품 삭제/정지, 기타 문제
    """
    try:
        service = IssueResponseService(db)
        guides = service.get_all_guides()
        return {
            "success": True,
            "data": guides
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guides/{issue_type}")
def get_guide(
    issue_type: str,
    db: Session = Depends(get_db)
):
    """
    특정 문제 유형 가이드라인 조회

    - issue_type: ip_infringement, reseller, suspension, other
    """
    try:
        service = IssueResponseService(db)
        guide = service.get_guide(issue_type)
        if not guide:
            raise HTTPException(status_code=404, detail=f"Guide not found: {issue_type}")
        return {
            "success": True,
            "data": guide
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{issue_type}")
def get_templates(
    issue_type: str,
    subtype: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    문제 유형별 템플릿 목록 조회
    """
    try:
        service = IssueResponseService(db)
        templates = service.get_templates(issue_type, subtype)
        return {
            "success": True,
            "data": templates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def get_history(
    coupang_account_id: Optional[int] = None,
    issue_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    이전 대응 이력 조회
    """
    try:
        service = IssueResponseService(db)
        history = service.get_history(
            coupang_account_id=coupang_account_id,
            issue_type=issue_type,
            limit=limit,
            offset=offset
        )
        return {
            "success": True,
            "data": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
def get_statistics(
    coupang_account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    통계 조회
    """
    try:
        service = IssueResponseService(db)
        stats = service.get_statistics(coupang_account_id)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{issue_id}")
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 문제 상세 조회
    """
    try:
        service = IssueResponseService(db)
        issue = service.get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail=f"Issue not found: {issue_id}")
        return {
            "success": True,
            "data": issue
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{issue_id}/status")
def update_status(
    issue_id: int,
    request: UpdateStatusRequest,
    db: Session = Depends(get_db)
):
    """
    문제 상태 업데이트

    - status: draft (초안), copied (복사됨), resolved (해결됨)
    """
    try:
        service = IssueResponseService(db)
        result = service.update_issue_status(
            issue_id=issue_id,
            status=request.status,
            resolution_notes=request.resolution_notes
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"Issue not found: {issue_id}")
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{issue_id}")
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db)
):
    """
    문제 삭제
    """
    try:
        service = IssueResponseService(db)
        success = service.delete_issue(issue_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Issue not found: {issue_id}")
        return {
            "success": True,
            "message": f"Issue {issue_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
