"""
Inquiries API Router
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..exceptions import NotFoundError, ValidationError as AppValidationError, APIError, DatabaseError

logger = logging.getLogger(__name__)
from ..models import Inquiry
from ..services import InquiryCollector, InquiryAnalyzer

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


# Pydantic schemas
class InquiryResponse(BaseModel):
    id: int
    coupang_inquiry_id: str
    customer_name: Optional[str]
    order_number: Optional[str]
    product_name: Optional[str]
    inquiry_text: str
    classified_category: Optional[str]
    confidence_score: Optional[float]
    risk_level: Optional[str]
    status: str
    requires_human: bool
    is_urgent: bool

    class Config:
        from_attributes = True


class InquiryStatsResponse(BaseModel):
    total: int
    pending: int
    processing: int
    processed: int
    failed: int
    requires_human: int
    urgent: int


class CollectInquiriesRequest(BaseModel):
    account_id: Optional[int] = None
    inquiry_type: str = "online"
    status_filter: Optional[str] = "WAITING"


class ManualInquiryGenerateRequest(BaseModel):
    account_id: Optional[int] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    order_number: Optional[str] = None
    inquiry_text: str


class ManualInquirySubmitRequest(BaseModel):
    account_id: Optional[int] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    order_number: Optional[str] = None
    inquiry_text: str
    response_text: str
    confidence_score: Optional[float] = None


@router.post("/collect")
def collect_inquiries(
    request: CollectInquiriesRequest,
    db: Session = Depends(get_db)
):
    """Collect new inquiries from Coupang Wing"""
    try:
        collector = InquiryCollector(db)
        inquiries = collector.collect_new_inquiries(
            account_id=request.account_id,
            inquiry_type=request.inquiry_type,
            status_filter=request.status_filter
        )

        return {
            "success": True,
            "count": len(inquiries),
            "inquiries": [{"id": inq.id, "coupang_inquiry_id": inq.coupang_inquiry_id} for inq in inquiries]
        }
    except AppValidationError as e:
        logger.warning(f"Invalid request for collect inquiries: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except APIError as e:
        logger.error(f"API error collecting inquiries: {e.message}")
        raise HTTPException(status_code=502, detail=e.message)
    except DatabaseError as e:
        logger.error(f"Database error collecting inquiries: {e.message}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Failed to collect inquiries: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect inquiries from Coupang")


@router.get("/stats", response_model=InquiryStatsResponse)
def get_inquiry_stats(db: Session = Depends(get_db)):
    """Get inquiry statistics"""
    try:
        collector = InquiryCollector(db)
        stats = collector.get_inquiry_stats()
        return stats
    except DatabaseError as e:
        logger.error(f"Database error getting inquiry stats: {e.message}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Failed to get inquiry stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve inquiry statistics")


@router.get("/pending", response_model=List[InquiryResponse])
def get_pending_inquiries(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get pending inquiries"""
    try:
        collector = InquiryCollector(db)
        inquiries = collector.get_pending_inquiries(limit=limit)
        return inquiries
    except AppValidationError as e:
        logger.warning(f"Invalid request for pending inquiries: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseError as e:
        logger.error(f"Database error getting pending inquiries: {e.message}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Failed to get pending inquiries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending inquiries")


@router.get("/{inquiry_id}", response_model=InquiryResponse)
def get_inquiry(inquiry_id: int, db: Session = Depends(get_db)):
    """Get inquiry by ID"""
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return inquiry


@router.post("/{inquiry_id}/analyze")
def analyze_inquiry(inquiry_id: int, db: Session = Depends(get_db)):
    """Analyze an inquiry"""
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    try:
        analyzer = InquiryAnalyzer(db)
        result = analyzer.analyze_inquiry(inquiry)
        return {"success": True, "analysis": result}
    except AppValidationError as e:
        logger.warning(f"Invalid inquiry for analysis (id={inquiry_id}): {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseError as e:
        logger.error(f"Database error analyzing inquiry (id={inquiry_id}): {e.message}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Failed to analyze inquiry (id={inquiry_id}): {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze inquiry")


@router.post("/{inquiry_id}/flag-human")
def flag_for_human(
    inquiry_id: int,
    reason: str = "",
    db: Session = Depends(get_db)
):
    """Flag inquiry for human review"""
    try:
        collector = InquiryCollector(db)
        collector.flag_for_human_review(inquiry_id, reason)
        return {"success": True, "message": "Inquiry flagged for human review"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        logger.error(f"Database error flagging inquiry (id={inquiry_id}): {e.message}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Failed to flag inquiry for human review (id={inquiry_id}): {e}")
        raise HTTPException(status_code=500, detail="Failed to flag inquiry for human review")


@router.post("/manual/generate")
def generate_manual_response(
    request: ManualInquiryGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate AI response for manually entered inquiry"""
    if not request.inquiry_text or not request.inquiry_text.strip():
        raise HTTPException(status_code=400, detail="Inquiry text is required")

    try:
        analyzer = InquiryAnalyzer(db)

        # 임시 Inquiry 객체 생성 (DB에 저장하지 않음)
        temp_inquiry = Inquiry(
            coupang_inquiry_id=f"manual_{int(__import__('time').time())}",
            customer_name=request.customer_name,
            product_name=request.product_name,
            order_number=request.order_number,
            inquiry_text=request.inquiry_text,
            status="manual"
        )

        # AI 분석 및 답변 생성
        result = analyzer.analyze_and_generate_response(temp_inquiry)

        return {
            "success": True,
            "response_text": result.get("response_text", ""),
            "confidence_score": result.get("confidence_score", 85.0),
            "category": result.get("category", "general"),
            "risk_level": result.get("risk_level", "low")
        }
    except AppValidationError as e:
        logger.warning(f"Invalid manual inquiry request: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except APIError as e:
        logger.error(f"API error generating manual response: {e.message}")
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to generate manual response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")


@router.post("/manual/submit")
def submit_manual_response(
    request: ManualInquirySubmitRequest,
    db: Session = Depends(get_db)
):
    """Save manually created inquiry and response"""
    from ..models import Response
    from datetime import datetime
    from sqlalchemy.exc import SQLAlchemyError

    # Validate required fields
    if not request.inquiry_text or not request.inquiry_text.strip():
        raise HTTPException(status_code=400, detail="Inquiry text is required")
    if not request.response_text or not request.response_text.strip():
        raise HTTPException(status_code=400, detail="Response text is required")

    try:
        # 문의 저장
        inquiry = Inquiry(
            coupang_inquiry_id=f"manual_{int(__import__('time').time())}",
            customer_name=request.customer_name,
            product_name=request.product_name,
            order_number=request.order_number,
            inquiry_text=request.inquiry_text,
            status="processed",
            classified_category="manual",
            requires_human=False,
            is_urgent=False
        )
        db.add(inquiry)
        db.flush()

        # 응답 저장
        response = Response(
            inquiry_id=inquiry.id,
            response_text=request.response_text,
            confidence_score=request.confidence_score or 85.0,
            status="submitted",
            approved_by="manual",
            approved_at=datetime.utcnow(),
            submitted_at=datetime.utcnow()
        )
        db.add(response)
        db.commit()

        logger.info(f"Manual inquiry submitted: inquiry_id={inquiry.id}, response_id={response.id}")
        return {
            "success": True,
            "inquiry_id": inquiry.id,
            "response_id": response.id,
            "message": "Manual inquiry and response saved successfully"
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error submitting manual response: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit manual response: {e}")
        raise HTTPException(status_code=500, detail="Failed to save manual inquiry and response")
