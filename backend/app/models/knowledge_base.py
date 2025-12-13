"""
Knowledge Base model - stores policies, FAQs, and reference information
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from ..database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)

    # Classification
    category = Column(String(100), nullable=False, index=True)  # policy, faq, product_info, template
    subcategory = Column(String(100), index=True)

    # Content
    title = Column(String(500), nullable=False)
    keyword = Column(String(100), index=True)
    content = Column(Text, nullable=False)

    # Metadata
    priority = Column(Integer, default=0)  # Higher priority items are used first
    version = Column(String(50))
    source = Column(String(200))  # Source of information
    tags = Column(Text)  # JSON string of tags

    # Usage Statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)  # Percentage

    # Status
    is_active = Column(Boolean, default=True)
    requires_review = Column(Boolean, default=False)

    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String(100))

    def __repr__(self):
        return f"<KnowledgeBase {self.id}: {self.category} - {self.title}>"
