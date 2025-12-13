"""
Learning Service
Learns from human feedback to improve AI responses
"""
import difflib
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger

from ..models import Response, ResponseFeedback, LearningPattern, PromptImprovement, Inquiry


class LearningService:
    """
    Service for learning from feedback and improving responses
    """

    def __init__(self, db: Session):
        self.db = db

    def record_feedback(
        self,
        response_id: int,
        edited_text: str,
        edited_by: str,
        edit_reason: Optional[str] = None,
        quality_score: Optional[float] = None
    ) -> ResponseFeedback:
        """
        Record feedback when a response is edited

        Args:
            response_id: Response ID
            edited_text: Edited response text
            edited_by: Editor username
            edit_reason: Reason for edit
            quality_score: Quality rating (1-5)

        Returns:
            ResponseFeedback object
        """
        response = self.db.query(Response).filter(Response.id == response_id).first()
        if not response:
            raise ValueError(f"Response {response_id} not found")

        # Analyze changes
        changes_summary = self._analyze_changes(
            response.response_text,
            edited_text
        )

        improvement_category = self._categorize_improvement(
            response.response_text,
            edited_text
        )

        # Create feedback record
        feedback = ResponseFeedback(
            response_id=response_id,
            inquiry_id=response.inquiry_id,
            original_text=response.response_text,
            edited_text=edited_text,
            edited_by=edited_by,
            edit_reason=edit_reason,
            quality_score=quality_score,
            changes_summary=changes_summary,
            improvement_category=improvement_category
        )

        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)

        logger.info(f"Recorded feedback for response {response_id}: {improvement_category}")

        # Extract learning patterns
        self._extract_patterns(feedback)

        return feedback

    def apply_learned_patterns(self, text: str, category: Optional[str] = None) -> str:
        """
        Apply learned patterns to improve text

        Args:
            text: Original text
            category: Inquiry category

        Returns:
            Improved text
        """
        # Get active patterns
        query = self.db.query(LearningPattern).filter(
            LearningPattern.is_active == True,
            LearningPattern.confidence_score >= 0.6
        )

        if category:
            query = query.filter(
                (LearningPattern.category == category) |
                (LearningPattern.category.is_(None))
            )

        patterns = query.order_by(
            LearningPattern.success_rate.desc()
        ).all()

        improved_text = text

        for pattern in patterns:
            if pattern.before_pattern in improved_text:
                improved_text = improved_text.replace(
                    pattern.before_pattern,
                    pattern.after_pattern
                )

                # Update usage statistics
                pattern.times_applied += 1
                logger.debug(f"Applied pattern: {pattern.pattern_type}")

        if improved_text != text:
            self.db.commit()
            logger.info(f"Applied {len([p for p in patterns if p.before_pattern in text])} patterns")

        return improved_text

    def get_learning_insights(self, days: int = 30) -> Dict:
        """
        Get learning insights and statistics

        Args:
            days: Number of days to analyze

        Returns:
            Insights dictionary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        feedbacks = self.db.query(ResponseFeedback).filter(
            ResponseFeedback.created_at >= cutoff_date
        ).all()

        if not feedbacks:
            return {
                'total_feedbacks': 0,
                'improvement_categories': {},
                'top_patterns': [],
                'avg_quality_score': 0
            }

        # Analyze improvement categories
        categories = {}
        for feedback in feedbacks:
            cat = feedback.improvement_category or 'other'
            categories[cat] = categories.get(cat, 0) + 1

        # Get quality scores
        quality_scores = [f.quality_score for f in feedbacks if f.quality_score]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        # Top patterns
        top_patterns = self.db.query(LearningPattern).filter(
            LearningPattern.is_active == True
        ).order_by(
            LearningPattern.times_applied.desc()
        ).limit(10).all()

        return {
            'total_feedbacks': len(feedbacks),
            'improvement_categories': categories,
            'top_patterns': [
                {
                    'type': p.pattern_type,
                    'before': p.before_pattern[:50],
                    'after': p.after_pattern[:50],
                    'times_applied': p.times_applied,
                    'success_rate': p.success_rate
                }
                for p in top_patterns
            ],
            'avg_quality_score': round(avg_quality, 2),
            'edit_rate': self._calculate_edit_rate(days)
        }

    def suggest_prompt_improvements(self) -> Dict:
        """
        Analyze feedback to suggest AI prompt improvements

        Returns:
            Improvement suggestions
        """
        # Analyze recent feedback
        recent_feedbacks = self.db.query(ResponseFeedback).order_by(
            ResponseFeedback.created_at.desc()
        ).limit(100).all()

        if not recent_feedbacks:
            return {'suggestions': []}

        # Categorize common issues
        issues = {}
        for feedback in recent_feedbacks:
            category = feedback.improvement_category or 'other'
            if category not in issues:
                issues[category] = []
            issues[category].append(feedback.edit_reason or '')

        suggestions = []

        # Generate suggestions based on common issues
        for category, reasons in issues.items():
            if len(reasons) >= 5:  # If issue appears 5+ times
                suggestions.append({
                    'category': category,
                    'frequency': len(reasons),
                    'suggestion': self._generate_prompt_suggestion(category, reasons)
                })

        return {
            'suggestions': suggestions,
            'analyzed_feedbacks': len(recent_feedbacks)
        }

    def create_prompt_version(
        self,
        version: str,
        prompt_text: str,
        notes: Optional[str] = None
    ) -> PromptImprovement:
        """
        Create a new prompt version for A/B testing

        Args:
            version: Version identifier
            prompt_text: New prompt text
            notes: Notes about changes

        Returns:
            PromptImprovement object
        """
        prompt = PromptImprovement(
            version=version,
            prompt_text=prompt_text,
            notes=notes,
            tested_from=datetime.utcnow()
        )

        self.db.add(prompt)
        self.db.commit()
        self.db.refresh(prompt)

        logger.info(f"Created prompt version: {version}")
        return prompt

    def _analyze_changes(self, original: str, edited: str) -> str:
        """Analyze what changed between original and edited text"""
        diff = list(difflib.unified_diff(
            original.splitlines(),
            edited.splitlines(),
            lineterm=''
        ))

        if not diff:
            return "No changes"

        added_lines = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed_lines = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        return f"Added {added_lines} lines, removed {removed_lines} lines"

    def _categorize_improvement(self, original: str, edited: str) -> str:
        """Categorize the type of improvement made"""
        # Length change
        len_diff = abs(len(edited) - len(original))
        len_pct_change = len_diff / len(original) * 100 if original else 0

        # Tone indicators
        formal_words = ['고객님', '감사드립니다', '도움']
        original_formal = sum(1 for word in formal_words if word in original)
        edited_formal = sum(1 for word in formal_words if word in edited)

        # Categorize
        if len_pct_change < 5:
            if edited_formal > original_formal:
                return 'tone_improvement'
            return 'minor_correction'
        elif len_pct_change < 20:
            return 'content_enhancement'
        elif len(edited) > len(original):
            return 'added_detail'
        else:
            return 'simplified'

    def _extract_patterns(self, feedback: ResponseFeedback):
        """Extract reusable patterns from feedback"""
        original_lines = feedback.original_text.split('\n')
        edited_lines = feedback.edited_text.split('\n')

        # Find sentence-level changes
        for i, (orig, edit) in enumerate(zip(original_lines, edited_lines)):
            if orig != edit and orig.strip() and edit.strip():
                # Check if this is a consistent pattern
                similarity = difflib.SequenceMatcher(None, orig, edit).ratio()

                if 0.3 < similarity < 0.9:  # Partial change, not complete rewrite
                    self._record_pattern(
                        feedback.improvement_category,
                        orig.strip(),
                        edit.strip(),
                        feedback.inquiry.classified_category if feedback.inquiry else None
                    )

    def _record_pattern(
        self,
        pattern_type: str,
        before: str,
        after: str,
        category: Optional[str]
    ):
        """Record a learning pattern"""
        # Check if pattern already exists
        existing = self.db.query(LearningPattern).filter(
            LearningPattern.before_pattern == before,
            LearningPattern.after_pattern == after
        ).first()

        if existing:
            existing.times_observed += 1
            existing.updated_at = datetime.utcnow()
        else:
            pattern = LearningPattern(
                pattern_type=pattern_type or 'general',
                category=category,
                before_pattern=before[:500],  # Limit length
                after_pattern=after[:500],
                times_observed=1,
                confidence_score=0.5
            )
            self.db.add(pattern)

        self.db.commit()

    def _calculate_edit_rate(self, days: int) -> float:
        """Calculate percentage of responses that were edited"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        total_responses = self.db.query(Response).filter(
            Response.created_at >= cutoff_date
        ).count()

        edited_responses = self.db.query(ResponseFeedback).filter(
            ResponseFeedback.created_at >= cutoff_date
        ).count()

        return round((edited_responses / total_responses * 100), 2) if total_responses > 0 else 0

    def _generate_prompt_suggestion(self, category: str, reasons: List[str]) -> str:
        """Generate prompt improvement suggestion based on feedback"""
        suggestions = {
            'tone_improvement': 'Consider adding more emphasis on polite and professional tone in the system prompt',
            'added_detail': 'Encourage the AI to provide more specific details and examples',
            'simplified': 'Ask the AI to be more concise and avoid unnecessary repetition',
            'minor_correction': 'Review factual accuracy guidelines',
            'content_enhancement': 'Request more comprehensive answers that address all aspects of the inquiry'
        }

        return suggestions.get(category, 'Review feedback examples for specific improvements')

    def export_training_data(self, min_quality_score: float = 4.0) -> List[Dict]:
        """
        Export high-quality feedback for fine-tuning

        Args:
            min_quality_score: Minimum quality score to include

        Returns:
            List of training examples
        """
        feedbacks = self.db.query(ResponseFeedback).filter(
            ResponseFeedback.quality_score >= min_quality_score,
            ResponseFeedback.used_for_training == False
        ).all()

        training_data = []

        for feedback in feedbacks:
            inquiry = self.db.query(Inquiry).filter(
                Inquiry.id == feedback.inquiry_id
            ).first()

            if inquiry:
                training_data.append({
                    'inquiry': inquiry.inquiry_text,
                    'category': inquiry.classified_category,
                    'original_response': feedback.original_text,
                    'improved_response': feedback.edited_text,
                    'quality_score': feedback.quality_score
                })

                # Mark as used
                feedback.used_for_training = True

        self.db.commit()

        logger.info(f"Exported {len(training_data)} training examples")
        return training_data
