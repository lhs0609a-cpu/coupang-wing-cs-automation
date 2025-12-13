"""
Inquiries API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
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
    inquiry_type: str = "online"
    status_filter: Optional[str] = "WAITING"


@router.post("/collect")
def collect_inquiries(
    request: CollectInquiriesRequest,
    db: Session = Depends(get_db)
):
    """Collect new inquiries from Coupang Wing"""
    try:
        collector = InquiryCollector(db)
        inquiries = collector.collect_new_inquiries(
            inquiry_type=request.inquiry_type,
            status_filter=request.status_filter
        )

        return {
            "success": True,
            "count": len(inquiries),
            "inquiries": [{"id": inq.id, "coupang_inquiry_id": inq.coupang_inquiry_id} for inq in inquiries]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=InquiryStatsResponse)
def get_inquiry_stats(db: Session = Depends(get_db)):
    """Get inquiry statistics"""
    collector = InquiryCollector(db)
    stats = collector.get_inquiry_stats()
    return stats


@router.get("/pending", response_model=List[InquiryResponse])
def get_pending_inquiries(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get pending inquiries"""
    collector = InquiryCollector(db)
    inquiries = collector.get_pending_inquiries(limit=limit)
    return inquiries


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{inquiry_id}/flag-human")
def flag_for_human(
    inquiry_id: int,
    reason: str = "",
    db: Session = Depends(get_db)
):
    """Flag inquiry for human review"""
    collector = InquiryCollector(db)

    try:
        collector.flag_for_human_review(inquiry_id, reason)
        return {"success": True, "message": "Inquiry flagged for human review"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
