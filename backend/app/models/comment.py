"""
Internal Comment and Note Models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class InquiryComment(Base):
    """
    Internal comments for team collaboration
    """
    __tablename__ = "inquiry_comments"

    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Comment content
    content = Column(Text, nullable=False)
    mentions = Column(String(500))  # JSON array of mentioned user IDs

    # Status
    is_pinned = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inquiry = relationship("Inquiry", back_populates="comments")
    user = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<InquiryComment {self.id}: Inquiry {self.inquiry_id}>"


class InquiryTag(Base):
    """
    Tags for organizing inquiries
    """
    __tablename__ = "inquiry_tags"

    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), nullable=False, index=True)

    # Tag info
    name = Column(String(50), nullable=False)
    color = Column(String(20), default="#gray")  # Hex color or color name

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    inquiry = relationship("Inquiry", back_populates="tags")


class InquiryBookmark(Base):
    """
    User bookmarks/favorites for inquiries
    """
    __tablename__ = "inquiry_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Bookmark details
    note = Column(Text)  # Personal note
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    inquiry = relationship("Inquiry")
    user = relationship("User")
