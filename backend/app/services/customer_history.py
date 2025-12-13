"""
Customer History Service
Tracks customer interaction history and patterns
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from loguru import logger
from collections import Counter

from ..models import Inquiry, Response, CustomerProfile


class CustomerHistoryService:
    """
    Service for managing customer history and profiles
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_profile(self, customer_id: str, customer_name: Optional[str] = None) -> CustomerProfile:
        """
        Get existing customer profile or create new one

        Args:
            customer_id: Customer ID
            customer_name: Customer name (optional)

        Returns:
            CustomerProfile object
        """
        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()

        if not profile:
            profile = CustomerProfile(
                customer_id=customer_id,
                customer_name=customer_name
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            logger.info(f"Created new customer profile: {customer_id}")

        return profile

    def update_profile_from_inquiry(self, inquiry: Inquiry):
        """
        Update customer profile based on new inquiry

        Args:
            inquiry: Inquiry object
        """
        if not inquiry.customer_id:
            return

        profile = self.get_or_create_profile(
            inquiry.customer_id,
            inquiry.customer_name
        )

        # Update statistics
        profile.total_inquiries += 1
        profile.last_inquiry_date = inquiry.inquiry_date or inquiry.created_at

        # Update common categories
        self._update_common_categories(profile, inquiry.classified_category)

        # Evaluate customer tier
        profile.customer_tier = self._evaluate_customer_tier(profile)

        # Check if frequent complainer
        profile.is_frequent_complainer = self._check_frequent_complainer(inquiry.customer_id)

        self.db.commit()

    def get_customer_history(self, customer_id: str, limit: int = 50) -> Dict:
        """
        Get complete customer history

        Args:
            customer_id: Customer ID
            limit: Maximum number of records

        Returns:
            Customer history dictionary
        """
        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()

        inquiries = self.db.query(Inquiry).filter(
            Inquiry.customer_id == customer_id
        ).order_by(desc(Inquiry.created_at)).limit(limit).all()

        # Get responses for these inquiries
        inquiry_ids = [inq.id for inq in inquiries]
        responses = self.db.query(Response).filter(
            Response.inquiry_id.in_(inquiry_ids)
        ).all()

        # Map responses to inquiries
        response_map = {r.inquiry_id: r for r in responses}

        history = []
        for inquiry in inquiries:
            response = response_map.get(inquiry.id)
            history.append({
                'inquiry_id': inquiry.id,
                'inquiry_date': inquiry.inquiry_date.isoformat() if inquiry.inquiry_date else None,
                'category': inquiry.classified_category,
                'inquiry_text': inquiry.inquiry_text[:200],
                'status': inquiry.status,
                'risk_level': inquiry.risk_level,
                'has_response': response is not None,
                'response_status': response.status if response else None
            })

        return {
            'profile': {
                'customer_id': profile.customer_id if profile else customer_id,
                'customer_name': profile.customer_name if profile else None,
                'total_inquiries': profile.total_inquiries if profile else 0,
                'customer_tier': profile.customer_tier if profile else 'regular',
                'is_vip': profile.is_vip if profile else False,
                'satisfaction_score': profile.satisfaction_score if profile else None
            },
            'history': history,
            'patterns': self.analyze_customer_patterns(customer_id)
        }

    def analyze_customer_patterns(self, customer_id: str) -> Dict:
        """
        Analyze customer behavior patterns

        Args:
            customer_id: Customer ID

        Returns:
            Patterns dictionary
        """
        inquiries = self.db.query(Inquiry).filter(
            Inquiry.customer_id == customer_id
        ).all()

        if not inquiries:
            return {}

        # Analyze categories
        categories = [inq.classified_category for inq in inquiries if inq.classified_category]
        category_counts = Counter(categories)

        # Analyze timing
        inquiry_hours = [inq.inquiry_date.hour for inq in inquiries if inq.inquiry_date]
        preferred_time = self._determine_preferred_time(inquiry_hours)

        # Analyze sentiment
        sentiments = [inq.sentiment for inq in inquiries if inq.sentiment]
        negative_count = sum(1 for s in sentiments if s == 'negative')

        # Response time expectations
        avg_complexity = sum(inq.complexity_score or 0 for inq in inquiries) / len(inquiries)

        return {
            'most_common_categories': dict(category_counts.most_common(3)),
            'preferred_contact_time': preferred_time,
            'negative_sentiment_rate': round(negative_count / len(sentiments) * 100, 2) if sentiments else 0,
            'avg_inquiry_complexity': round(avg_complexity, 2),
            'repeat_inquiry_rate': self._calculate_repeat_rate(inquiries)
        }

    def get_similar_past_inquiries(
        self,
        inquiry: Inquiry,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar past inquiries from same customer

        Args:
            inquiry: Current inquiry
            limit: Maximum results

        Returns:
            List of similar inquiries
        """
        if not inquiry.customer_id:
            return []

        # Get past inquiries from same customer
        past_inquiries = self.db.query(Inquiry).filter(
            and_(
                Inquiry.customer_id == inquiry.customer_id,
                Inquiry.id != inquiry.id,
                Inquiry.classified_category == inquiry.classified_category
            )
        ).order_by(desc(Inquiry.created_at)).limit(limit * 2).all()

        # Score similarity
        scored_inquiries = []
        for past_inq in past_inquiries:
            similarity = self._calculate_text_similarity(
                inquiry.inquiry_text,
                past_inq.inquiry_text
            )

            if similarity > 0.3:  # Threshold
                scored_inquiries.append({
                    'inquiry': past_inq,
                    'similarity': similarity
                })

        # Sort by similarity and take top results
        scored_inquiries.sort(key=lambda x: x['similarity'], reverse=True)

        results = []
        for item in scored_inquiries[:limit]:
            past_inq = item['inquiry']

            # Get the response
            response = self.db.query(Response).filter(
                Response.inquiry_id == past_inq.id,
                Response.status == 'submitted'
            ).first()

            results.append({
                'inquiry_id': past_inq.id,
                'inquiry_date': past_inq.inquiry_date.isoformat() if past_inq.inquiry_date else None,
                'inquiry_text': past_inq.inquiry_text,
                'similarity_score': round(item['similarity'], 2),
                'response_text': response.response_text if response else None,
                'was_successful': response.submission_status == 'success' if response else None
            })

        return results

    def identify_vip_customers(self, min_orders: int = 10, min_satisfaction: float = 4.5) -> List[CustomerProfile]:
        """
        Identify VIP customers based on criteria

        Args:
            min_orders: Minimum number of orders
            min_satisfaction: Minimum satisfaction score

        Returns:
            List of VIP customer profiles
        """
        vip_customers = self.db.query(CustomerProfile).filter(
            and_(
                CustomerProfile.total_orders >= min_orders,
                CustomerProfile.satisfaction_score >= min_satisfaction,
                CustomerProfile.is_frequent_complainer == False
            )
        ).all()

        # Mark as VIP
        for customer in vip_customers:
            if not customer.is_vip:
                customer.is_vip = True

        self.db.commit()

        logger.info(f"Identified {len(vip_customers)} VIP customers")
        return vip_customers

    def get_recommendations_for_inquiry(self, inquiry: Inquiry) -> Dict:
        """
        Get recommendations based on customer history

        Args:
            inquiry: Current inquiry

        Returns:
            Recommendations dictionary
        """
        if not inquiry.customer_id:
            return {'recommendations': []}

        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == inquiry.customer_id
        ).first()

        recommendations = []

        # VIP handling
        if profile and profile.is_vip:
            recommendations.append({
                'type': 'vip_customer',
                'message': '⭐ VIP Customer - Prioritize and use enhanced service tone',
                'priority': 'high'
            })

        # Frequent complainer
        if profile and profile.is_frequent_complainer:
            recommendations.append({
                'type': 'frequent_complainer',
                'message': '⚠️ Frequent complainer - Extra care needed, consider escalation',
                'priority': 'medium'
            })

        # Similar past inquiries
        similar = self.get_similar_past_inquiries(inquiry, limit=3)
        if similar:
            recommendations.append({
                'type': 'similar_past_inquiries',
                'message': f'📋 Found {len(similar)} similar past inquiries - review previous responses',
                'similar_inquiries': similar,
                'priority': 'medium'
            })

        # Pattern-based recommendations
        patterns = self.analyze_customer_patterns(inquiry.customer_id)
        if patterns.get('negative_sentiment_rate', 0) > 50:
            recommendations.append({
                'type': 'negative_pattern',
                'message': '😞 Customer has high negative sentiment rate - use empathetic tone',
                'priority': 'high'
            })

        return {
            'recommendations': recommendations,
            'customer_profile': {
                'tier': profile.customer_tier if profile else 'regular',
                'total_inquiries': profile.total_inquiries if profile else 0,
                'is_vip': profile.is_vip if profile else False
            }
        }

    def _update_common_categories(self, profile: CustomerProfile, new_category: Optional[str]):
        """Update common inquiry categories"""
        if not new_category:
            return

        categories = profile.common_inquiry_categories or []

        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except:
                categories = []

        categories.append(new_category)

        # Keep only last 20 categories
        categories = categories[-20:]

        # Count occurrences
        category_counts = Counter(categories)
        profile.common_inquiry_categories = dict(category_counts.most_common(5))

    def _evaluate_customer_tier(self, profile: CustomerProfile) -> str:
        """Evaluate customer tier"""
        if profile.is_vip:
            return 'vip'

        if profile.total_inquiries > 20:
            return 'power_user'

        if profile.is_frequent_complainer:
            return 'needs_attention'

        return 'regular'

    def _check_frequent_complainer(self, customer_id: str, threshold: int = 5) -> bool:
        """Check if customer is frequent complainer"""
        recent_cutoff = datetime.utcnow() - timedelta(days=90)

        negative_inquiries = self.db.query(Inquiry).filter(
            and_(
                Inquiry.customer_id == customer_id,
                Inquiry.created_at >= recent_cutoff,
                Inquiry.sentiment == 'negative'
            )
        ).count()

        return negative_inquiries >= threshold

    def _determine_preferred_time(self, hours: List[int]) -> str:
        """Determine preferred contact time"""
        if not hours:
            return 'unknown'

        avg_hour = sum(hours) / len(hours)

        if avg_hour < 12:
            return 'morning'
        elif avg_hour < 18:
            return 'afternoon'
        else:
            return 'evening'

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (Jaccard similarity)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0

    def _calculate_repeat_rate(self, inquiries: List[Inquiry]) -> float:
        """Calculate rate of repeat inquiries"""
        if len(inquiries) < 2:
            return 0.0

        categories = [inq.classified_category for inq in inquiries if inq.classified_category]
        if not categories:
            return 0.0

        category_counts = Counter(categories)
        repeat_count = sum(count - 1 for count in category_counts.values() if count > 1)

        return round(repeat_count / len(categories) * 100, 2)
