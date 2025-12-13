"""
Template Model for Response Templates
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Template(Base):
    """
    Response template model
    """
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template Info
    name = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    description = Column(Text)

    # Categorization
    category = Column(String(100), index=True)  # Matches inquiry categories
    subcategory = Column(String(100))
    tags = Column(String(500))  # JSON array of tags

    # Usage Control
    is_active = Column(Boolean, default=True)
    risk_level = Column(String(20))  # low, medium, high
    requires_approval = Column(Boolean, default=False)

    # Performance Metrics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_confidence_score = Column(Float, default=0.0)
    last_used_at = Column(DateTime)

    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Variables in template (JSON array of variable names)
    variables = Column(String(1000))  # e.g., ["customer_name", "order_number"]

    def __repr__(self):
        return f"<Template {self.id}: {self.name}>"
