"""
Advanced Features API Router
Includes: Learning, Customer History, Templates, Performance, Backup
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from ..database import get_db
from ..models import Inquiry, Response
from ..services.learning import LearningService
from ..services.customer_history import CustomerHistoryService
from ..services.template_manager import TemplateManager
from ..services.performance import PerformanceMonitor
from ..services.backup import BackupService
from ..services.reporting import ReportingService
from ..scheduler import get_scheduler

router = APIRouter(prefix="/advanced", tags=["Advanced Features"])

# Pydantic models
class FeedbackRequest(BaseModel):
    response_id: int
    edited_text: str
    edited_by: str
    edit_reason: Optional[str] = None
    quality_score: Optional[float] = None


class TemplateRequest(BaseModel):
    name: str
    content: str


class BackupRequest(BaseModel):
    include_files: bool = True


# ===== Learning Endpoints =====

@router.post("/learning/feedback")
def record_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """Record feedback for learning"""
    try:
        service = LearningService(db)
        feedback = service.record_feedback(
            response_id=request.response_id,
            edited_text=request.edited_text,
            edited_by=request.edited_by,
            edit_reason=request.edit_reason,
            quality_score=request.quality_score
        )
        return {
            "success": True,
            "feedback_id": feedback.id,
            "improvement_category": feedback.improvement_category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/insights")
def get_learning_insights(days: int = 30, db: Session = Depends(get_db)):
    """Get learning insights"""
    service = LearningService(db)
    return service.get_learning_insights(days)


@router.get("/learning/prompt-suggestions")
def get_prompt_suggestions(db: Session = Depends(get_db)):
    """Get AI prompt improvement suggestions"""
    service = LearningService(db)
    return service.suggest_prompt_improvements()


@router.get("/learning/export-training-data")
def export_training_data(min_quality: float = 4.0, db: Session = Depends(get_db)):
    """Export training data for fine-tuning"""
    service = LearningService(db)
    return {
        "training_data": service.export_training_data(min_quality)
    }


# ===== Customer History Endpoints =====

@router.get("/customers/{customer_id}/history")
def get_customer_history(customer_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Get customer history"""
    service = CustomerHistoryService(db)
    return service.get_customer_history(customer_id, limit)


@router.get("/customers/{customer_id}/patterns")
def get_customer_patterns(customer_id: str, db: Session = Depends(get_db)):
    """Analyze customer patterns"""
    service = CustomerHistoryService(db)
    return service.analyze_customer_patterns(customer_id)


@router.get("/customers/{customer_id}/recommendations")
def get_recommendations(customer_id: str, db: Session = Depends(get_db)):
    """Get recommendations for handling customer"""
    # Get latest inquiry for this customer
    inquiry = db.query(Inquiry).filter(
        Inquiry.customer_id == customer_id
    ).order_by(Inquiry.created_at.desc()).first()

    if not inquiry:
        return {"recommendations": [], "message": "No inquiries found"}

    service = CustomerHistoryService(db)
    return service.get_recommendations_for_inquiry(inquiry)


@router.get("/customers/vip/identify")
def identify_vip_customers(
    min_orders: int = 10,
    min_satisfaction: float = 4.5,
    db: Session = Depends(get_db)
):
    """Identify VIP customers"""
    service = CustomerHistoryService(db)
    vips = service.identify_vip_customers(min_orders, min_satisfaction)
    return {
        "count": len(vips),
        "customers": [
            {
                "customer_id": vip.customer_id,
                "customer_name": vip.customer_name,
                "total_inquiries": vip.total_inquiries
            }
            for vip in vips
        ]
    }


# ===== Template Management Endpoints =====

@router.get("/templates")
def list_templates():
    """List all templates"""
    manager = TemplateManager()
    return {"templates": manager.list_templates()}


@router.get("/templates/{template_name}")
def get_template(template_name: str):
    """Get template content"""
    manager = TemplateManager()
    content = manager.get_template(template_name)

    if content is None:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"name": template_name, "content": content}


@router.post("/templates")
def create_template(request: TemplateRequest):
    """Create new template"""
    manager = TemplateManager()
    success = manager.create_template(request.name, request.content)

    if not success:
        raise HTTPException(status_code=400, detail="Template already exists or creation failed")

    return {"success": True, "name": request.name}


@router.put("/templates/{template_name}")
def update_template(template_name: str, request: TemplateRequest):
    """Update template"""
    manager = TemplateManager()
    success = manager.update_template(template_name, request.content)

    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"success": True, "name": template_name}


@router.delete("/templates/{template_name}")
def delete_template(template_name: str):
    """Delete template"""
    manager = TemplateManager()
    success = manager.delete_template(template_name)

    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"success": True, "name": template_name}


# ===== Performance Monitoring Endpoints =====

@router.get("/performance/system")
def get_system_stats():
    """Get system performance stats"""
    monitor = PerformanceMonitor()
    return monitor.get_system_stats()


@router.get("/performance/report")
def get_performance_report():
    """Get performance report"""
    monitor = PerformanceMonitor()
    return monitor.get_performance_report()


# ===== Backup/Restore Endpoints =====

@router.post("/backup/create")
def create_backup(request: BackupRequest):
    """Create backup"""
    service = BackupService()
    return service.create_backup(request.include_files)


@router.get("/backup/list")
def list_backups():
    """List all backups"""
    service = BackupService()
    return {"backups": service.list_backups()}


@router.post("/backup/{backup_name}/restore")
def restore_backup(backup_name: str):
    """Restore from backup"""
    service = BackupService()
    return service.restore_backup(backup_name)


@router.delete("/backup/{backup_name}")
def delete_backup(backup_name: str):
    """Delete backup"""
    service = BackupService()
    success = service.delete_backup(backup_name)

    if not success:
        raise HTTPException(status_code=404, detail="Backup not found")

    return {"success": True, "backup_name": backup_name}


# ===== Scheduler Endpoints =====

@router.post("/scheduler/start")
def start_scheduler():
    """Start automation scheduler"""
    scheduler = get_scheduler()
    scheduler.start()
    return {"success": True, "message": "Scheduler started"}


@router.post("/scheduler/stop")
def stop_scheduler():
    """Stop automation scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()
    return {"success": True, "message": "Scheduler stopped"}


@router.get("/scheduler/status")
def get_scheduler_status():
    """Get scheduler status"""
    scheduler = get_scheduler()
    return scheduler.get_job_status()


# ===== Reporting Endpoints =====

@router.get("/reports/daily")
def get_daily_report(days_ago: int = 0, db: Session = Depends(get_db)):
    """Get daily report"""
    from datetime import datetime, timedelta
    date = datetime.utcnow() - timedelta(days=days_ago)

    service = ReportingService(db)
    return service.generate_daily_report(date)


@router.get("/reports/weekly")
def get_weekly_report(weeks_ago: int = 0, db: Session = Depends(get_db)):
    """Get weekly report"""
    service = ReportingService(db)
    return service.generate_weekly_report(weeks_ago)


@router.get("/reports/monthly")
def get_monthly_report(months_ago: int = 0, db: Session = Depends(get_db)):
    """Get monthly report"""
    service = ReportingService(db)
    return service.generate_monthly_report(months_ago)


@router.get("/reports/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """Get real-time dashboard"""
    service = ReportingService(db)
    return service.get_real_time_dashboard()
