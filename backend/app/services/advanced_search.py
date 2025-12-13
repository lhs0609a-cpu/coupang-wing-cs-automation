"""
Advanced Search Service
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from loguru import logger

from ..models import Inquiry, Response, CustomerProfile


class AdvancedSearchService:
    """
    Advanced search with complex filters
    """

    def __init__(self, db: Session):
        self.db = db

    def search_inquiries(self, filters: Dict[str, Any]) -> List[Inquiry]:
        """
        Advanced inquiry search

        Filters:
        - keyword: Text search in inquiry_text, product_name, customer_name
        - customer_id: Exact customer match
        - category: Inquiry category
        - risk_level: Risk level filter
        - status: Status filter
        - date_from: Start date
        - date_to: End date
        - is_urgent: Urgent flag
        - requires_human: Requires human flag
        - sentiment: Sentiment filter
        - assigned_to: Assigned user ID
        - has_tags: Has specific tags
        - confidence_min: Minimum confidence score
        - confidence_max: Maximum confidence score
        """
        query = self.db.query(Inquiry)

        # Keyword search (full-text like)
        if 'keyword' in filters and filters['keyword']:
            keyword = f"%{filters['keyword']}%"
            query = query.filter(
                or_(
                    Inquiry.inquiry_text.like(keyword),
                    Inquiry.product_name.like(keyword),
                    Inquiry.customer_name.like(keyword),
                    Inquiry.order_number.like(keyword)
                )
            )

        # Customer filter
        if 'customer_id' in filters:
            query = query.filter(Inquiry.customer_id == filters['customer_id'])

        # Category filter
        if 'category' in filters:
            if isinstance(filters['category'], list):
                query = query.filter(Inquiry.classified_category.in_(filters['category']))
            else:
                query = query.filter(Inquiry.classified_category == filters['category'])

        # Risk level filter
        if 'risk_level' in filters:
            query = query.filter(Inquiry.risk_level == filters['risk_level'])

        # Status filter
        if 'status' in filters:
            if isinstance(filters['status'], list):
                query = query.filter(Inquiry.status.in_(filters['status']))
            else:
                query = query.filter(Inquiry.status == filters['status'])

        # Date range filter
        if 'date_from' in filters:
            query = query.filter(Inquiry.inquiry_date >= filters['date_from'])

        if 'date_to' in filters:
            query = query.filter(Inquiry.inquiry_date <= filters['date_to'])

        # Boolean filters
        if 'is_urgent' in filters:
            query = query.filter(Inquiry.is_urgent == filters['is_urgent'])

        if 'requires_human' in filters:
            query = query.filter(Inquiry.requires_human == filters['requires_human'])

        # Sentiment filter
        if 'sentiment' in filters:
            query = query.filter(Inquiry.sentiment == filters['sentiment'])

        # Assigned to filter
        if 'assigned_to' in filters:
            query = query.filter(Inquiry.assigned_to == filters['assigned_to'])

        # Confidence score range
        if 'confidence_min' in filters:
            query = query.filter(Inquiry.confidence_score >= filters['confidence_min'])

        if 'confidence_max' in filters:
            query = query.filter(Inquiry.confidence_score <= filters['confidence_max'])

        # Sorting
        sort_by = filters.get('sort_by', 'created_at')
        sort_order = filters.get('sort_order', 'desc')

        if hasattr(Inquiry, sort_by):
            column = getattr(Inquiry, sort_by)
            if sort_order == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

        # Pagination
        limit = filters.get('limit', 50)
        offset = filters.get('offset', 0)

        return query.limit(limit).offset(offset).all()

    def save_search_filter(
        self,
        user_id: int,
        name: str,
        filters: Dict
    ) -> Dict:
        """
        Save frequently used search filter

        Args:
            user_id: User ID
            name: Filter name
            filters: Filter configuration

        Returns:
            Saved filter info
        """
        import json

        saved_filter = {
            'id': f"filter_{user_id}_{int(datetime.utcnow().timestamp())}",
            'user_id': user_id,
            'name': name,
            'filters': filters,
            'created_at': datetime.utcnow().isoformat()
        }

        # In production, save to database
        # For now, return the filter
        logger.info(f"Saved search filter: {name}")
        return saved_filter

    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """
        Get search suggestions based on partial query

        Args:
            partial_query: Partial search text
            limit: Maximum suggestions

        Returns:
            List of suggestions
        """
        suggestions = []

        # Product name suggestions
        products = self.db.query(Inquiry.product_name).filter(
            Inquiry.product_name.like(f"%{partial_query}%")
        ).distinct().limit(limit).all()

        suggestions.extend([p[0] for p in products if p[0]])

        # Customer name suggestions
        customers = self.db.query(Inquiry.customer_name).filter(
            Inquiry.customer_name.like(f"%{partial_query}%")
        ).distinct().limit(limit).all()

        suggestions.extend([c[0] for c in customers if c[0]])

        return list(set(suggestions))[:limit]
