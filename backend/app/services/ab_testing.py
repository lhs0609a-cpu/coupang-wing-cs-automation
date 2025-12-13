"""
A/B Testing System for Response Templates
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger
import random
import math

from ..models import Template, Response, Inquiry


class ABTestingService:
    """
    A/B testing system for comparing template effectiveness
    """

    def __init__(self, db: Session):
        self.db = db
        self.active_tests = {}  # In-memory test registry

    def create_ab_test(
        self,
        name: str,
        template_a_id: int,
        template_b_id: int,
        description: str = "",
        traffic_split: float = 0.5,
        duration_days: int = 7
    ) -> Dict:
        """
        Create a new A/B test

        Args:
            name: Test name
            template_a_id: Control template ID
            template_b_id: Variant template ID
            description: Test description
            traffic_split: Percentage of traffic to variant (0.0-1.0)
            duration_days: Test duration in days

        Returns:
            Test configuration
        """
        # Validate templates exist
        template_a = self.db.query(Template).filter(Template.id == template_a_id).first()
        template_b = self.db.query(Template).filter(Template.id == template_b_id).first()

        if not template_a or not template_b:
            raise ValueError("One or both templates not found")

        test_id = f"test_{int(datetime.utcnow().timestamp())}"

        test_config = {
            'test_id': test_id,
            'name': name,
            'description': description,
            'template_a': {
                'id': template_a_id,
                'name': template_a.name,
                'variant': 'A (Control)'
            },
            'template_b': {
                'id': template_b_id,
                'name': template_b.name,
                'variant': 'B (Variant)'
            },
            'traffic_split': traffic_split,
            'start_date': datetime.utcnow(),
            'end_date': datetime.utcnow() + timedelta(days=duration_days),
            'status': 'active',
            'metrics': {
                'variant_a': {'impressions': 0, 'approvals': 0, 'rejections': 0},
                'variant_b': {'impressions': 0, 'approvals': 0, 'rejections': 0}
            }
        }

        # Store in active tests
        self.active_tests[test_id] = test_config

        logger.info(f"Created A/B test: {name} ({test_id})")
        return test_config

    def assign_variant(self, test_id: str) -> Dict:
        """
        Assign a user to a test variant

        Args:
            test_id: Test identifier

        Returns:
            Assigned variant information
        """
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")

        test = self.active_tests[test_id]

        # Check if test is still active
        if datetime.utcnow() > test['end_date']:
            test['status'] = 'completed'
            raise ValueError(f"Test {test_id} has ended")

        # Randomly assign based on traffic split
        use_variant_b = random.random() < test['traffic_split']

        if use_variant_b:
            variant = 'B'
            template = test['template_b']
            test['metrics']['variant_b']['impressions'] += 1
        else:
            variant = 'A'
            template = test['template_a']
            test['metrics']['variant_a']['impressions'] += 1

        return {
            'test_id': test_id,
            'variant': variant,
            'template_id': template['id'],
            'template_name': template['name']
        }

    def record_outcome(
        self,
        test_id: str,
        variant: str,
        outcome: str,
        response_id: Optional[int] = None
    ):
        """
        Record the outcome of a test variant

        Args:
            test_id: Test identifier
            variant: 'A' or 'B'
            outcome: 'approved', 'rejected', 'edited'
            response_id: Associated response ID
        """
        if test_id not in self.active_tests:
            logger.warning(f"Test {test_id} not found")
            return

        test = self.active_tests[test_id]
        variant_key = f'variant_{variant.lower()}'

        if variant_key not in test['metrics']:
            logger.warning(f"Variant {variant} not found in test {test_id}")
            return

        # Record outcome
        if outcome == 'approved':
            test['metrics'][variant_key]['approvals'] += 1
        elif outcome == 'rejected':
            test['metrics'][variant_key]['rejections'] += 1

        logger.debug(f"Recorded {outcome} for test {test_id}, variant {variant}")

    def get_test_results(self, test_id: str) -> Dict:
        """
        Get current test results with statistical analysis

        Args:
            test_id: Test identifier

        Returns:
            Test results and statistics
        """
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")

        test = self.active_tests[test_id]

        # Calculate metrics for each variant
        variant_a_stats = self._calculate_variant_stats(
            test['metrics']['variant_a'],
            test['template_a']['name']
        )

        variant_b_stats = self._calculate_variant_stats(
            test['metrics']['variant_b'],
            test['template_b']['name']
        )

        # Calculate statistical significance
        significance = self._calculate_statistical_significance(
            variant_a_stats,
            variant_b_stats
        )

        # Determine winner
        winner = self._determine_winner(
            variant_a_stats,
            variant_b_stats,
            significance
        )

        return {
            'test_id': test_id,
            'name': test['name'],
            'status': test['status'],
            'start_date': test['start_date'].isoformat(),
            'end_date': test['end_date'].isoformat(),
            'variant_a': variant_a_stats,
            'variant_b': variant_b_stats,
            'statistical_significance': significance,
            'winner': winner,
            'recommendation': self._generate_recommendation(
                variant_a_stats,
                variant_b_stats,
                significance
            )
        }

    def _calculate_variant_stats(self, metrics: Dict, name: str) -> Dict:
        """Calculate statistics for a variant"""
        impressions = metrics['impressions']
        approvals = metrics['approvals']
        rejections = metrics['rejections']

        total_outcomes = approvals + rejections
        approval_rate = approvals / total_outcomes if total_outcomes > 0 else 0
        rejection_rate = rejections / total_outcomes if total_outcomes > 0 else 0

        return {
            'name': name,
            'impressions': impressions,
            'approvals': approvals,
            'rejections': rejections,
            'total_outcomes': total_outcomes,
            'approval_rate': round(approval_rate, 4),
            'rejection_rate': round(rejection_rate, 4),
            'conversion_rate': round(approval_rate, 4)  # Same as approval rate
        }

    def _calculate_statistical_significance(
        self,
        variant_a: Dict,
        variant_b: Dict
    ) -> Dict:
        """
        Calculate statistical significance using z-test for proportions

        Returns:
            Statistical significance analysis
        """
        # Sample sizes
        n_a = variant_a['total_outcomes']
        n_b = variant_b['total_outcomes']

        if n_a < 30 or n_b < 30:
            return {
                'is_significant': False,
                'p_value': None,
                'confidence_level': 0,
                'message': 'Insufficient sample size (need at least 30 per variant)'
            }

        # Conversion rates
        p_a = variant_a['approval_rate']
        p_b = variant_b['approval_rate']

        # Pooled proportion
        p_pooled = (variant_a['approvals'] + variant_b['approvals']) / (n_a + n_b)

        # Standard error
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n_a + 1/n_b))

        if se == 0:
            return {
                'is_significant': False,
                'p_value': None,
                'confidence_level': 0,
                'message': 'Cannot calculate significance (SE = 0)'
            }

        # Z-score
        z_score = (p_b - p_a) / se

        # Approximate p-value (two-tailed test)
        # Using standard normal approximation
        from math import erf
        p_value = 2 * (1 - 0.5 * (1 + erf(abs(z_score) / math.sqrt(2))))

        # Determine significance level
        is_significant = p_value < 0.05
        confidence_level = (1 - p_value) * 100

        return {
            'is_significant': is_significant,
            'p_value': round(p_value, 4),
            'z_score': round(z_score, 4),
            'confidence_level': round(confidence_level, 2),
            'message': 'Statistically significant' if is_significant else 'Not statistically significant'
        }

    def _determine_winner(
        self,
        variant_a: Dict,
        variant_b: Dict,
        significance: Dict
    ) -> Dict:
        """Determine the winning variant"""
        if not significance['is_significant']:
            return {
                'variant': None,
                'message': 'No clear winner - results not statistically significant'
            }

        # Compare approval rates
        if variant_b['approval_rate'] > variant_a['approval_rate']:
            improvement = ((variant_b['approval_rate'] - variant_a['approval_rate']) /
                          variant_a['approval_rate'] * 100 if variant_a['approval_rate'] > 0 else 0)
            return {
                'variant': 'B',
                'name': variant_b['name'],
                'improvement': round(improvement, 2),
                'message': f"Variant B wins with {improvement:.1f}% improvement"
            }
        elif variant_a['approval_rate'] > variant_b['approval_rate']:
            improvement = ((variant_a['approval_rate'] - variant_b['approval_rate']) /
                          variant_b['approval_rate'] * 100 if variant_b['approval_rate'] > 0 else 0)
            return {
                'variant': 'A',
                'name': variant_a['name'],
                'improvement': round(improvement, 2),
                'message': f"Variant A wins with {improvement:.1f}% improvement"
            }
        else:
            return {
                'variant': None,
                'message': 'No winner - approval rates are equal'
            }

    def _generate_recommendation(
        self,
        variant_a: Dict,
        variant_b: Dict,
        significance: Dict
    ) -> str:
        """Generate action recommendation based on results"""
        if not significance['is_significant']:
            if variant_a['total_outcomes'] < 30 or variant_b['total_outcomes'] < 30:
                return "Continue test - need more data for statistical significance"
            else:
                return "No significant difference found - use either variant or test different approaches"

        winner = self._determine_winner(variant_a, variant_b, significance)

        if winner['variant'] == 'B':
            return f"Implement Variant B - shows {winner['improvement']:.1f}% improvement with {significance['confidence_level']:.0f}% confidence"
        elif winner['variant'] == 'A':
            return f"Keep Variant A - performs {winner['improvement']:.1f}% better with {significance['confidence_level']:.0f}% confidence"
        else:
            return "No clear winner - consider testing alternative variations"

    def stop_test(self, test_id: str) -> Dict:
        """
        Stop an active test

        Args:
            test_id: Test identifier

        Returns:
            Final test results
        """
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")

        test = self.active_tests[test_id]
        test['status'] = 'stopped'
        test['actual_end_date'] = datetime.utcnow()

        logger.info(f"Stopped test {test_id}")
        return self.get_test_results(test_id)

    def get_active_tests(self) -> List[Dict]:
        """Get all active tests"""
        active = []

        for test_id, test in self.active_tests.items():
            if test['status'] == 'active' and datetime.utcnow() <= test['end_date']:
                active.append({
                    'test_id': test_id,
                    'name': test['name'],
                    'start_date': test['start_date'].isoformat(),
                    'end_date': test['end_date'].isoformat(),
                    'template_a': test['template_a']['name'],
                    'template_b': test['template_b']['name'],
                    'impressions_a': test['metrics']['variant_a']['impressions'],
                    'impressions_b': test['metrics']['variant_b']['impressions']
                })

        return active

    def get_template_performance_comparison(
        self,
        template_ids: List[int],
        days: int = 30
    ) -> Dict:
        """
        Compare historical performance of multiple templates

        Args:
            template_ids: List of template IDs to compare
            days: Number of days to analyze

        Returns:
            Comparison data
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        comparison = []

        for template_id in template_ids:
            # Get template
            template = self.db.query(Template).filter(
                Template.id == template_id
            ).first()

            if not template:
                continue

            # Get responses using this template
            responses = self.db.query(Response).filter(
                Response.template_id == template_id,
                Response.created_at >= start_date
            ).all()

            total = len(responses)
            if total == 0:
                continue

            approved = sum(1 for r in responses if r.status == 'approved')
            rejected = sum(1 for r in responses if r.status == 'rejected')
            avg_confidence = sum(r.confidence_score or 0 for r in responses) / total

            comparison.append({
                'template_id': template_id,
                'template_name': template.name,
                'total_uses': total,
                'approvals': approved,
                'rejections': rejected,
                'approval_rate': round(approved / total, 4) if total > 0 else 0,
                'avg_confidence': round(avg_confidence, 4)
            })

        # Sort by approval rate
        comparison.sort(key=lambda x: x['approval_rate'], reverse=True)

        return {
            'period_days': days,
            'templates_compared': len(comparison),
            'comparison': comparison
        }
