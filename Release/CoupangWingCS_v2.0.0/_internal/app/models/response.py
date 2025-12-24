"""
Response model - represents generated responses to customer inquiries
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), nullable=False, index=True)

    # Response Content
    response_text = Column(Text, nullable=False)
    original_response = Column(Text)  # Store original before any edits

    # Quality Metrics
    confidence_score = Column(Float, default=0.0)
    risk_level = Column(String(20))  # low, medium, high
    quality_score = Column(Float, default=0.0)

    # Generation Details
    template_used = Column(String(100))
    generation_method = Column(String(50))  # template, ai, hybrid, manual
    policy_references = Column(Text)  # JSON string of policy IDs used

    # Validation Results
    validation_passed = Column(Boolean, default=False)
    validation_issues = Column(Text)  # JSON string of validation issues
    format_check_passed = Column(Boolean, default=True)
    content_check_passed = Column(Boolean, default=True)
    policy_check_passed = Column(Boolean, default=True)

    # Approval Workflow
    status = Column(String(20), default="draft")  # draft, pending_approval, approved, rejected, submitted
    approved_by = Column(String(100))  # Username/ID of approver
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)

    # Submission Details
    submitted_at = Column(DateTime)
    submitted_by = Column(String(100))
    submission_status = Column(String(20))  # success, failed, pending
    submission_error = Column(Text)

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    auto_approved = Column(Boolean, default=False)
    edit_count = Column(Integer, default=0)
    response_time_seconds = Column(Integer)  # Time from inquiry to response

    # Relationships
    inquiry = relationship("Inquiry", back_populates="responses")

    def __repr__(self):
        return f"<Response {self.id}: Inquiry {self.inquiry_id} - {self.status}>"
