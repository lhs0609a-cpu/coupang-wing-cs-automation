"""
Automation Execution Log model - tracks automation runs and their results
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from datetime import datetime
from ..database import Base


class AutomationExecutionLog(Base):
    __tablename__ = "automation_execution_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Execution Details
    execution_type = Column(String(50), nullable=False)  # "auto_answer_v2", "test_login", etc.
    status = Column(String(20), nullable=False, index=True)  # "success", "failed", "partial"

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Automation Settings
    username = Column(String(100), nullable=True)
    headless_mode = Column(Boolean, default=False)

    # Statistics
    total_inquiries = Column(Integer, default=0)
    answered = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)

    # Details
    details = Column(JSON, nullable=True)  # Detailed information about the run
    error_message = Column(Text, nullable=True)

    # Metadata
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<AutomationExecutionLog {self.id}: {self.execution_type} - {self.status}>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "execution_type": self.execution_type,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "username": self.username,
            "headless_mode": self.headless_mode,
            "statistics": {
                "total_inquiries": self.total_inquiries,
                "answered": self.answered,
                "failed": self.failed,
                "skipped": self.skipped
            },
            "details": self.details,
            "error_message": self.error_message
        }
