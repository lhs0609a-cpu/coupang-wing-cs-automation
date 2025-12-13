"""
Inquiry model - represents customer inquiries from Coupang Wing
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    coupang_inquiry_id = Column(String(100), unique=True, index=True, nullable=False)
    vendor_id = Column(String(100), nullable=False)

    # Customer Information
    customer_name = Column(String(100))
    customer_id = Column(String(100))

    # Order Information
    order_number = Column(String(100), index=True)
    product_id = Column(String(100), index=True)
    product_name = Column(String(500))

    # Inquiry Content
    inquiry_text = Column(Text, nullable=False)
    inquiry_category = Column(String(50), index=True)  # shipping, refund, product, etc.
    inquiry_subcategory = Column(String(50))

    # Classification
    classified_category = Column(String(50))  # Auto-classified category
    confidence_score = Column(Float, default=0.0)  # Classification confidence
    risk_level = Column(String(20))  # low, medium, high

    # Dates
    inquiry_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Status
    status = Column(String(20), default="pending")  # pending, processing, processed, failed
    requires_human = Column(Boolean, default=False)  # Flag for human intervention
    is_urgent = Column(Boolean, default=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), index=True)  # Assigned user

    # Metadata
    keywords = Column(Text)  # JSON string of extracted keywords
    sentiment = Column(String(20))  # positive, neutral, negative
    complexity_score = Column(Float, default=0.0)

    # Relationships
    responses = relationship("Response", back_populates="inquiry", cascade="all, delete-orphan")
    logs = relationship("ActivityLog", back_populates="inquiry", cascade="all, delete-orphan")
    comments = relationship("InquiryComment", back_populates="inquiry", cascade="all, delete-orphan")
    tags = relationship("InquiryTag", back_populates="inquiry", cascade="all, delete-orphan")
    assigned_to_user = relationship("User", back_populates="assigned_inquiries", foreign_keys=[assigned_to])

    def __repr__(self):
        return f"<Inquiry {self.id}: {self.coupang_inquiry_id}>"
