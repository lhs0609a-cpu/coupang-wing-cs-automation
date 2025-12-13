"""
Learning and Feedback Models
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class ResponseFeedback(Base):
    """
    Response feedback and edits for learning
    """
    __tablename__ = "response_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("responses.id"), nullable=False)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), nullable=False)

    # Original and edited versions
    original_text = Column(Text, nullable=False)
    edited_text = Column(Text, nullable=False)

    # Editor information
    edited_by = Column(String(100), nullable=False)
    edit_reason = Column(Text)

    # Feedback scores
    quality_score = Column(Float)  # 1-5 rating
    was_helpful = Column(Boolean)

    # Learning data
    changes_summary = Column(Text)  # Summary of what was changed
    improvement_category = Column(String(50))  # tone, accuracy, completeness, etc.

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    used_for_training = Column(Boolean, default=False)

    # Relationships
    response = relationship("Response", back_populates="feedbacks")
    inquiry = relationship("Inquiry")


class LearningPattern(Base):
    """
    Learned patterns from feedback
    """
    __tablename__ = "learning_patterns"

    id = Column(Integer, primary_key=True, index=True)

    # Pattern information
    pattern_type = Column(String(50), nullable=False)  # phrase_replacement, tone_adjustment, etc.
    category = Column(String(50))  # Category where pattern applies

    # Pattern details
    before_pattern = Column(Text, nullable=False)
    after_pattern = Column(Text, nullable=False)
    context = Column(Text)  # When to apply this pattern

    # Usage statistics
    times_observed = Column(Integer, default=1)
    times_applied = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)

    # Metadata
    confidence_score = Column(Float, default=0.5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PromptImprovement(Base):
    """
    AI prompt improvements based on feedback
    """
    __tablename__ = "prompt_improvements"

    id = Column(Integer, primary_key=True, index=True)

    # Prompt version
    version = Column(String(20), nullable=False, unique=True)
    prompt_text = Column(Text, nullable=False)

    # Performance metrics
    avg_quality_score = Column(Float)
    edit_rate = Column(Float)  # Percentage of responses that needed editing
    usage_count = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=False)
    tested_from = Column(DateTime)
    tested_until = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
