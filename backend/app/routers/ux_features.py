"""
UX Enhancement Features API Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

from ..database import get_db
from ..services.template_recommendation import TemplateRecommendationService
from ..services.sentiment_analysis import SentimentAnalysisService
from ..services.ab_testing import ABTestingService
from ..services.webhook_manager import WebhookManager
from ..services.privacy_mask import PrivacyMaskService
from ..services.security_audit import SecurityAuditService
from ..services.advanced_search import AdvancedSearchService
from ..services.bulk_operations import BulkOperationsService
from ..services.excel_export import ExcelExportService
from ..models import Inquiry, Response

router = APIRouter(prefix="/ux", tags=["UX Features"])


# =====================
# Pydantic Models
# =====================

class TemplateRecommendRequest(BaseModel):
    inquiry_id: int
    limit: int = 5


class SentimentAnalysisRequest(BaseModel):
    text: str


class ABTestRequest(BaseModel):
    name: str
    template_a_id: int
    template_b_id: int
    description: str = ""
    traffic_split: float = 0.5
    duration_days: int = 7


class ABTestOutcomeRequest(BaseModel):
    variant: str
    outcome: str
    response_id: Optional[int] = None


class WebhookRegisterRequest(BaseModel):
    name: str
    url: str
    events: List[str]
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    active: bool = True


class MaskRequest(BaseModel):
    text: str
    mask_types: Optional[List[str]] = None
    custom_masks: Optional[Dict[str, str]] = None


class AuditLogRequest(BaseModel):
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class BulkApproveRequest(BaseModel):
    response_ids: List[int]
    approved_by: str


class BulkRejectRequest(BaseModel):
    response_ids: List[int]
    reason: str = ""


class BulkAssignRequest(BaseModel):
    inquiry_ids: List[int]
    assigned_to: int


class BulkStatusChangeRequest(BaseModel):
    inquiry_ids: List[int]
    new_status: str


# =====================
# Template Recommendation
# =====================

@router.post("/templates/recommend")
def recommend_templates(
    request: TemplateRecommendRequest,
    db: Session = Depends(get_db)
):
    """Get AI-powered template recommendations for an inquiry"""
    service = TemplateRecommendationService(db)

    inquiry = db.query(Inquiry).filter(Inquiry.id == request.inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    recommendations = service.recommend_templates(inquiry, request.limit)
    return {"recommendations": recommendations}


@router.post("/templates/prefill/{template_id}")
def prefill_template(
    template_id: int,
    inquiry_id: int,
    db: Session = Depends(get_db)
):
    """Pre-fill template variables with inquiry data"""
    from ..models import Template

    service = TemplateRecommendationService(db)

    template = db.query(Template).filter(Template.id == template_id).first()
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()

    if not template or not inquiry:
        raise HTTPException(status_code=404, detail="Template or inquiry not found")

    filled_content, fill_status = service.pre_fill_template(template.content, inquiry)

    return {
        "template_id": template_id,
        "filled_content": filled_content,
        "fill_status": fill_status
    }


@router.get("/templates/{template_id}/stats")
def get_template_stats(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get performance statistics for a template"""
    service = TemplateRecommendationService(db)
    stats = service.get_template_performance_stats(template_id)
    return stats


# =====================
# Sentiment Analysis
# =====================

@router.post("/sentiment/analyze")
def analyze_sentiment(request: SentimentAnalysisRequest):
    """Analyze sentiment and emotions in text"""
    service = SentimentAnalysisService(None)
    analysis = service.analyze_inquiry_sentiment(request.text)
    return analysis


