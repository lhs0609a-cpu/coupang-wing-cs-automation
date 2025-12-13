"""
Smart Template Recommendation AI
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from loguru import logger
from datetime import datetime, timedelta
import re

from ..models import Template, Inquiry, Response


class TemplateRecommendationService:
    """
    AI-powered template recommendation system
    """

    def __init__(self, db: Session):
        self.db = db

    def recommend_templates(
        self,
        inquiry: Inquiry,
        limit: int = 5
    ) -> List[Dict]:
        """
        Recommend templates for an inquiry using multiple strategies

        Args:
            inquiry: Inquiry object
            limit: Number of recommendations

        Returns:
            List of recommended templates with confidence scores
        """
        recommendations = []

        # Strategy 1: Category matching
        category_matches = self._match_by_category(inquiry, limit)
        recommendations.extend(category_matches)

        # Strategy 2: Keyword matching
        keyword_matches = self._match_by_keywords(inquiry, limit)
        recommendations.extend(keyword_matches)

        # Strategy 3: Historical success rate
        historical_matches = self._match_by_history(inquiry, limit)
        recommendations.extend(historical_matches)

        # Strategy 4: Similar inquiry matching
        similar_matches = self._match_by_similarity(inquiry, limit)
        recommendations.extend(similar_matches)

        # Combine and rank recommendations
        final_recommendations = self._rank_recommendations(
            recommendations,
            limit
        )

        logger.info(f"Generated {len(final_recommendations)} template recommendations for inquiry {inquiry.id}")
        return final_recommendations

    def _match_by_category(self, inquiry: Inquiry, limit: int) -> List[Dict]:
        """Match templates by inquiry category"""
        if not inquiry.classified_category:
            return []

        templates = self.db.query(Template).filter(
            Template.category == inquiry.classified_category,
            Template.is_active == True
        ).all()

        results = []
        for template in templates:
            confidence = 0.7  # Base confidence for category match

            # Boost if risk levels match
            if template.risk_level == inquiry.risk_level:
                confidence += 0.1

            results.append({
                'template': template,
                'confidence': min(confidence, 1.0),
                'reason': 'category_match',
                'variables': self._extract_variables(template.content)
            })

        return results

    def _match_by_keywords(self, inquiry: Inquiry, limit: int) -> List[Dict]:
        """Match templates by keyword overlap"""
        if not inquiry.inquiry_text:
            return []

        # Extract keywords from inquiry
        inquiry_keywords = self._extract_keywords(inquiry.inquiry_text)

        templates = self.db.query(Template).filter(
            Template.is_active == True
        ).all()

        results = []
        for template in templates:
            # Count keyword matches in template content
            template_keywords = self._extract_keywords(template.content)
            common_keywords = set(inquiry_keywords) & set(template_keywords)

            if common_keywords:
                # Calculate confidence based on keyword overlap
                overlap_ratio = len(common_keywords) / max(len(inquiry_keywords), 1)
                confidence = min(0.5 + (overlap_ratio * 0.3), 0.8)

                results.append({
                    'template': template,
                    'confidence': confidence,
                    'reason': 'keyword_match',
                    'matched_keywords': list(common_keywords),
                    'variables': self._extract_variables(template.content)
                })

        return results

    def _match_by_history(self, inquiry: Inquiry, limit: int) -> List[Dict]:
        """Match templates based on historical success"""
        # Get templates that have been successfully used
        successful_templates = self.db.query(
            Response.template_id,
            func.count(Response.id).label('usage_count'),
            func.avg(Response.confidence_score).label('avg_confidence')
        ).filter(
            Response.status == 'approved',
            Response.template_id.isnot(None)
        ).group_by(
            Response.template_id
        ).order_by(
            desc('usage_count')
        ).limit(limit).all()

        results = []
        for template_id, usage_count, avg_confidence in successful_templates:
            template = self.db.query(Template).filter(
                Template.id == template_id
            ).first()

            if template and template.is_active:
                # Confidence based on historical performance
                confidence = min(0.6 + (avg_confidence * 0.2), 0.8)

                results.append({
                    'template': template,
                    'confidence': confidence,
                    'reason': 'historical_success',
                    'usage_count': usage_count,
                    'avg_score': float(avg_confidence) if avg_confidence else 0,
                    'variables': self._extract_variables(template.content)
                })

        return results

    def _match_by_similarity(self, inquiry: Inquiry, limit: int) -> List[Dict]:
        """Match templates based on similar past inquiries"""
        if not inquiry.classified_category:
            return []

        # Find similar inquiries
        similar_inquiries = self.db.query(Inquiry).filter(
            Inquiry.classified_category == inquiry.classified_category,
            Inquiry.id != inquiry.id,
            Inquiry.status == 'responded'
        ).order_by(
            desc(Inquiry.created_at)
        ).limit(20).all()

        # Get templates used for similar inquiries
        template_usage = {}
        for similar_inq in similar_inquiries:
            responses = self.db.query(Response).filter(
                Response.inquiry_id == similar_inq.id,
                Response.status == 'approved',
                Response.template_id.isnot(None)
            ).all()

            for response in responses:
                if response.template_id not in template_usage:
                    template_usage[response.template_id] = {
                        'count': 0,
                        'total_confidence': 0
                    }
                template_usage[response.template_id]['count'] += 1
                template_usage[response.template_id]['total_confidence'] += (response.confidence_score or 0)

        results = []
        for template_id, usage_data in template_usage.items():
            template = self.db.query(Template).filter(
                Template.id == template_id
            ).first()

            if template and template.is_active:
                avg_confidence = usage_data['total_confidence'] / usage_data['count']
                confidence = min(0.55 + (avg_confidence * 0.2), 0.75)

                results.append({
                    'template': template,
                    'confidence': confidence,
                    'reason': 'similar_inquiry',
                    'similar_count': usage_data['count'],
                    'variables': self._extract_variables(template.content)
                })

        return results

    def _rank_recommendations(
        self,
        recommendations: List[Dict],
        limit: int
    ) -> List[Dict]:
        """
        Combine and rank recommendations from different strategies
        """
        # Group by template ID and combine scores
        template_scores = {}

        for rec in recommendations:
            template_id = rec['template'].id

            if template_id not in template_scores:
                template_scores[template_id] = {
                    'template': rec['template'],
                    'total_confidence': 0,
                    'reasons': [],
                    'variables': rec.get('variables', {}),
                    'metadata': {}
                }

            # Add confidence score
            template_scores[template_id]['total_confidence'] += rec['confidence']
            template_scores[template_id]['reasons'].append(rec['reason'])

            # Store additional metadata
            if 'matched_keywords' in rec:
                template_scores[template_id]['metadata']['keywords'] = rec['matched_keywords']
            if 'usage_count' in rec:
                template_scores[template_id]['metadata']['usage_count'] = rec['usage_count']

        # Normalize and sort
        final_recommendations = []
        for template_id, data in template_scores.items():
            # Normalize confidence (average of all strategies)
            normalized_confidence = min(
                data['total_confidence'] / len(data['reasons']),
                1.0
            )

            final_recommendations.append({
                'template_id': template_id,
                'template_name': data['template'].name,
                'template_content': data['template'].content,
                'confidence': round(normalized_confidence, 2),
                'reasons': list(set(data['reasons'])),
                'variables': data['variables'],
                'metadata': data['metadata']
            })

        # Sort by confidence
        final_recommendations.sort(key=lambda x: x['confidence'], reverse=True)

        return final_recommendations[:limit]

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return []

        # Remove special characters and convert to lowercase
        cleaned = re.sub(r'[^\w\s가-힣]', ' ', text.lower())

        # Split into words
        words = cleaned.split()

        # Filter out common words (simple Korean stop words)
        stop_words = {
            '이', '그', '저', '것', '수', '등', '및', '에', '의', '가', '을', '를',
            '은', '는', '이다', '있다', '하다', '되다', '입니다', '했습니다'
        }

        keywords = [word for word in words if word not in stop_words and len(word) > 1]

        return keywords

    def _extract_variables(self, template_content: str) -> Dict[str, str]:
        """
        Extract variable placeholders from template content

        Returns:
            Dict mapping variable names to descriptions
        """
        variables = {}

        # Match patterns like {{customer_name}}, {{order_number}}, etc.
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, template_content)

        for var_name in matches:
            # Generate user-friendly description
            description = var_name.replace('_', ' ').title()
            variables[var_name] = description

        return variables

    def pre_fill_template(
        self,
        template_content: str,
        inquiry: Inquiry
    ) -> Tuple[str, Dict[str, bool]]:
        """
        Automatically pre-fill template variables from inquiry data

        Args:
            template_content: Template text with variables
            inquiry: Inquiry object

        Returns:
            Tuple of (filled_content, fill_status_dict)
        """
        filled_content = template_content
        fill_status = {}

        # Map inquiry fields to template variables
        variable_mapping = {
            'customer_name': inquiry.customer_name,
            'customer_id': inquiry.customer_id,
            'order_number': inquiry.order_number,
            'product_name': inquiry.product_name,
            'inquiry_date': inquiry.inquiry_date.strftime('%Y-%m-%d') if inquiry.inquiry_date else None,
            'category': inquiry.classified_category
        }

        # Replace variables
        for var_name, var_value in variable_mapping.items():
            pattern = f'{{{{{var_name}}}}}'
            if pattern in filled_content:
                if var_value:
                    filled_content = filled_content.replace(pattern, str(var_value))
                    fill_status[var_name] = True
                else:
                    # Keep placeholder if no value available
                    fill_status[var_name] = False

        logger.info(f"Pre-filled template with {sum(fill_status.values())} variables")
        return filled_content, fill_status

    def get_template_performance_stats(self, template_id: int) -> Dict:
        """
        Get performance statistics for a template

        Args:
            template_id: Template ID

        Returns:
            Performance statistics
        """
        # Get all responses using this template
        responses = self.db.query(Response).filter(
            Response.template_id == template_id
        ).all()

        if not responses:
            return {
                'usage_count': 0,
                'approval_rate': 0,
                'avg_confidence': 0,
                'avg_processing_time': 0
            }

        total = len(responses)
        approved = sum(1 for r in responses if r.status == 'approved')
        total_confidence = sum(r.confidence_score or 0 for r in responses)

        # Calculate average processing time
        processing_times = []
        for r in responses:
            if r.submitted_at and r.created_at:
                delta = (r.submitted_at - r.created_at).total_seconds()
                processing_times.append(delta)

        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

        return {
            'usage_count': total,
            'approval_rate': round(approved / total, 2) if total > 0 else 0,
            'avg_confidence': round(total_confidence / total, 2) if total > 0 else 0,
            'avg_processing_time': round(avg_processing_time, 2),
            'last_used': max(r.created_at for r in responses) if responses else None
        }
