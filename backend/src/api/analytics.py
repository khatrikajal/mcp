"""
Analytics API Endpoints

Provides endpoints for analytics dashboard, metrics, and reporting.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.src.db.connection import get_db
from backend.src.db.models import User, Organization, SecurityEventType, ThreatLevel
from backend.src.api.auth_utils import get_current_user
from backend.src.services.audit_service import AuditService
from backend.src.services.rbac_service import RBACService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ==================== Response Models ====================

class DateRangeMetrics(BaseModel):
    start: str
    end: str


class OrganizationMetrics(BaseModel):
    date_range: DateRangeMetrics
    events_by_category: dict
    active_users: int
    top_agents: List[dict]


class DailyActivityItem(BaseModel):
    date: str
    event_count: int
    unique_users: int


class ToolUsageStat(BaseModel):
    tool_name: str
    execution_count: int
    success_count: int
    success_rate: float


class SecurityAlertItem(BaseModel):
    id: int
    event_type: str
    threat_level: str
    description: Optional[str]
    ip_address: Optional[str]
    user_id: Optional[int]
    created_at: datetime


class FailedLoginPattern(BaseModel):
    ip_address: str
    attempt_count: int


class DashboardSummary(BaseModel):
    total_agents: int
    total_conversations: int
    total_messages: int
    active_users_today: int
    pending_approvals: int
    meetings_this_week: int
    interviews_this_week: int
    security_alerts_24h: int


# ==================== Endpoints ====================

@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard summary metrics for the organization.

    Requires permission: analytics:view
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "analytics:view"):
        raise HTTPException(status_code=403, detail="Permission denied: analytics:view required")

    from backend.src.db.models import Agent, Conversation, Message, ApprovalRequest, MeetingDelegation, InterviewSession, AuditLog
    from sqlalchemy import func, and_

    org_id = current_user.organization_id
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    day_ago = datetime.utcnow() - timedelta(hours=24)

    # Count agents in organization
    total_agents = db.query(Agent).filter(Agent.organization_id == org_id).count()

    # Count conversations
    total_conversations = db.query(Conversation).join(User).filter(
        User.organization_id == org_id
    ).count()

    # Count messages
    total_messages = db.query(Message).join(Conversation).join(User).filter(
        User.organization_id == org_id
    ).count()

    # Active users today
    active_users_today = db.query(func.count(func.distinct(AuditLog.user_id))).filter(
        and_(
            AuditLog.organization_id == org_id,
            AuditLog.created_at >= today
        )
    ).scalar() or 0

    # Pending approvals
    pending_approvals = db.query(ApprovalRequest).join(Agent).filter(
        and_(
            Agent.organization_id == org_id,
            ApprovalRequest.status == "pending"
        )
    ).count()

    # Meetings this week
    meetings_this_week = db.query(MeetingDelegation).filter(
        and_(
            MeetingDelegation.organization_id == org_id,
            MeetingDelegation.meeting_start_time >= week_ago
        )
    ).count()

    # Interviews this week
    interviews_this_week = db.query(InterviewSession).filter(
        and_(
            InterviewSession.organization_id == org_id,
            InterviewSession.scheduled_time >= week_ago
        )
    ).count()

    # Security alerts in last 24 hours
    security_alerts_24h = db.query(AuditLog).filter(
        and_(
            AuditLog.organization_id == org_id,
            AuditLog.threat_level.in_([ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]),
            AuditLog.created_at >= day_ago
        )
    ).count()

    return DashboardSummary(
        total_agents=total_agents,
        total_conversations=total_conversations,
        total_messages=total_messages,
        active_users_today=active_users_today,
        pending_approvals=pending_approvals,
        meetings_this_week=meetings_this_week,
        interviews_this_week=interviews_this_week,
        security_alerts_24h=security_alerts_24h
    )


@router.get("/metrics")
def get_organization_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated metrics for the organization.

    Requires permission: analytics:view
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "analytics:view"):
        raise HTTPException(status_code=403, detail="Permission denied: analytics:view required")

    audit_service = AuditService(db)
    return audit_service.get_organization_metrics(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/daily-activity", response_model=List[DailyActivityItem])
def get_daily_activity(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get daily activity counts for the organization.

    Requires permission: analytics:view
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "analytics:view"):
        raise HTTPException(status_code=403, detail="Permission denied: analytics:view required")

    audit_service = AuditService(db)
    return audit_service.get_daily_activity(
        organization_id=current_user.organization_id,
        days=days
    )


@router.get("/tool-usage", response_model=List[ToolUsageStat])
def get_tool_usage_stats(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get tool usage statistics.

    Requires permission: analytics:view
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "analytics:view"):
        raise HTTPException(status_code=403, detail="Permission denied: analytics:view required")

    audit_service = AuditService(db)
    return audit_service.get_tool_usage_stats(
        organization_id=current_user.organization_id,
        days=days
    )


@router.get("/security-alerts", response_model=List[SecurityAlertItem])
def get_security_alerts(
    hours: int = Query(default=24, ge=1, le=168),
    min_threat_level: str = Query(default="medium"),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent security alerts.

    Requires permission: admin:view_audit_logs
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:view_audit_logs"):
        raise HTTPException(status_code=403, detail="Permission denied: admin:view_audit_logs required")

    # Convert string to ThreatLevel enum
    try:
        threat_level = ThreatLevel(min_threat_level.lower())
    except ValueError:
        threat_level = ThreatLevel.MEDIUM

    audit_service = AuditService(db)
    alerts = audit_service.get_security_alerts(
        organization_id=current_user.organization_id,
        min_threat_level=threat_level,
        hours=hours,
        limit=limit
    )

    return [
        SecurityAlertItem(
            id=alert.id,
            event_type=alert.event_type.value,
            threat_level=alert.threat_level.value,
            description=alert.description,
            ip_address=alert.ip_address,
            user_id=alert.user_id,
            created_at=alert.created_at
        )
        for alert in alerts
    ]


@router.get("/failed-logins", response_model=List[FailedLoginPattern])
def get_failed_login_patterns(
    hours: int = Query(default=24, ge=1, le=168),
    min_count: int = Query(default=3, ge=2, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get suspicious failed login patterns.

    Requires permission: admin:view_audit_logs
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:view_audit_logs"):
        raise HTTPException(status_code=403, detail="Permission denied: admin:view_audit_logs required")

    audit_service = AuditService(db)
    return audit_service.get_failed_logins(hours=hours, min_count=min_count)


@router.get("/user-activity/{user_id}")
def get_user_activity(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_types: Optional[List[str]] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get activity logs for a specific user.

    Requires permission: admin:view_audit_logs
    """
    rbac = RBACService(db)

    # Users can view their own activity, admins can view anyone's
    if current_user.id != user_id and not rbac.has_permission(current_user.id, "admin:view_audit_logs"):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Verify user is in same organization
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user or target_user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert event type strings to enums
    event_type_enums = None
    if event_types:
        event_type_enums = []
        for et in event_types:
            try:
                event_type_enums.append(SecurityEventType(et))
            except ValueError:
                pass

    audit_service = AuditService(db)
    logs = audit_service.get_user_activity(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        event_types=event_type_enums,
        limit=limit
    )

    return [
        {
            "id": log.id,
            "event_type": log.event_type.value,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "description": log.description,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]


@router.get("/export")
def export_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = Query(default="json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export analytics data.

    Requires permission: analytics:export
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "analytics:export"):
        raise HTTPException(status_code=403, detail="Permission denied: analytics:export required")

    audit_service = AuditService(db)

    # Get all relevant data
    metrics = audit_service.get_organization_metrics(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date
    )

    daily_activity = audit_service.get_daily_activity(
        organization_id=current_user.organization_id,
        days=30
    )

    tool_usage = audit_service.get_tool_usage_stats(
        organization_id=current_user.organization_id,
        days=30
    )

    export_data = {
        "organization_id": current_user.organization_id,
        "export_date": datetime.utcnow().isoformat(),
        "date_range": metrics.get("date_range", {}),
        "summary": {
            "events_by_category": metrics.get("events_by_category", {}),
            "active_users": metrics.get("active_users", 0),
            "top_agents": metrics.get("top_agents", [])
        },
        "daily_activity": daily_activity,
        "tool_usage": tool_usage
    }

    if format == "csv":
        # Convert to CSV format
        import csv
        import io
        from fastapi.responses import StreamingResponse

        output = io.StringIO()

        # Daily activity CSV
        if daily_activity:
            writer = csv.DictWriter(output, fieldnames=["date", "event_count", "unique_users"])
            writer.writeheader()
            for row in daily_activity:
                writer.writerow(row)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics_export.csv"}
        )

    return export_data


@router.post("/track-event")
def track_analytics_event(
    event_category: str,
    event_name: str,
    properties: Optional[dict] = None,
    value: Optional[float] = None,
    agent_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track a custom analytics event.

    For internal use by other services.
    """
    audit_service = AuditService(db)

    event = audit_service.track_event(
        organization_id=current_user.organization_id,
        event_category=event_category,
        event_name=event_name,
        user_id=current_user.id,
        agent_id=agent_id,
        properties=properties,
        value=value
    )

    return {
        "id": event.id,
        "event_category": event.event_category,
        "event_name": event.event_name,
        "created_at": event.created_at.isoformat()
    }
