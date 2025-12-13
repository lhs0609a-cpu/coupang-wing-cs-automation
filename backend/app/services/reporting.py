"""
Reporting Service
Generates statistics and reports
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger

from ..models import Inquiry, Response, ActivityLog


class ReportingService:
    """
    Service for generating reports and statistics
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict:
        """
        Generate daily report

        Args:
            date: Date to generate report for (default: today)

        Returns:
            Report dictionary
        """
        if not date:
            date = datetime.utcnow()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        report = {
            'date': date.strftime('%Y-%m-%d'),
            'inquiries': self._get_inquiry_stats(start_of_day, end_of_day),
            'responses': self._get_response_stats(start_of_day, end_of_day),
            'automation': self._get_automation_stats(start_of_day, end_of_day),
            'categories': self._get_category_breakdown(start_of_day, end_of_day),
            'performance': self._get_performance_metrics(start_of_day, end_of_day)
        }

        return report

    def generate_weekly_report(self, weeks_ago: int = 0) -> Dict:
        """
        Generate weekly report

        Args:
            weeks_ago: Number of weeks ago (0 = current week)

        Returns:
            Report dictionary
        """
        today = datetime.utcnow()
        start_of_week = today - timedelta(days=today.weekday(), weeks=weeks_ago)
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=7)

        # Daily breakdown
        daily_stats = []
        for i in range(7):
            day_start = start_of_week + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'inquiries': self._count_inquiries(day_start, day_end),
                'responses': self._count_responses(day_start, day_end),
                'auto_approved': self._count_auto_approved(day_start, day_end)
            })

        report = {
            'week_start': start_of_week.strftime('%Y-%m-%d'),
            'week_end': end_of_week.strftime('%Y-%m-%d'),
            'daily_breakdown': daily_stats,
            'total_inquiries': self._count_inquiries(start_of_week, end_of_week),
            'total_responses': self._count_responses(start_of_week, end_of_week),
            'categories': self._get_category_breakdown(start_of_week, end_of_week),
            'top_issues': self._get_top_issues(start_of_week, end_of_week)
        }

        return report

    def generate_monthly_report(self, months_ago: int = 0) -> Dict:
        """
        Generate monthly report

        Args:
            months_ago: Number of months ago (0 = current month)

        Returns:
            Report dictionary
        """
        today = datetime.utcnow()

        # Calculate start of target month
        year = today.year
        month = today.month - months_ago

        while month < 1:
            month += 12
            year -= 1

        start_of_month = datetime(year, month, 1)

        # Calculate end of month
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1)
        else:
            end_of_month = datetime(year, month + 1, 1)

        report = {
            'month': start_of_month.strftime('%Y-%m'),
            'total_inquiries': self._count_inquiries(start_of_month, end_of_month),
            'total_responses': self._count_responses(start_of_month, end_of_month),
            'automation_rate': self._calculate_automation_rate(start_of_month, end_of_month),
            'categories': self._get_category_breakdown(start_of_month, end_of_month),
            'quality_metrics': self._get_quality_metrics(start_of_month, end_of_month),
            'response_times': self._get_response_time_stats(start_of_month, end_of_month)
        }

        return report

    def get_real_time_dashboard(self) -> Dict:
        """
        Get real-time dashboard statistics

        Returns:
            Dashboard data
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        return {
            'timestamp': now.isoformat(),
            'today': {
                'inquiries': self._count_inquiries(today_start, now),
                'responses': self._count_responses(today_start, now),
                'auto_approved': self._count_auto_approved(today_start, now),
                'pending_approval': self._count_pending_approval()
            },
            'pending': {
                'inquiries': self._count_pending_inquiries(),
                'responses': self._count_pending_approval(),
                'requires_human': self._count_requires_human()
            },
            'recent_activity': self._get_recent_activity(limit=10),
            'alerts': self._get_active_alerts()
        }

    def _get_inquiry_stats(self, start: datetime, end: datetime) -> Dict:
        """Get inquiry statistics for period"""
        total = self._count_inquiries(start, end)

        by_status = {}
        status_counts = self.db.query(
            Inquiry.status,
            func.count(Inquiry.id)
        ).filter(
            and_(
                Inquiry.created_at >= start,
                Inquiry.created_at < end
            )
        ).group_by(Inquiry.status).all()

        for status, count in status_counts:
            by_status[status] = count

        return {
            'total': total,
            'by_status': by_status,
            'urgent': self.db.query(Inquiry).filter(
                and_(
                    Inquiry.created_at >= start,
                    Inquiry.created_at < end,
                    Inquiry.is_urgent == True
                )
            ).count(),
            'requires_human': self.db.query(Inquiry).filter(
                and_(
                    Inquiry.created_at >= start,
                    Inquiry.created_at < end,
                    Inquiry.requires_human == True
                )
            ).count()
        }

    def _get_response_stats(self, start: datetime, end: datetime) -> Dict:
        """Get response statistics for period"""
        total = self._count_responses(start, end)

        by_status = {}
        status_counts = self.db.query(
            Response.status,
            func.count(Response.id)
        ).filter(
            and_(
                Response.created_at >= start,
                Response.created_at < end
            )
        ).group_by(Response.status).all()

        for status, count in status_counts:
            by_status[status] = count

        avg_confidence = self.db.query(
            func.avg(Response.confidence_score)
        ).filter(
            and_(
                Response.created_at >= start,
                Response.created_at < end
            )
        ).scalar() or 0

        return {
            'total': total,
            'by_status': by_status,
            'avg_confidence': round(avg_confidence, 2),
            'validation_passed': self.db.query(Response).filter(
                and_(
                    Response.created_at >= start,
                    Response.created_at < end,
                    Response.validation_passed == True
                )
            ).count()
        }

    def _get_automation_stats(self, start: datetime, end: datetime) -> Dict:
        """Get automation statistics"""
        total_responses = self._count_responses(start, end)
        auto_approved = self._count_auto_approved(start, end)

        automation_rate = (auto_approved / total_responses * 100) if total_responses > 0 else 0

        return {
            'total_responses': total_responses,
            'auto_approved': auto_approved,
            'automation_rate': round(automation_rate, 2),
            'human_reviewed': total_responses - auto_approved
        }

    def _get_category_breakdown(self, start: datetime, end: datetime) -> Dict:
        """Get breakdown by category"""
        categories = self.db.query(
            Inquiry.classified_category,
            func.count(Inquiry.id)
        ).filter(
            and_(
                Inquiry.created_at >= start,
                Inquiry.created_at < end,
                Inquiry.classified_category.isnot(None)
            )
        ).group_by(Inquiry.classified_category).all()

        breakdown = {}
        for category, count in categories:
            breakdown[category] = count

        return breakdown

    def _get_performance_metrics(self, start: datetime, end: datetime) -> Dict:
        """Get performance metrics"""
        responses = self.db.query(Response).filter(
            and_(
                Response.created_at >= start,
                Response.created_at < end,
                Response.response_time_seconds.isnot(None)
            )
        ).all()

        if not responses:
            return {
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0
            }

        response_times = [r.response_time_seconds for r in responses]

        return {
            'avg_response_time': round(sum(response_times) / len(response_times), 2),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times)
        }

    def _get_quality_metrics(self, start: datetime, end: datetime) -> Dict:
        """Get quality metrics"""
        responses = self.db.query(Response).filter(
            and_(
                Response.created_at >= start,
                Response.created_at < end
            )
        ).all()

        if not responses:
            return {}

        total = len(responses)
        high_confidence = sum(1 for r in responses if r.confidence_score and r.confidence_score >= 90)
        low_risk = sum(1 for r in responses if r.risk_level == 'low')

        return {
            'high_confidence_rate': round(high_confidence / total * 100, 2),
            'low_risk_rate': round(low_risk / total * 100, 2),
            'avg_confidence': round(sum(r.confidence_score or 0 for r in responses) / total, 2)
        }

    def _get_response_time_stats(self, start: datetime, end: datetime) -> Dict:
        """Get response time statistics"""
        return self._get_performance_metrics(start, end)

    def _get_top_issues(self, start: datetime, end: datetime, limit: int = 10) -> List[Dict]:
        """Get top issues by frequency"""
        categories = self.db.query(
            Inquiry.classified_category,
            func.count(Inquiry.id).label('count')
        ).filter(
            and_(
                Inquiry.created_at >= start,
                Inquiry.created_at < end
            )
        ).group_by(
            Inquiry.classified_category
        ).order_by(
            func.count(Inquiry.id).desc()
        ).limit(limit).all()

        return [
            {'category': cat, 'count': count}
            for cat, count in categories
        ]

    def _get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Get recent activity logs"""
        logs = self.db.query(ActivityLog).order_by(
            ActivityLog.created_at.desc()
        ).limit(limit).all()

        return [
            {
                'action': log.action,
                'actor': log.actor,
                'created_at': log.created_at.isoformat(),
                'status': log.status
            }
            for log in logs
        ]

    def _get_active_alerts(self) -> List[Dict]:
        """Get active alerts"""
        alerts = []

        # Check for pending human reviews
        pending_human = self._count_requires_human()
        if pending_human > 5:
            alerts.append({
                'level': 'warning',
                'message': f'{pending_human} inquiries require human review'
            })

        # Check for pending approvals
        pending_approval = self._count_pending_approval()
        if pending_approval > 10:
            alerts.append({
                'level': 'info',
                'message': f'{pending_approval} responses pending approval'
            })

        return alerts

    def _calculate_automation_rate(self, start: datetime, end: datetime) -> float:
        """Calculate automation rate"""
        total = self._count_responses(start, end)
        auto = self._count_auto_approved(start, end)

        return round((auto / total * 100), 2) if total > 0 else 0

    # Helper count methods
    def _count_inquiries(self, start: datetime, end: datetime) -> int:
        return self.db.query(Inquiry).filter(
            and_(
                Inquiry.created_at >= start,
                Inquiry.created_at < end
            )
        ).count()

    def _count_responses(self, start: datetime, end: datetime) -> int:
        return self.db.query(Response).filter(
            and_(
                Response.created_at >= start,
                Response.created_at < end
            )
        ).count()

    def _count_auto_approved(self, start: datetime, end: datetime) -> int:
        return self.db.query(Response).filter(
            and_(
                Response.created_at >= start,
                Response.created_at < end,
                Response.auto_approved == True
            )
        ).count()

    def _count_pending_inquiries(self) -> int:
        return self.db.query(Inquiry).filter(
            Inquiry.status == 'pending'
        ).count()

    def _count_pending_approval(self) -> int:
        return self.db.query(Response).filter(
            Response.status.in_(['pending_approval', 'draft'])
        ).count()

    def _count_requires_human(self) -> int:
        return self.db.query(Inquiry).filter(
            Inquiry.requires_human == True,
            Inquiry.status != 'processed'
        ).count()
