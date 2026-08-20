"""
Audit Service

Comprehensive audit logging for security, compliance, and analytics.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from backend.src.db.models import (
    AuditLog,
    AnalyticsEvent,
    SecurityEventType,
    ThreatLevel,
)

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for audit logging and analytics tracking.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== Audit Logging ====================

    def log_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        action: Optional[str] = None,
        threat_level: ThreatLevel = ThreatLevel.NONE,
        description: Optional[str] = None,
        request_data: Optional[Dict] = None,
        response_status: Optional[int] = None,
        error_message: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> AuditLog:
        """
        Log a security/audit event.

        Args:
            event_type: Type of security event
            user_id: User performing the action
            organization_id: Organization context
            ip_address: Client IP
            user_agent: Client user agent
            session_id: Session identifier
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            action: Action performed
            threat_level: Severity level
            description: Human-readable description
            request_data: Sanitized request data
            response_status: HTTP response status
            error_message: Error message if any
            endpoint: API endpoint
            method: HTTP method
            duration_ms: Request duration

        Returns:
            Created AuditLog entry
        """
        # Sanitize request data to remove sensitive info
        sanitized_data = self._sanitize_request_data(request_data) if request_data else {}

        log_entry = AuditLog(
            event_type=event_type,
            user_id=user_id,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            threat_level=threat_level,
            description=description,
            request_data=sanitized_data,
            response_status=response_status,
            error_message=error_message,
            endpoint=endpoint,
            method=method,
            duration_ms=duration_ms,
        )

        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)

        # Log high-severity events to application logger as well
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            logger.warning(
                f"Security Event [{threat_level.value}]: {event_type.value} - {description}"
            )

        return log_entry

    def _sanitize_request_data(self, data: Dict) -> Dict:
        """
        Remove sensitive information from request data.

        Args:
            data: Raw request data

        Returns:
            Sanitized data
        """
        sensitive_keys = {
            'password', 'token', 'api_key', 'secret', 'authorization',
            'cookie', 'session', 'credit_card', 'ssn', 'cvv'
        }

        def sanitize_recursive(obj):
            if isinstance(obj, dict):
                return {
                    k: '[REDACTED]' if k.lower() in sensitive_keys else sanitize_recursive(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [sanitize_recursive(item) for item in obj]
            return obj

        return sanitize_recursive(data)

    # ==================== Log Queries ====================

    def get_user_activity(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[SecurityEventType]] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.

        Args:
            user_id: User ID
            start_date: Start of date range
            end_date: End of date range
            event_types: Filter by event types
            limit: Maximum results

        Returns:
            List of AuditLog entries
        """
        query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        if event_types:
            query = query.filter(AuditLog.event_type.in_(event_types))

        return query.order_by(desc(AuditLog.created_at)).limit(limit).all()

    def get_security_alerts(
        self,
        organization_id: Optional[int] = None,
        min_threat_level: ThreatLevel = ThreatLevel.MEDIUM,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get recent security alerts.

        Args:
            organization_id: Filter by organization
            min_threat_level: Minimum threat level
            hours: Lookback period in hours
            limit: Maximum results

        Returns:
            List of AuditLog entries
        """
        threat_levels = [ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        level_idx = threat_levels.index(min_threat_level) if min_threat_level in threat_levels else 0
        relevant_levels = threat_levels[level_idx:]

        query = self.db.query(AuditLog).filter(
            AuditLog.threat_level.in_(relevant_levels),
            AuditLog.created_at >= datetime.utcnow() - timedelta(hours=hours)
        )

        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)

        return query.order_by(desc(AuditLog.created_at)).limit(limit).all()

    def get_failed_logins(
        self,
        hours: int = 24,
        min_count: int = 3
    ) -> List[Dict]:
        """
        Get suspicious login patterns.

        Args:
            hours: Lookback period
            min_count: Minimum failed attempts to flag

        Returns:
            List of suspicious patterns
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        results = self.db.query(
            AuditLog.ip_address,
            func.count(AuditLog.id).label('attempt_count')
        ).filter(
            AuditLog.event_type == SecurityEventType.LOGIN_FAILURE,
            AuditLog.created_at >= cutoff
        ).group_by(
            AuditLog.ip_address
        ).having(
            func.count(AuditLog.id) >= min_count
        ).all()

        return [
            {"ip_address": r[0], "attempt_count": r[1]}
            for r in results
        ]

    # ==================== Analytics Events ====================

    def track_event(
        self,
        organization_id: int,
        event_category: str,
        event_name: str,
        user_id: Optional[int] = None,
        agent_id: Optional[int] = None,
        properties: Optional[Dict] = None,
        value: Optional[float] = None
    ) -> AnalyticsEvent:
        """
        Track an analytics event.

        Args:
            organization_id: Organization context
            event_category: Event category (chat, tool, meeting, etc.)
            event_name: Specific event name
            user_id: User if applicable
            agent_id: Agent if applicable
            properties: Additional event properties
            value: Numeric value if applicable

        Returns:
            Created AnalyticsEvent
        """
        event = AnalyticsEvent(
            organization_id=organization_id,
            user_id=user_id,
            agent_id=agent_id,
            event_category=event_category,
            event_name=event_name,
            properties=properties or {},
            value=value,
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    # ==================== Analytics Queries ====================

    def get_organization_metrics(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for an organization.

        Args:
            organization_id: Organization ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dict with aggregated metrics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Event counts by category
        category_counts = self.db.query(
            AnalyticsEvent.event_category,
            func.count(AnalyticsEvent.id)
        ).filter(
            AnalyticsEvent.organization_id == organization_id,
            AnalyticsEvent.created_at >= start_date,
            AnalyticsEvent.created_at <= end_date
        ).group_by(
            AnalyticsEvent.event_category
        ).all()

        # Active users
        active_users = self.db.query(
            func.count(func.distinct(AnalyticsEvent.user_id))
        ).filter(
            AnalyticsEvent.organization_id == organization_id,
            AnalyticsEvent.created_at >= start_date,
            AnalyticsEvent.created_at <= end_date
        ).scalar()

        # Most used agents
        from backend.src.db.models import Agent
        agent_usage = self.db.query(
            Agent.name,
            func.count(AnalyticsEvent.id).label('usage_count')
        ).join(
            AnalyticsEvent, AnalyticsEvent.agent_id == Agent.id
        ).filter(
            AnalyticsEvent.organization_id == organization_id,
            AnalyticsEvent.created_at >= start_date,
            AnalyticsEvent.created_at <= end_date
        ).group_by(
            Agent.name
        ).order_by(
            desc('usage_count')
        ).limit(10).all()

        return {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "events_by_category": {cat: count for cat, count in category_counts},
            "active_users": active_users or 0,
            "top_agents": [{"name": name, "usage": count} for name, count in agent_usage],
        }

    def get_tool_usage_stats(
        self,
        organization_id: int,
        days: int = 30
    ) -> List[Dict]:
        """
        Get tool usage statistics.

        Args:
            organization_id: Organization ID
            days: Lookback period

        Returns:
            List of tool usage stats
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        results = self.db.query(
            func.json_extract(AnalyticsEvent.properties, '$.tool_name').label('tool_name'),
            func.count(AnalyticsEvent.id).label('execution_count'),
            func.sum(
                func.case(
                    (func.json_extract(AnalyticsEvent.properties, '$.success') == True, 1),
                    else_=0
                )
            ).label('success_count')
        ).filter(
            AnalyticsEvent.organization_id == organization_id,
            AnalyticsEvent.event_category == 'tool',
            AnalyticsEvent.event_name == 'tool_executed',
            AnalyticsEvent.created_at >= cutoff
        ).group_by(
            'tool_name'
        ).all()

        return [
            {
                "tool_name": r[0],
                "execution_count": r[1],
                "success_count": r[2] or 0,
                "success_rate": (r[2] or 0) / r[1] if r[1] > 0 else 0
            }
            for r in results if r[0]
        ]

    def get_daily_activity(
        self,
        organization_id: int,
        days: int = 30
    ) -> List[Dict]:
        """
        Get daily activity counts.

        Args:
            organization_id: Organization ID
            days: Number of days

        Returns:
            List of daily counts
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        results = self.db.query(
            func.date(AnalyticsEvent.created_at).label('date'),
            func.count(AnalyticsEvent.id).label('event_count'),
            func.count(func.distinct(AnalyticsEvent.user_id)).label('unique_users')
        ).filter(
            AnalyticsEvent.organization_id == organization_id,
            AnalyticsEvent.created_at >= cutoff
        ).group_by(
            func.date(AnalyticsEvent.created_at)
        ).order_by(
            'date'
        ).all()

        return [
            {
                "date": str(r[0]),
                "event_count": r[1],
                "unique_users": r[2]
            }
            for r in results
        ]
