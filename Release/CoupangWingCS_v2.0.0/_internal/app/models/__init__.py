"""
Database models
"""
from .inquiry import Inquiry
from .response import Response
from .log import ActivityLog
from .knowledge_base import KnowledgeBase

__all__ = ["Inquiry", "Response", "ActivityLog", "KnowledgeBase"]
