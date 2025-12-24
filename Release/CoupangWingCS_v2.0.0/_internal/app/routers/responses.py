"""
Responses API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import Inquiry, Response
from ..services import (
    ResponseGenerator,
    ResponseValidator,
    ResponseSubmitter
)

router = APIRouter(prefix="/responses", tags=["responses"])


# Pydantic schemas
class ResponseSchema(BaseModel):
    id: int
    inquiry_id: int
    response_text: str
    confidence_score: Optional[float]
    risk_level: Optional[str]
    status: str
    validation_passed: bool
    approved_by: Optional[str]
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True


class GenerateResponseRequest(BaseModel):
    inquiry_id: int
    method: str = "template"  # template, ai, hybrid


class ApproveResponseRequest(BaseModel):
    approved_by: str
    edited_text: Optional[str] = None


class SubmitResponseRequest(BaseModel):
    submitted_by: str = "system"


@router.post("/generate")
def generate_response(
    request: GenerateResponseRequest,
    db: Session = Depends(get_db)
):
    """Generate response for an inquiry"""
    inquiry = db.query(Inquiry).filter(Inquiry.id == request.inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    try:
        generator = ResponseGenerator(db)
        response = generator.generate_response(inquiry, method=request.method)

        if not response:
            return {"success": False, "error": "Failed to generate response"}

        # Validate response
        validator = ResponseValidator(db)
        validation_result = validator.validate_response(response, inquiry)

        return {
            "success": True,
            "response_id": response.id,
            "response_text": response.response_text,
            "validation": validation_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending-approval", response_model=List[ResponseSchema])
def get_pending_approval(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get responses pending approval"""
    responses = db.query(Response).filter(
        Response.status.in_(["pending_approval", "draft"])
    ).order_by(
        Response.confidence_score.desc()
    ).limit(limit).all()

    return responses


@router.get("/{response_id}", response_model=ResponseSchema)
def get_response(response_id: int, db: Session = Depends(get_db)):
    """Get response by ID"""
    response = db.query(Response).filter(Response.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response


@router.get("/{response_id}/validation")
def get_validation_summary(response_id: int, db: Session = Depends(get_db)):
    """Get validation summary for a response"""
    validator = ResponseValidator(db)
    summary = validator.get_validation_summary(response_id)

    if not summary:
        raise HTTPException(status_code=404, detail="Response not found")

    return summary


@router.post("/{response_id}/approve")
def approve_response(
    response_id: int,
    request: ApproveResponseRequest,
    db: Session = Depends(get_db)
):
    """Approve a response"""
    response = db.query(Response).filter(Response.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    try:
        # If edited, update response text
        if request.edited_text:
            response.response_text = request.edited_text
            response.edit_count = (response.edit_count or 0) + 1

            # Re-validate edited response
            validator = ResponseValidator(db)
            validator.validate_response(response)

        # Approve
        response.status = "approved"
        response.approved_by = request.approved_by
        response.approved_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "response_id": response.id,
            "status": response.status
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{response_id}/reject")
def reject_response(
    response_id: int,
    reason: str = "",
    db: Session = Depends(get_db)
):
    """Reject a response"""
    response = db.query(Response).filter(Response.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    try:
        response.status = "rejected"
        response.rejection_reason = reason
        db.commit()

        return {
            "success": True,
            "response_id": response.id,
            "status": response.status
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{response_id}/submit")
def submit_response(
    response_id: int,
    request: SubmitResponseRequest,
    db: Session = Depends(get_db)
):
    """Submit an approved response to Coupang Wing"""
    try:
        submitter = ResponseSubmitter(db)
        result = submitter.submit_response(response_id, request.submitted_by)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit-bulk")
def submit_bulk(limit: int = 10, db: Session = Depends(get_db)):
    """Submit multiple approved responses"""
    try:
        submitter = ResponseSubmitter(db)
        result = submitter.bulk_submit_approved(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/submission")
def get_submission_stats(db: Session = Depends(get_db)):
    """Get submission statistics"""
    submitter = ResponseSubmitter(db)
    stats = submitter.get_submission_stats()
    return stats
