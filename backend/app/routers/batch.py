"""
Batch Job Tracking API Router
배치 작업 추적 API 라우터
"""
from fastapi import APIRouter, Query, Body
from typing import Optional, List, Dict

from ..services.batch_tracker import get_batch_tracker, BatchStatus

router = APIRouter(prefix="/batch", tags=["Batch Jobs"])


@router.get("/jobs")
def list_batch_jobs(
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """
    배치 작업 목록 조회

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)
        job_type: Filter by job type
        limit: Maximum number of jobs to return
    """
    tracker = get_batch_tracker()

    status_enum = None
    if status:
        try:
            status_enum = BatchStatus(status.lower())
        except ValueError:
            pass

    jobs = tracker.list_jobs(
        status=status_enum,
        job_type=job_type,
        limit=limit
    )

    return {
        "jobs": jobs,
        "count": len(jobs)
    }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    배치 작업 상태 조회

    실시간 진행률 및 상세 정보 반환
    """
    tracker = get_batch_tracker()
    status = tracker.get_job_status(job_id)

    if "error" in status:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")

    return status


@router.get("/jobs/{job_id}/results")
def get_job_results(
    job_id: str,
    failed_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    배치 작업 상세 결과 조회

    Args:
        job_id: Job identifier
        failed_only: Return only failed items
        limit: Maximum number of results
    """
    tracker = get_batch_tracker()
    results = tracker.get_job_results(job_id, failed_only, limit)

    return {
        "job_id": job_id,
        "results": results,
        "count": len(results),
        "failed_only": failed_only
    }


@router.post("/jobs/{job_id}/pause")
def pause_job(job_id: str):
    """배치 작업 일시정지"""
    tracker = get_batch_tracker()

    try:
        tracker.pause_job(job_id)
        return {"success": True, "message": "Job paused"}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/resume")
def resume_job(job_id: str):
    """배치 작업 재개"""
    tracker = get_batch_tracker()

    try:
        tracker.resume_job(job_id)
        return {"success": True, "message": "Job resumed"}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """배치 작업 취소"""
    tracker = get_batch_tracker()

    try:
        tracker.cancel_job(job_id)
        return {"success": True, "message": "Job cancelled"}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
def get_batch_stats():
    """
    전체 배치 작업 통계
    """
    tracker = get_batch_tracker()

    # Count by status
    status_counts = {}
    for status in BatchStatus:
        jobs = tracker.list_jobs(status=status, limit=1000)
        status_counts[status.value] = len(jobs)

    # Total jobs
    all_jobs = tracker.list_jobs(limit=1000)

    return {
        "total_jobs": len(all_jobs),
        "by_status": status_counts,
        "recent_jobs": tracker.list_jobs(limit=10)
    }


@router.post("/cleanup")
def cleanup_old_jobs(days: int = Body(7, ge=1, le=365, embed=True)):
    """
    오래된 완료/실패 작업 정리

    Args:
        days: Keep jobs from the last N days
    """
    tracker = get_batch_tracker()
    cleaned = tracker.cleanup_old_jobs(days)

    return {
        "success": True,
        "cleaned_count": cleaned,
        "message": f"Cleaned up {cleaned} old jobs (older than {days} days)"
    }


@router.post("/test/create-sample-job")
def create_sample_job(
    job_type: str = Body("test_job"),
    total_items: int = Body(100, ge=1, le=10000)
):
    """
    테스트용 샘플 작업 생성
    """
    tracker = get_batch_tracker()

    job_id = tracker.create_job(
        job_type=job_type,
        total_items=total_items,
        metadata={"test": True}
    )

    tracker.start_job(job_id)

    # Simulate some progress
    tracker.update_progress(job_id, processed=10)

    return {
        "job_id": job_id,
        "message": "Sample job created",
        "status_url": f"/api/batch/jobs/{job_id}"
    }
