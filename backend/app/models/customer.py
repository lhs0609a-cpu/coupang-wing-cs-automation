"""
Customer Profile and History Models
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON
from datetime import datetime

from ..database import Base


class CustomerProfile(Base):
    """
    Customer profile with aggregated data
    """
    __tablename__ = "customer_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # Customer identification
    customer_id = Column(String(100), unique=True, nullable=False, index=True)
    customer_name = Column(String(200))
    customer_email = Column(String(200))

    # Statistics
    total_inquiries = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    satisfaction_score = Column(Float)  # Average satisfaction if available

    # Behavior patterns
    common_inquiry_categories = Column(JSON)  # List of common categories
    preferred_contact_time = Column(String(50))  # morning, afternoon, evening
    response_rate = Column(Float)  # How often they respond to follow-ups

    # Customer type
    customer_tier = Column(String(20))  # regular, vip, problematic
    is_frequent_complainer = Column(Boolean, default=False)
    is_vip = Column(Boolean, default=False)

    # Recent activity
    last_inquiry_date = Column(DateTime)
    last_order_date = Column(DateTime)

    # Notes
    internal_notes = Column(Text)  # Private notes about the customer

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CustomerProfile {self.customer_id}: {self.customer_name}>"
