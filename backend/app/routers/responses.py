"""
Responses API Router
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import Inquiry, Response
from ..exceptions import NotFoundError, ValidationError as AppValidationError, APIError, DatabaseError
from ..services import (
    ResponseGenerator,
    ResponseValidator,
    ResponseSubmitter
)

logger = logging.getLogger(__name__)

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
    # Validate method
    valid_methods = ["template", "ai", "hybrid"]
    if request.method not in valid_methods:
        raise HTTPException(status_code=400, detail=f"Invalid method. Must be one of: {valid_methods}")

    try:
        inquiry = db.query(Inquiry).filter(Inquiry.id == request.inquiry_id).first()
        if not inquiry:
            raise HTTPException(status_code=404, detail="Inquiry not found")

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
    except HTTPException:
        raise
    except APIError as e:
        logger.error(f"API error generating response: {e.message}")
        raise HTTPException(status_code=502, detail=e.message)
    except SQLAlchemyError as e:
        logger.error(f"Database error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate response")


@router.get("/pending-approval", response_model=List[ResponseSchema])
def get_pending_approval(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get responses pending approval"""
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 500")

    try:
        responses = db.query(Response).filter(
            Response.status.in_(["pending_approval", "draft"])
        ).order_by(
            Response.confidence_score.desc()
        ).limit(limit).all()

        return responses
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching pending approvals: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")


# Response history schemas
class ResponseWithInquirySchema(BaseModel):
    id: int
    inquiry_id: int
    response_text: str
    confidence_score: Optional[float]
    risk_level: Optional[str]
    status: str
    validation_passed: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    submitted_at: Optional[datetime]
    created_at: datetime
    inquiry_text: Optional[str]
    customer_name: Optional[str]
    product_name: Optional[str]
    order_number: Optional[str]
    inquiry_type: Optional[str]

    class Config:
        from_attributes = True


@router.get("/history", response_model=List[ResponseWithInquirySchema])
def get_response_history(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get response history with inquiry details"""
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 500")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    try:
        query = db.query(Response).join(Inquiry, Response.inquiry_id == Inquiry.id, isouter=True)

        # Apply status filter if provided
        if status_filter and status_filter != 'all':
            query = query.filter(Response.status == status_filter)

        # Order by most recent first
        responses = query.order_by(Response.created_at.desc()).offset(offset).limit(limit).all()

        # Build response with inquiry details
        result = []
        for response in responses:
            inquiry = response.inquiry
            result.append({
                "id": response.id,
                "inquiry_id": response.inquiry_id,
                "response_text": response.response_text,
                "confidence_score": response.confidence_score,
                "risk_level": response.risk_level,
                "status": response.status,
                "validation_passed": response.validation_passed,
                "approved_by": response.approved_by,
                "approved_at": response.approved_at,
                "submitted_at": response.submitted_at,
                "created_at": response.created_at,
                "inquiry_text": inquiry.inquiry_text if inquiry else None,
                "customer_name": inquiry.customer_name if inquiry else None,
                "product_name": inquiry.product_name if inquiry else None,
                "order_number": inquiry.order_number if inquiry else None,
                "inquiry_type": getattr(inquiry, 'inquiry_type', None) if inquiry else None,
            })

        return result
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching response history: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")


@router.get("/all", response_model=List[ResponseWithInquirySchema])
def get_all_responses_with_inquiry(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all responses with inquiry details - alias for /history"""
    return get_response_history(limit=limit, offset=offset, status_filter=status_filter, db=db)


@router.get("/{response_id}", response_model=ResponseSchema)
def get_response(response_id: int, db: Session = Depends(get_db)):
    """Get response by ID"""
    try:
        response = db.query(Response).filter(Response.id == response_id).first()
        if not response:
            raise HTTPException(status_code=404, detail="Response not found")
        return response
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching response {response_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")


@router.get("/{response_id}/validation")
def get_validation_summary(response_id: int, db: Session = Depends(get_db)):
    """Get validation summary for a response"""
    try:
        validator = ResponseValidator(db)
        summary = validator.get_validation_summary(response_id)

        if not summary:
            raise HTTPException(status_code=404, detail="Response not found")

        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching validation summary for response {response_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch validation summary")


@router.post("/{response_id}/approve")
def approve_response(
    response_id: int,
    request: ApproveResponseRequest,
    db: Session = Depends(get_db)
):
    """Approve a response"""
    if not request.approved_by or not request.approved_by.strip():
        raise HTTPException(status_code=400, detail="approved_by is required")

    try:
        response = db.query(Response).filter(Response.id == response_id).first()
        if not response:
            raise HTTPException(status_code=404, detail="Response not found")

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

        logger.info(f"Response {response_id} approved by {request.approved_by}")
        return {
            "success": True,
            "response_id": response.id,
            "status": response.status
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error approving response {response_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving response {response_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to approve response")


@router.post("/{response_id}/reject")
def reject_response(
    response_id: int,
    reason: str = "",
    db: Session = Depends(get_db)
):
    """Reject a response"""
    try:
        response = db.query(Response).filter(Response.id == response_id).first()
        if not response:
            raise HTTPException(status_code=404, detail="Response not found")

        response.status = "rejected"
        response.rejection_reason = reason
        db.commit()

        logger.info(f"Response {response_id} rejected. Reason: {reason}")
        return {
            "success": True,
            "response_id": response.id,
            "status": response.status
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error rejecting response {response_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting response {response_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reject response")


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
        logger.info(f"Response {response_id} submitted by {request.submitted_by}")
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except APIError as e:
        logger.error(f"API error submitting response {response_id}: {e.message}")
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        logger.error(f"Error submitting response {response_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit response")


@router.post("/submit-bulk")
def submit_bulk(limit: int = 10, db: Session = Depends(get_db)):
    """Submit multiple approved responses"""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    try:
        submitter = ResponseSubmitter(db)
        result = submitter.bulk_submit_approved(limit=limit)
        logger.info(f"Bulk submit completed: {result}")
        return result
    except APIError as e:
        logger.error(f"API error in bulk submit: {e.message}")
        raise HTTPException(status_code=502, detail=e.message)
    except Exception as e:
        logger.error(f"Error in bulk submit: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit responses")


@router.get("/stats/submission")
def get_submission_stats(db: Session = Depends(get_db)):
    """Get submission statistics"""
    try:
        submitter = ResponseSubmitter(db)
        stats = submitter.get_submission_stats()
        return stats
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching submission stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error fetching submission stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch submission statistics")
