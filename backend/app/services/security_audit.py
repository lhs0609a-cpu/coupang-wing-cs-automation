"""
Security and Audit Logging Service
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from loguru import logger
import hashlib
import json

from ..models.user import AuditLog, User


class SecurityAuditService:
    """
    Comprehensive audit logging and security monitoring
    """

    def __init__(self, db: Session):
        self.db = db
        self.security_events = []  # In-memory for real-time monitoring

    def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = 'success'
    ) -> AuditLog:
        """
        Log a user action

        Args:
            user_id: User ID performing the action
            action: Action performed (e.g., 'inquiry.create', 'response.approve')
            resource_type: Type of resource (e.g., 'inquiry', 'response', 'template')
            resource_id: ID of the resource
            details: Additional details
            ip_address: User's IP address
            user_agent: User's browser/client info
            status: Action status ('success', 'failed', 'blocked')

        Returns:
            Created audit log entry
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )

        self.db.add(audit_log)
        self.db.commit()

        # Add to real-time monitoring if security-relevant
        if self._is_security_event(action, status):
            self.security_events.append({
                'user_id': user_id,
                'action': action,
                'timestamp': datetime.utcnow(),
                'status': status,
                'ip_address': ip_address
            })

        logger.info(f"Audit log: User {user_id} - {action} on {resource_type}:{resource_id}")
        return audit_log

    def _is_security_event(self, action: str, status: str) -> bool:
        """Determine if an action is security-relevant"""
        security_actions = [
            'user.login',
            'user.logout',
            'user.login_failed',
            'user.password_change',
            'user.role_change',
            'permission.grant',
            'permission.revoke',
            'data.export',
            'data.delete',
            'settings.change'
        ]

        return action in security_actions or status in ['failed', 'blocked']

    def get_user_activity(
        self,
        user_id: int,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get activity history for a specific user

        Args:
            user_id: User ID
            days: Number of days to look back
            limit: Maximum number of records

        Returns:
            List of activity records
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = self.db.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_date
            )
        ).order_by(
            desc(AuditLog.timestamp)
        ).limit(limit).all()

        return [
            {
                'id': log.id,
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'details': log.details,
                'timestamp': log.timestamp.isoformat(),
                'ip_address': log.ip_address
            }
            for log in logs
        ]

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get audit trail for a specific resource

        Args:
            resource_type: Resource type
            resource_id: Resource ID
            limit: Maximum number of records

        Returns:
            Audit trail
        """
        logs = self.db.query(AuditLog).filter(
            and_(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id
            )
        ).order_by(
            desc(AuditLog.timestamp)
        ).limit(limit).all()

        # Include user information
        activity = []
        for log in logs:
            user = self.db.query(User).filter(User.id == log.user_id).first()

            activity.append({
                'id': log.id,
                'action': log.action,
                'user_id': log.user_id,
                'user_name': user.username if user else 'Unknown',
                'details': log.details,
                'timestamp': log.timestamp.isoformat(),
                'ip_address': log.ip_address
            })

        return activity

    def detect_suspicious_activity(self, hours: int = 24) -> List[Dict]:
        """
        Detect suspicious activity patterns

        Args:
            hours: Time window to analyze

        Returns:
            List of suspicious activities
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        suspicious = []

        # Pattern 1: Multiple failed login attempts
        failed_logins = self.db.query(
            AuditLog.user_id,
            AuditLog.ip_address,
            func.count(AuditLog.id).label('attempt_count')
        ).filter(
            and_(
                AuditLog.action == 'user.login_failed',
                AuditLog.timestamp >= start_time
            )
        ).group_by(
            AuditLog.user_id,
            AuditLog.ip_address
        ).having(
            func.count(AuditLog.id) >= 5  # 5+ failed attempts
        ).all()

        for user_id, ip_address, count in failed_logins:
            suspicious.append({
                'type': 'multiple_failed_logins',
                'severity': 'high',
                'user_id': user_id,
                'ip_address': ip_address,
                'count': count,
                'description': f'{count} failed login attempts from {ip_address}'
            })

        # Pattern 2: Unusual data export volume
        exports = self.db.query(
            AuditLog.user_id,
            func.count(AuditLog.id).label('export_count')
        ).filter(
            and_(
                AuditLog.action == 'data.export',
                AuditLog.timestamp >= start_time
            )
        ).group_by(
            AuditLog.user_id
        ).having(
            func.count(AuditLog.id) >= 10  # 10+ exports
        ).all()

        for user_id, count in exports:
            user = self.db.query(User).filter(User.id == user_id).first()
            suspicious.append({
                'type': 'excessive_data_export',
                'severity': 'medium',
                'user_id': user_id,
                'user_name': user.username if user else 'Unknown',
                'count': count,
                'description': f'User performed {count} data exports'
            })

        # Pattern 3: Access from multiple IPs in short time
        multi_ip_users = self.db.query(
            AuditLog.user_id,
            func.count(func.distinct(AuditLog.ip_address)).label('ip_count')
        ).filter(
            AuditLog.timestamp >= start_time
        ).group_by(
            AuditLog.user_id
        ).having(
            func.count(func.distinct(AuditLog.ip_address)) >= 5  # 5+ different IPs
        ).all()

        for user_id, ip_count in multi_ip_users:
            user = self.db.query(User).filter(User.id == user_id).first()
            suspicious.append({
                'type': 'multiple_ip_addresses',
                'severity': 'medium',
                'user_id': user_id,
                'user_name': user.username if user else 'Unknown',
                'ip_count': ip_count,
                'description': f'User accessed from {ip_count} different IP addresses'
            })

        # Pattern 4: After-hours activity
        after_hours = self.db.query(AuditLog).filter(
            and_(
                AuditLog.timestamp >= start_time,
                or_(
                    func.extract('hour', AuditLog.timestamp) < 6,  # Before 6 AM
                    func.extract('hour', AuditLog.timestamp) >= 22  # After 10 PM
                )
            )
        ).all()

        if len(after_hours) > 20:
            suspicious.append({
                'type': 'after_hours_activity',
                'severity': 'low',
                'count': len(after_hours),
                'description': f'{len(after_hours)} actions performed outside business hours'
            })

        logger.info(f"Detected {len(suspicious)} suspicious activity patterns")
        return suspicious

    def get_security_dashboard(self, days: int = 7) -> Dict:
        """
        Get security dashboard metrics

        Args:
            days: Number of days to analyze

        Returns:
            Security dashboard data
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Total actions
        total_actions = self.db.query(func.count(AuditLog.id)).filter(
            AuditLog.timestamp >= start_date
        ).scalar()

        # Failed logins
        failed_logins = self.db.query(func.count(AuditLog.id)).filter(
            and_(
                AuditLog.action == 'user.login_failed',
                AuditLog.timestamp >= start_date
            )
        ).scalar()

        # Successful logins
        successful_logins = self.db.query(func.count(AuditLog.id)).filter(
            and_(
                AuditLog.action == 'user.login',
                AuditLog.timestamp >= start_date
            )
        ).scalar()

        # Data exports
        data_exports = self.db.query(func.count(AuditLog.id)).filter(
            and_(
                AuditLog.action == 'data.export',
                AuditLog.timestamp >= start_date
            )
        ).scalar()

        # Permission changes
        permission_changes = self.db.query(func.count(AuditLog.id)).filter(
            and_(
                AuditLog.action.in_(['permission.grant', 'permission.revoke', 'user.role_change']),
                AuditLog.timestamp >= start_date
            )
        ).scalar()

        # Active users
        active_users = self.db.query(
            func.count(func.distinct(AuditLog.user_id))
        ).filter(
            AuditLog.timestamp >= start_date
        ).scalar()

        # Most active users
        top_users = self.db.query(
            AuditLog.user_id,
            func.count(AuditLog.id).label('action_count')
        ).filter(
            AuditLog.timestamp >= start_date
        ).group_by(
            AuditLog.user_id
        ).order_by(
            desc('action_count')
        ).limit(5).all()

        top_users_list = []
        for user_id, count in top_users:
            user = self.db.query(User).filter(User.id == user_id).first()
            top_users_list.append({
                'user_id': user_id,
                'user_name': user.username if user else 'Unknown',
                'action_count': count
            })

        return {
            'period_days': days,
            'total_actions': total_actions,
            'failed_logins': failed_logins,
            'successful_logins': successful_logins,
            'login_success_rate': round(
                successful_logins / (successful_logins + failed_logins),
                2
            ) if (successful_logins + failed_logins) > 0 else 0,
            'data_exports': data_exports,
            'permission_changes': permission_changes,
            'active_users': active_users,
            'top_users': top_users_list,
            'suspicious_activities': len(self.detect_suspicious_activity(hours=days * 24))
        }

    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Generate compliance audit report

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report
        """
        logs = self.db.query(AuditLog).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            )
        ).all()

        # Categorize actions
        categorized = {
            'data_access': [],
            'data_modification': [],
            'data_export': [],
            'user_management': [],
            'permission_changes': [],
            'other': []
        }

        for log in logs:
            if 'export' in log.action:
                categorized['data_export'].append(log)
            elif 'create' in log.action or 'update' in log.action or 'delete' in log.action:
                categorized['data_modification'].append(log)
            elif 'read' in log.action or 'view' in log.action:
                categorized['data_access'].append(log)
            elif 'user' in log.action:
                categorized['user_management'].append(log)
            elif 'permission' in log.action or 'role' in log.action:
                categorized['permission_changes'].append(log)
            else:
                categorized['other'].append(log)

        # Generate report hash for integrity
        report_data = json.dumps({
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_events': len(logs)
        }, sort_keys=True)

        report_hash = hashlib.sha256(report_data.encode()).hexdigest()

        return {
            'report_id': f"compliance_{int(datetime.utcnow().timestamp())}",
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_events': len(logs),
            'events_by_category': {
                category: len(events)
                for category, events in categorized.items()
            },
            'data_exports': len(categorized['data_export']),
            'data_modifications': len(categorized['data_modification']),
            'permission_changes': len(categorized['permission_changes']),
            'unique_users': len(set(log.user_id for log in logs)),
            'report_hash': report_hash,
            'generated_at': datetime.utcnow().isoformat()
        }

    def search_audit_logs(
        self,
        filters: Dict,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search audit logs with filters

        Args:
            filters: Search filters (user_id, action, resource_type, date_from, date_to, etc.)
            limit: Maximum results

        Returns:
            Matching audit logs
        """
        query = self.db.query(AuditLog)

        # Apply filters
        if 'user_id' in filters:
            query = query.filter(AuditLog.user_id == filters['user_id'])

        if 'action' in filters:
            query = query.filter(AuditLog.action.like(f"%{filters['action']}%"))

        if 'resource_type' in filters:
            query = query.filter(AuditLog.resource_type == filters['resource_type'])

        if 'resource_id' in filters:
            query = query.filter(AuditLog.resource_id == filters['resource_id'])

        if 'date_from' in filters:
            query = query.filter(AuditLog.timestamp >= filters['date_from'])

        if 'date_to' in filters:
            query = query.filter(AuditLog.timestamp <= filters['date_to'])

        if 'ip_address' in filters:
            query = query.filter(AuditLog.ip_address == filters['ip_address'])

        # Execute query
        logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()

        # Format results
        results = []
        for log in logs:
            user = self.db.query(User).filter(User.id == log.user_id).first()
            results.append({
                'id': log.id,
                'user_id': log.user_id,
                'user_name': user.username if user else 'Unknown',
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'details': log.details,
                'timestamp': log.timestamp.isoformat(),
                'ip_address': log.ip_address,
                'user_agent': log.user_agent
            })

        return results


# Add missing import for 'or_'
from sqlalchemy import or_
