"""
Delegation API Endpoints

Handles AI meeting delegation operations including:
- Listing delegations (upcoming, pending, completed)
- Approving/rejecting delegations
- Viewing delegation reports
- Manual delegation triggers
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.src.db.connection import get_db
from backend.src.db.models import User, MeetingDelegation, DelegationStatus, MeetingImportance
from backend.src.api.auth_utils import get_current_active_user
from backend.src.services.delegation_service import DelegationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/delegations", tags=["delegations"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ActionItemResponse(BaseModel):
    """Action item from meeting report."""
    task: str
    assignee: str
    status: str = "pending"


class DelegationResponse(BaseModel):
    """Response model for meeting delegation."""
    id: int
    user_id: int
    organization_id: int
    meeting_id: str
    meeting_title: str
    meeting_description: Optional[str]
    meeting_start_time: str
    meeting_end_time: str
    meeting_location: Optional[str]
    meeting_organizer: Optional[str]
    meeting_attendees: List[dict]
    importance: str
    importance_score: int
    importance_reasons: List[str]
    status: str
    auto_approved: bool
    requires_approval: bool
    notetaker_id: Optional[str]
    notetaker_joined_at: Optional[str]
    notetaker_left_at: Optional[str]
    introduction_script: Optional[str]
    report_summary: Optional[str]
    action_items: Optional[List[dict]]
    decisions: Optional[List[str]]
    report_sent: bool
    report_sent_at: Optional[str]
    error_message: Optional[str]
    created_at: str
    updated_at: str
    approved_at: Optional[str]
    completed_at: Optional[str]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, delegation: MeetingDelegation):
        return cls(
            id=delegation.id,
            user_id=delegation.user_id,
            organization_id=delegation.organization_id,
            meeting_id=delegation.meeting_id,
            meeting_title=delegation.meeting_title,
            meeting_description=delegation.meeting_description,
            meeting_start_time=delegation.meeting_start_time.isoformat(),
            meeting_end_time=delegation.meeting_end_time.isoformat(),
            meeting_location=delegation.meeting_location,
            meeting_organizer=delegation.meeting_organizer,
            meeting_attendees=delegation.meeting_attendees or [],
            importance=delegation.importance.value,
            importance_score=delegation.importance_score,
            importance_reasons=delegation.importance_reasons or [],
            status=delegation.status.value,
            auto_approved=delegation.auto_approved,
            requires_approval=delegation.requires_approval,
            notetaker_id=delegation.notetaker_id,
            notetaker_joined_at=delegation.notetaker_joined_at.isoformat() if delegation.notetaker_joined_at else None,
            notetaker_left_at=delegation.notetaker_left_at.isoformat() if delegation.notetaker_left_at else None,
            introduction_script=delegation.introduction_script,
            report_summary=delegation.report_summary,
            action_items=delegation.action_items,
            decisions=delegation.decisions,
            report_sent=delegation.report_sent,
            report_sent_at=delegation.report_sent_at.isoformat() if delegation.report_sent_at else None,
            error_message=delegation.error_message,
            created_at=delegation.created_at.isoformat(),
            updated_at=delegation.updated_at.isoformat(),
            approved_at=delegation.approved_at.isoformat() if delegation.approved_at else None,
            completed_at=delegation.completed_at.isoformat() if delegation.completed_at else None,
        )


class DelegationReportResponse(BaseModel):
    """Full report response for a delegation."""
    id: int
    meeting_title: str
    meeting_start_time: str
    meeting_end_time: str
    meeting_attendees: List[dict]
    transcript: Optional[str]
    report: Optional[str]
    report_summary: Optional[str]
    action_items: Optional[List[dict]]
    decisions: Optional[List[str]]
    report_sent: bool

    class Config:
        from_attributes = True


class DelegationStatsResponse(BaseModel):
    """Statistics about user's delegations."""
    total: int
    pending: int
    approved: int
    completed: int
    failed: int


class ProcessMeetingsRequest(BaseModel):
    """Request to manually process upcoming meetings."""
    look_ahead_hours: int = Field(default=24, ge=1, le=168)


