"""
Batch Job Progress Tracker
배치 작업 진행률 추적 시스템
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from loguru import logger
import uuid


class BatchStatus(str, Enum):
    """배치 작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """배치 작업 정보"""
    job_id: str
    job_type: str
    status: BatchStatus
    total_items: int
    processed_items: int
    failed_items: int
    skipped_items: int
    progress_percent: float
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['started_at'] = self.started_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


class BatchJobTracker:
    """
    배치 작업 추적기
    """

    def __init__(self):
        self.jobs: Dict[str, BatchJob] = {}
        self.job_results: Dict[str, List[Dict]] = {}  # Store detailed results

    def create_job(
        self,
        job_type: str,
        total_items: int,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new batch job

        Args:
            job_type: Type of batch job (e.g., "bulk_approve", "csv_import")
            total_items: Total number of items to process
            metadata: Additional metadata

        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())

        job = BatchJob(
            job_id=job_id,
            job_type=job_type,
            status=BatchStatus.PENDING,
            total_items=total_items,
            processed_items=0,
            failed_items=0,
            skipped_items=0,
            progress_percent=0.0,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {}
        )

        self.jobs[job_id] = job
        self.job_results[job_id] = []

        logger.info(f"Created batch job {job_id}: {job_type} ({total_items} items)")
        return job_id

    def start_job(self, job_id: str):
        """Start a batch job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]
        job.status = BatchStatus.RUNNING
        job.updated_at = datetime.utcnow()

        logger.info(f"Started batch job {job_id}")

    def update_progress(
        self,
        job_id: str,
        processed: int = 0,
        failed: int = 0,
        skipped: int = 0
    ):
        """
        Update job progress

        Args:
            job_id: Job identifier
            processed: Number of successfully processed items
            failed: Number of failed items
            skipped: Number of skipped items
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        if processed > 0:
            job.processed_items += processed
        if failed > 0:
            job.failed_items += failed
        if skipped > 0:
            job.skipped_items += skipped

        # Calculate progress
        total_processed = job.processed_items + job.failed_items + job.skipped_items
        job.progress_percent = min(
            (total_processed / job.total_items * 100) if job.total_items > 0 else 100,
            100.0
        )

        job.updated_at = datetime.utcnow()

        logger.debug(
            f"Job {job_id} progress: {job.progress_percent:.1f}% "
            f"({total_processed}/{job.total_items})"
        )

    def add_result(
        self,
        job_id: str,
        item_id: Any,
        success: bool,
        message: str = "",
        details: Optional[Dict] = None
    ):
        """
        Add individual item result

        Args:
            job_id: Job identifier
            item_id: Item identifier
            success: Whether processing succeeded
            message: Result message
            details: Additional details
        """
        if job_id not in self.job_results:
            self.job_results[job_id] = []

        result = {
            "item_id": item_id,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        self.job_results[job_id].append(result)

        # Update progress
        if success:
            self.update_progress(job_id, processed=1)
        else:
            self.update_progress(job_id, failed=1)

    def complete_job(self, job_id: str, error: Optional[str] = None):
        """
        Mark job as completed or failed

        Args:
            job_id: Job identifier
            error: Error message if job failed
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        if error:
            job.status = BatchStatus.FAILED
            job.error_message = error
            logger.error(f"Batch job {job_id} failed: {error}")
        else:
            job.status = BatchStatus.COMPLETED
            logger.success(
                f"Batch job {job_id} completed: "
                f"{job.processed_items} processed, {job.failed_items} failed"
            )

        job.completed_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        job.progress_percent = 100.0

    def pause_job(self, job_id: str):
        """Pause a running job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        if job.status != BatchStatus.RUNNING:
            raise ValueError(f"Job {job_id} is not running")

        job.status = BatchStatus.PAUSED
        job.updated_at = datetime.utcnow()

        logger.info(f"Paused batch job {job_id}")

    def resume_job(self, job_id: str):
        """Resume a paused job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        if job.status != BatchStatus.PAUSED:
            raise ValueError(f"Job {job_id} is not paused")

        job.status = BatchStatus.RUNNING
        job.updated_at = datetime.utcnow()

        logger.info(f"Resumed batch job {job_id}")

    def cancel_job(self, job_id: str):
        """Cancel a job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]
        job.status = BatchStatus.CANCELLED
        job.updated_at = datetime.utcnow()
        job.completed_at = datetime.utcnow()

        logger.info(f"Cancelled batch job {job_id}")

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job details"""
        return self.jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Dict:
        """Get job status with details"""
        job = self.get_job(job_id)

        if not job:
            return {"error": "Job not found"}

        # Calculate statistics
        success_items = job.processed_items
        total_completed = job.processed_items + job.failed_items + job.skipped_items
        remaining = max(job.total_items - total_completed, 0)

        # Estimate time remaining
        eta_seconds = None
        if job.status == BatchStatus.RUNNING and total_completed > 0:
            elapsed = (datetime.utcnow() - job.started_at).total_seconds()
            rate = total_completed / elapsed if elapsed > 0 else 0
            if rate > 0 and remaining > 0:
                eta_seconds = int(remaining / rate)

        return {
            **job.to_dict(),
            "statistics": {
                "success_count": success_items,
                "failed_count": job.failed_items,
                "skipped_count": job.skipped_items,
                "remaining_count": remaining,
                "success_rate": round(
                    success_items / total_completed, 4
                ) if total_completed > 0 else 0
            },
            "timing": {
                "elapsed_seconds": (
                    datetime.utcnow() - job.started_at
                ).total_seconds() if job.started_at else 0,
                "eta_seconds": eta_seconds,
                "eta_formatted": self._format_duration(eta_seconds) if eta_seconds else None
            }
        }

    def get_job_results(
        self,
        job_id: str,
        failed_only: bool = False,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get detailed job results

        Args:
            job_id: Job identifier
            failed_only: Return only failed items
            limit: Maximum number of results to return

        Returns:
            List of item results
        """
        if job_id not in self.job_results:
            return []

        results = self.job_results[job_id]

        if failed_only:
            results = [r for r in results if not r['success']]

        return results[-limit:]

    def list_jobs(
        self,
        status: Optional[BatchStatus] = None,
        job_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List batch jobs with filters

        Args:
            status: Filter by status
            job_type: Filter by job type
            limit: Maximum number of jobs to return

        Returns:
            List of job summaries
        """
        jobs = list(self.jobs.values())

        # Apply filters
        if status:
            jobs = [j for j in jobs if j.status == status]

        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]

        # Sort by most recent
        jobs.sort(key=lambda j: j.updated_at, reverse=True)

        # Limit
        jobs = jobs[:limit]

        return [j.to_dict() for j in jobs]

    def cleanup_old_jobs(self, days: int = 7):
        """
        Clean up completed jobs older than N days

        Args:
            days: Number of days to keep completed jobs

        Returns:
            Number of jobs cleaned up
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        jobs_to_delete = []

        for job_id, job in self.jobs.items():
            if job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]:
                if job.completed_at and job.completed_at < cutoff:
                    jobs_to_delete.append(job_id)

        for job_id in jobs_to_delete:
            del self.jobs[job_id]
            if job_id in self.job_results:
                del self.job_results[job_id]

        if jobs_to_delete:
            logger.info(f"Cleaned up {len(jobs_to_delete)} old batch jobs")

        return len(jobs_to_delete)

    def _format_duration(self, seconds: Optional[int]) -> Optional[str]:
        """Format duration in human-readable format"""
        if seconds is None:
            return None

        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


# Global tracker instance
_tracker: Optional[BatchJobTracker] = None


def get_batch_tracker() -> BatchJobTracker:
    """Get global batch tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = BatchJobTracker()
    return _tracker