@router.get("/sentiment/trends")
def get_sentiment_trends(
    days: int = Query(7, ge=1, le=90),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get sentiment trends over time"""
    service = SentimentAnalysisService(db)
    trends = service.get_sentiment_trends(days, category)
    return trends


@router.get("/sentiment/emotions")
def get_emotion_distribution(
    days: int = Query(7, ge=1, le=90),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get emotion distribution for visualization"""
    service = SentimentAnalysisService(db)
    distribution = service.get_emotion_distribution(days, category)
    return distribution


@router.get("/sentiment/by-category")
def get_sentiment_by_category(db: Session = Depends(get_db)):
    """Get sentiment breakdown by inquiry category"""
    service = SentimentAnalysisService(db)
    category_sentiment = service.get_sentiment_by_category()
    return {"categories": category_sentiment}


@router.get("/sentiment/response-tone")
def get_response_tone_analysis(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Analyze tone effectiveness of responses"""
    service = SentimentAnalysisService(db)
    tone_analysis = service.get_response_tone_analysis(days)
    return tone_analysis


# =====================
# A/B Testing
# =====================

@router.post("/ab-tests")
def create_ab_test(
    request: ABTestRequest,
    db: Session = Depends(get_db)
):
    """Create a new A/B test"""
    service = ABTestingService(db)
    test = service.create_ab_test(
        request.name,
        request.template_a_id,
        request.template_b_id,
        request.description,
        request.traffic_split,
        request.duration_days
    )
    return test


@router.get("/ab-tests")
def list_active_tests(db: Session = Depends(get_db)):
    """List all active A/B tests"""
    service = ABTestingService(db)
    tests = service.get_active_tests()
    return {"tests": tests}


@router.get("/ab-tests/{test_id}")
def get_test_results(test_id: str, db: Session = Depends(get_db)):
    """Get A/B test results with statistical analysis"""
    service = ABTestingService(db)
    results = service.get_test_results(test_id)
    return results


@router.post("/ab-tests/{test_id}/assign")
def assign_variant(test_id: str, db: Session = Depends(get_db)):
    """Assign a user to a test variant"""
    service = ABTestingService(db)
    assignment = service.assign_variant(test_id)
    return assignment


@router.post("/ab-tests/{test_id}/outcome")
def record_outcome(
    test_id: str,
    request: ABTestOutcomeRequest,
    db: Session = Depends(get_db)
):
    """Record outcome for a test variant"""
    service = ABTestingService(db)
    service.record_outcome(test_id, request.variant, request.outcome, request.response_id)
    return {"success": True}


@router.post("/ab-tests/{test_id}/stop")
def stop_test(test_id: str, db: Session = Depends(get_db)):
    """Stop an active A/B test"""
    service = ABTestingService(db)
    results = service.stop_test(test_id)
    return results


@router.post("/ab-tests/compare")
def compare_templates(
    template_ids: List[int] = Body(...),
    days: int = Body(30),
    db: Session = Depends(get_db)
):
    """Compare historical performance of templates"""
    service = ABTestingService(db)
    comparison = service.get_template_performance_comparison(template_ids, days)
    return comparison


# =====================
# Webhooks
# =====================

@router.post("/webhooks")
async def register_webhook(
    request: WebhookRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new webhook"""
    manager = WebhookManager(db)
    webhook = manager.register_webhook(
        request.name,
        request.url,
        request.events,
        request.secret,
        request.headers,
        request.active
    )
    return webhook


@router.get("/webhooks")
def list_webhooks(db: Session = Depends(get_db)):
    """List all registered webhooks"""
    manager = WebhookManager(db)
    webhooks = manager.list_webhooks()
    return {"webhooks": webhooks}


@router.get("/webhooks/{webhook_id}")
def get_webhook(webhook_id: str, db: Session = Depends(get_db)):
    """Get webhook configuration"""
    manager = WebhookManager(db)
    webhook = manager.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.put("/webhooks/{webhook_id}")
def update_webhook(
    webhook_id: str,
    updates: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """Update webhook configuration"""
    manager = WebhookManager(db)
    webhook = manager.update_webhook(webhook_id, updates)
    return webhook


@router.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: str, db: Session = Depends(get_db)):
    """Delete a webhook"""
    manager = WebhookManager(db)
    manager.delete_webhook(webhook_id)
    return {"success": True}


@router.get("/webhooks/{webhook_id}/stats")
def get_webhook_stats(webhook_id: str, db: Session = Depends(get_db)):
    """Get webhook delivery statistics"""
    manager = WebhookManager(db)
    stats = manager.get_webhook_stats(webhook_id)
    return stats


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str, db: Session = Depends(get_db)):
    """Send a test event to a webhook"""
    manager = WebhookManager(db)
    result = await manager.test_webhook(webhook_id)
    return result


# =====================
# Privacy & Masking
# =====================

@router.post("/privacy/mask")
def mask_sensitive_data(request: MaskRequest):
    """Mask sensitive information in text"""
    service = PrivacyMaskService()
    masked_text, report = service.mask_sensitive_data(
        request.text,
        request.mask_types,
        request.custom_masks
    )
    return {
        "masked_text": masked_text,
        "report": report
    }


@router.post("/privacy/detect")
def detect_sensitive_data(text: str = Body(..., embed=True)):
    """Detect sensitive information in text"""
    service = PrivacyMaskService()
    detections = service.detect_sensitive_data(text)
    return {"detections": detections}


@router.post("/privacy/validate")
def validate_masked_text(text: str = Body(..., embed=True)):
    """Validate that text is properly masked"""
    service = PrivacyMaskService()
    validation = service.validate_masked_output(text)
    return validation


@router.post("/privacy/unmask")
def unmask_data(
    masked_text: str = Body(...),
    original_text: str = Body(...),
    user_role: str = Body(...)
):
    """Unmask data based on user permissions"""
    service = PrivacyMaskService()
    unmasked = service.unmask_data(masked_text, original_text, user_role)
    return {"text": unmasked}


# =====================
# Security & Audit
# =====================

@router.post("/audit/log")
def create_audit_log(request: AuditLogRequest, db: Session = Depends(get_db)):
    """Create an audit log entry"""
    service = SecurityAuditService(db)
    log = service.log_action(
        request.user_id,
        request.action,
        request.resource_type,
        request.resource_id,
        request.details,
        request.ip_address,
        request.user_agent
    )
    return {"id": log.id, "timestamp": log.timestamp}


@router.get("/audit/user/{user_id}")
def get_user_activity(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get activity history for a user"""
    service = SecurityAuditService(db)
    activity = service.get_user_activity(user_id, days, limit)
    return {"activity": activity}


@router.get("/audit/resource/{resource_type}/{resource_id}")
def get_resource_history(
    resource_type: str,
    resource_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get audit trail for a specific resource"""
    service = SecurityAuditService(db)
    history = service.get_resource_history(resource_type, resource_id, limit)
    return {"history": history}


@router.get("/audit/suspicious")
def detect_suspicious_activity(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Detect suspicious activity patterns"""
    service = SecurityAuditService(db)
    suspicious = service.detect_suspicious_activity(hours)
    return {"suspicious_activities": suspicious}


@router.get("/audit/dashboard")
def get_security_dashboard(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get security dashboard metrics"""
    service = SecurityAuditService(db)
    dashboard = service.get_security_dashboard(days)
    return dashboard


@router.post("/audit/compliance-report")
def generate_compliance_report(
    start_date: datetime = Body(...),
    end_date: datetime = Body(...),
    db: Session = Depends(get_db)
):
    """Generate compliance audit report"""
    service = SecurityAuditService(db)
    report = service.generate_compliance_report(start_date, end_date)
    return report


@router.post("/audit/search")
def search_audit_logs(
    filters: Dict = Body(...),
    limit: int = Body(100),
    db: Session = Depends(get_db)
):
    """Search audit logs with filters"""
    service = SecurityAuditService(db)
    logs = service.search_audit_logs(filters, limit)
    return {"logs": logs, "count": len(logs)}


# =====================
# Advanced Search
# =====================

@router.post("/search/inquiries")
def advanced_search_inquiries(
    filters: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """Advanced inquiry search with complex filters"""
    service = AdvancedSearchService(db)
    results = service.search_inquiries(filters)

    return {
        "results": [
            {
                "id": inq.id,
                "customer_name": inq.customer_name,
                "inquiry_text": inq.inquiry_text[:200],
                "category": inq.classified_category,
                "status": inq.status,
                "created_at": inq.created_at
            }
            for inq in results
        ],
        "count": len(results)
    }


@router.get("/search/suggestions")
def get_search_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on partial query"""
    service = AdvancedSearchService(db)
    suggestions = service.get_search_suggestions(query, limit)
    return {"suggestions": suggestions}


# =====================
# Bulk Operations
# =====================

@router.post("/bulk/approve-responses")
def bulk_approve_responses(
    request: BulkApproveRequest,
    db: Session = Depends(get_db)
):
    """Approve multiple responses at once"""
    service = BulkOperationsService(db)
    results = service.bulk_approve_responses(request.response_ids, request.approved_by)
    return results


@router.post("/bulk/reject-responses")
def bulk_reject_responses(
    request: BulkRejectRequest,
    db: Session = Depends(get_db)
):
    """Reject multiple responses"""
    service = BulkOperationsService(db)
    results = service.bulk_reject_responses(request.response_ids, request.reason)
    return results


@router.post("/bulk/assign-inquiries")
def bulk_assign_inquiries(
    request: BulkAssignRequest,
    db: Session = Depends(get_db)
):
    """Assign multiple inquiries to a user"""
    service = BulkOperationsService(db)
    results = service.bulk_assign_inquiries(request.inquiry_ids, request.assigned_to)
    return results


@router.post("/bulk/change-status")
def bulk_change_status(
    request: BulkStatusChangeRequest,
    db: Session = Depends(get_db)
):
    """Change status of multiple inquiries"""
    service = BulkOperationsService(db)
    results = service.bulk_change_status(request.inquiry_ids, request.new_status)
    return results


# =====================
# Excel/CSV Export
# =====================

@router.post("/export/inquiries/csv")
def export_inquiries_csv(
    inquiry_ids: Optional[List[int]] = Body(None),
    filters: Optional[Dict] = Body(None),
    db: Session = Depends(get_db)
):
    """Export inquiries to CSV"""
    from fastapi.responses import Response

    service = ExcelExportService(db)
    csv_content = service.export_inquiries_to_csv(inquiry_ids, filters)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=inquiries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.post("/export/responses/csv")
def export_responses_csv(
    response_ids: Optional[List[int]] = Body(None),
    db: Session = Depends(get_db)
):
    """Export responses to CSV"""
    from fastapi.responses import Response

    service = ExcelExportService(db)
    csv_content = service.export_responses_to_csv(response_ids)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.post("/import/inquiries/csv")
def import_inquiries_csv(
    csv_content: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Import inquiries from CSV"""
    service = ExcelExportService(db)
    results = service.import_inquiries_from_csv(csv_content)
    return results