class RejectDelegationRequest(BaseModel):
    """Request to reject a delegation."""
    reason: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("", response_model=List[DelegationResponse])
def list_delegations(
    status_filter: Optional[str] = Query(None, alias="status"),
    importance_filter: Optional[str] = Query(None, alias="importance"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List all delegations for the current user.

    Query parameters:
    - status: Filter by status (pending, approved, completed, failed, etc.)
    - importance: Filter by importance (critical, high, medium, low)
    - limit: Maximum number of results (default: 50)
    - offset: Pagination offset
    """
    query = db.query(MeetingDelegation).filter(
        MeetingDelegation.user_id == current_user.id,
        MeetingDelegation.organization_id == current_user.organization_id,
    )

    # Apply status filter
    if status_filter:
        try:
            status_enum = DelegationStatus(status_filter.lower())
            query = query.filter(MeetingDelegation.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )

    # Apply importance filter
    if importance_filter:
        try:
            importance_enum = MeetingImportance(importance_filter.lower())
            query = query.filter(MeetingDelegation.importance == importance_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid importance: {importance_filter}"
            )

    # Order by meeting start time (upcoming first)
    delegations = query.order_by(
        MeetingDelegation.meeting_start_time.desc()
    ).offset(offset).limit(limit).all()

    return [DelegationResponse.from_orm(d) for d in delegations]


@router.get("/upcoming", response_model=List[DelegationResponse])
def list_upcoming_delegations(
    minutes_ahead: int = Query(60, ge=5, le=1440),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List delegations for meetings starting within the specified time window.

    Parameters:
    - minutes_ahead: How far ahead to look (default: 60 minutes)
    """
    delegation_service = DelegationService(db)
    delegations = delegation_service.get_upcoming_delegations(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        minutes_ahead=minutes_ahead,
    )

    return [DelegationResponse.from_orm(d) for d in delegations]


@router.get("/pending", response_model=List[DelegationResponse])
def list_pending_delegations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all delegations pending user approval."""
    delegation_service = DelegationService(db)
    delegations = delegation_service.get_pending_delegations(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )

    return [DelegationResponse.from_orm(d) for d in delegations]


@router.get("/stats", response_model=DelegationStatsResponse)
def get_delegation_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get statistics about the user's delegations."""
    base_query = db.query(MeetingDelegation).filter(
        MeetingDelegation.user_id == current_user.id,
        MeetingDelegation.organization_id == current_user.organization_id,
    )

    total = base_query.count()
    pending = base_query.filter(
        MeetingDelegation.status == DelegationStatus.PENDING
    ).count()
    approved = base_query.filter(
        MeetingDelegation.status == DelegationStatus.APPROVED
    ).count()
    completed = base_query.filter(
        MeetingDelegation.status == DelegationStatus.COMPLETED
    ).count()
    failed = base_query.filter(
        MeetingDelegation.status == DelegationStatus.FAILED
    ).count()

    return DelegationStatsResponse(
        total=total,
        pending=pending,
        approved=approved,
        completed=completed,
        failed=failed,
    )


@router.get("/{delegation_id}", response_model=DelegationResponse)
def get_delegation(
    delegation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific delegation by ID."""
    delegation = db.query(MeetingDelegation).filter(
        MeetingDelegation.id == delegation_id,
        MeetingDelegation.user_id == current_user.id,
    ).first()

    if not delegation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delegation not found"
        )

    return DelegationResponse.from_orm(delegation)


@router.get("/{delegation_id}/report", response_model=DelegationReportResponse)
def get_delegation_report(
    delegation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the full report for a completed delegation."""
    delegation = db.query(MeetingDelegation).filter(
        MeetingDelegation.id == delegation_id,
        MeetingDelegation.user_id == current_user.id,
    ).first()

    if not delegation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delegation not found"
        )

    if delegation.status != DelegationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report not available - delegation not completed"
        )

    return DelegationReportResponse(
        id=delegation.id,
        meeting_title=delegation.meeting_title,
        meeting_start_time=delegation.meeting_start_time.isoformat(),
        meeting_end_time=delegation.meeting_end_time.isoformat(),
        meeting_attendees=delegation.meeting_attendees or [],
        transcript=delegation.transcript,
        report=delegation.report,
        report_summary=delegation.report_summary,
        action_items=delegation.action_items,
        decisions=delegation.decisions,
        report_sent=delegation.report_sent,
    )


@router.post("/{delegation_id}/approve", response_model=DelegationResponse)
def approve_delegation(
    delegation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Approve a pending delegation."""
    delegation_service = DelegationService(db)

    try:
        delegation = delegation_service.approve_delegation(
            delegation_id=delegation_id,
            user_id=current_user.id,
        )
        return DelegationResponse.from_orm(delegation)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{delegation_id}/reject", response_model=DelegationResponse)
def reject_delegation(
    delegation_id: int,
    reject_data: RejectDelegationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reject a pending delegation."""
    delegation_service = DelegationService(db)

    try:
        delegation = delegation_service.reject_delegation(
            delegation_id=delegation_id,
            user_id=current_user.id,
            reason=reject_data.reason,
        )
        return DelegationResponse.from_orm(delegation)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{delegation_id}/join", response_model=DelegationResponse)
def join_meeting(
    delegation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger joining a meeting for an approved delegation.

    Normally handled automatically by the cron job, but can be triggered manually.
    """
    delegation_service = DelegationService(db)

    # Verify ownership
    delegation = db.query(MeetingDelegation).filter(
        MeetingDelegation.id == delegation_id,
        MeetingDelegation.user_id == current_user.id,
    ).first()

    if not delegation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delegation not found"
        )

    try:
        delegation = delegation_service.join_meeting(delegation_id)
        return DelegationResponse.from_orm(delegation)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{delegation_id}/complete", response_model=DelegationResponse)
def complete_delegation(
    delegation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger completion (fetch transcript, generate report) for a delegation.

    Normally handled automatically by the cron job, but can be triggered manually.
    """
    delegation_service = DelegationService(db)

    # Verify ownership
    delegation = db.query(MeetingDelegation).filter(
        MeetingDelegation.id == delegation_id,
        MeetingDelegation.user_id == current_user.id,
    ).first()

    if not delegation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delegation not found"
        )

    try:
        delegation = delegation_service.complete_delegation(delegation_id)
        return DelegationResponse.from_orm(delegation)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{delegation_id}/send-report")
def send_delegation_report(
    delegation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Send the delegation report via email."""
    delegation_service = DelegationService(db)

    # Verify ownership
    delegation = db.query(MeetingDelegation).filter(
        MeetingDelegation.id == delegation_id,
        MeetingDelegation.user_id == current_user.id,
    ).first()

    if not delegation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delegation not found"
        )

    try:
        delegation_service.send_delegation_report(delegation_id)
        return {"message": "Report sent successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/process-meetings", response_model=List[DelegationResponse])
def process_upcoming_meetings(
    request: ProcessMeetingsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger processing of upcoming meetings.

    This scans the calendar for upcoming meetings and creates delegations.
    Normally handled automatically by the cron job.
    """
    delegation_service = DelegationService(db)

    delegations = delegation_service.process_upcoming_meetings(
        user=current_user,
        look_ahead_hours=request.look_ahead_hours,
    )

    return [DelegationResponse.from_orm(d) for d in delegations]


@router.delete("/{delegation_id}")
def delete_delegation(
    delegation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete a delegation.

    Only pending or rejected delegations can be deleted.
    """
    delegation = db.query(MeetingDelegation).filter(
        MeetingDelegation.id == delegation_id,
        MeetingDelegation.user_id == current_user.id,
    ).first()

    if not delegation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delegation not found"
        )

    # Only allow deletion of pending or rejected delegations
    if delegation.status not in [DelegationStatus.PENDING, DelegationStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete delegation in current status"
        )

    db.delete(delegation)
    db.commit()

    return {"message": "Delegation deleted"}
