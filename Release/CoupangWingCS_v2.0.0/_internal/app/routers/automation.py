"""
Automation API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..services.auto_workflow import AutoWorkflow

router = APIRouter(prefix="/automation", tags=["automation"])


class AutoWorkflowRequest(BaseModel):
    limit: int = 10
    auto_submit: bool = True


@router.post("/run-full-workflow")
def run_full_workflow(
    request: AutoWorkflowRequest,
    db: Session = Depends(get_db)
):
    """
    Run complete automated workflow:
    1. Collect inquiries
    2. Analyze inquiries
    3. Generate AI responses
    4. Validate responses
    5. Auto-approve if safe
    6. Auto-submit to Coupang (if enabled)
    """
    try:
        workflow = AutoWorkflow(db)
        results = workflow.run_full_auto_workflow(
            limit=request.limit,
            auto_submit=request.auto_submit
        )
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-process-and-submit")
def auto_process_and_submit(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Automatically process and submit responses (convenience endpoint)
    """
    try:
        workflow = AutoWorkflow(db)
        results = workflow.auto_process_and_submit(limit=limit)
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-pending-approvals")
def process_pending_approvals(db: Session = Depends(get_db)):
    """
    Process all pending approvals and auto-approve/submit safe ones
    """
    try:
        workflow = AutoWorkflow(db)
        results = workflow.process_pending_approvals()
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_automation_stats(db: Session = Depends(get_db)):
    """
    Get automation statistics
    """
    try:
        workflow = AutoWorkflow(db)
        stats = workflow.get_workflow_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
