"""
Activity Log model - tracks all system activities for audit trail
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), nullable=True, index=True)
    response_id = Column(Integer, ForeignKey("responses.id"), nullable=True, index=True)

    # Action Details
    action = Column(String(50), nullable=False, index=True)  # inquiry_created, response_generated, etc.
    action_type = Column(String(50))  # create, update, delete, approve, submit

    # Actor Information
    actor = Column(String(100))  # system, user_id, service_name
    actor_type = Column(String(20))  # system, human, ai

    # Details
    details = Column(Text)  # JSON string with additional details
    status = Column(String(20))  # success, failed, warning
    error_message = Column(Text)

    # Metadata
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    duration_ms = Column(Integer)  # Duration of action in milliseconds

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    inquiry = relationship("Inquiry", back_populates="logs")

    def __repr__(self):
        return f"<ActivityLog {self.id}: {self.action} at {self.timestamp}>"
