"""
Delegation Repository

Provides data access operations for MeetingDelegation entities
with specialized queries for delegation management.
"""
from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from backend.src.repositories.base import ScopedRepository, EntityNotFoundError
from backend.src.db.models import MeetingDelegation, DelegationStatus, MeetingImportance


class DelegationRepository(ScopedRepository[MeetingDelegation]):
    """
    Repository for MeetingDelegation entities.

    Provides specialized queries for delegation management including
    filtering by status, importance, and time windows.
    """

    def __init__(
        self,
        session: Session,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ):
        super().__init__(session, MeetingDelegation, user_id, organization_id)

    def get_by_meeting_id(self, meeting_id: str) -> Optional[MeetingDelegation]:
        """Get delegation by external meeting ID."""
        query = self.query().filter(MeetingDelegation.meeting_id == meeting_id)
        return self._apply_scope(query).first()

    def get_pending(self) -> List[MeetingDelegation]:
        """Get all pending delegations awaiting approval."""
        query = self.query().filter(
            MeetingDelegation.status == DelegationStatus.PENDING
        ).order_by(MeetingDelegation.meeting_start_time.asc())
        return self._apply_scope(query).all()

    def get_upcoming(self, minutes_ahead: int = 60) -> List[MeetingDelegation]:
        """
        Get delegations for meetings starting within the time window.

        Args:
            minutes_ahead: Number of minutes to look ahead

        Returns:
            List of upcoming delegations
        """
        now = datetime.utcnow()
        cutoff = now + timedelta(minutes=minutes_ahead)

        query = self.query().filter(
            and_(
                MeetingDelegation.meeting_start_time >= now,
                MeetingDelegation.meeting_start_time <= cutoff,
                MeetingDelegation.status.in_([
                    DelegationStatus.PENDING,
                    DelegationStatus.APPROVED
                ])
            )
        ).order_by(MeetingDelegation.meeting_start_time.asc())

        return self._apply_scope(query).all()

    def get_ready_to_join(self, join_before_minutes: int = 5) -> List[MeetingDelegation]:
        """
        Get approved delegations ready to join.

        Returns delegations that are approved, not yet joined,
        and within the join window.
        """
        now = datetime.utcnow()
        join_window = now + timedelta(minutes=join_before_minutes)
        past_buffer = now - timedelta(minutes=5)

        query = self.query().filter(
            and_(
                MeetingDelegation.status == DelegationStatus.APPROVED,
                MeetingDelegation.meeting_start_time <= join_window,
                MeetingDelegation.meeting_start_time >= past_buffer,
                MeetingDelegation.notetaker_id.is_(None)
            )
        )

        return self._apply_scope(query).all()

    def get_completed_without_report(self) -> List[MeetingDelegation]:
        """Get delegations that have joined but not yet completed."""
        now = datetime.utcnow()

        query = self.query().filter(
            and_(
                MeetingDelegation.status == DelegationStatus.JOINED,
                MeetingDelegation.meeting_end_time <= now,
                MeetingDelegation.notetaker_id.isnot(None)
            )
        )

        return self._apply_scope(query).all()

    def get_by_status(
        self,
        status: DelegationStatus,
        skip: int = 0,
        limit: int = 50
    ) -> List[MeetingDelegation]:
        """Get delegations by status with pagination."""
        query = self.query().filter(
            MeetingDelegation.status == status
        ).order_by(
            MeetingDelegation.meeting_start_time.desc()
        ).offset(skip).limit(limit)

        return self._apply_scope(query).all()

    def get_by_importance(
        self,
        importance: MeetingImportance,
        skip: int = 0,
        limit: int = 50
    ) -> List[MeetingDelegation]:
        """Get delegations by importance level."""
        query = self.query().filter(
            MeetingDelegation.importance == importance
        ).order_by(
            MeetingDelegation.meeting_start_time.desc()
        ).offset(skip).limit(limit)

        return self._apply_scope(query).all()

    def get_completed(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[MeetingDelegation]:
        """Get completed delegations with optional date range."""
        query = self.query().filter(
            MeetingDelegation.status == DelegationStatus.COMPLETED
        )

        if start_date:
            query = query.filter(MeetingDelegation.completed_at >= start_date)
        if end_date:
            query = query.filter(MeetingDelegation.completed_at <= end_date)

        return self._apply_scope(query).order_by(
            MeetingDelegation.completed_at.desc()
        ).limit(limit).all()

    def get_statistics(self) -> dict:
        """
        Get aggregated statistics for delegations.

        Returns:
            Dictionary with counts by status
        """
        query = self._apply_scope(self.query())

        total = query.count()
        pending = query.filter(
            MeetingDelegation.status == DelegationStatus.PENDING
        ).count()
        approved = query.filter(
            MeetingDelegation.status == DelegationStatus.APPROVED
        ).count()
        completed = query.filter(
            MeetingDelegation.status == DelegationStatus.COMPLETED
        ).count()
        failed = query.filter(
            MeetingDelegation.status == DelegationStatus.FAILED
        ).count()

        return {
            'total': total,
            'pending': pending,
            'approved': approved,
            'completed': completed,
            'failed': failed,
        }

    def get_with_unsent_reports(self) -> List[MeetingDelegation]:
        """Get completed delegations with reports not yet sent."""
        query = self.query().filter(
            and_(
                MeetingDelegation.status == DelegationStatus.COMPLETED,
                MeetingDelegation.report.isnot(None),
                MeetingDelegation.report_sent == False
            )
        )

        return self._apply_scope(query).all()

    def mark_report_sent(self, delegation_id: int) -> MeetingDelegation:
        """Mark a delegation's report as sent."""
        delegation = self.get_by_id(delegation_id)
        if not delegation:
            raise EntityNotFoundError('MeetingDelegation', delegation_id)

        delegation.report_sent = True
        delegation.report_sent_at = datetime.utcnow()
        delegation.updated_at = datetime.utcnow()

        return self.update(delegation)

    def search(
        self,
        query_text: Optional[str] = None,
        status: Optional[DelegationStatus] = None,
        importance: Optional[MeetingImportance] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[MeetingDelegation]:
        """
        Advanced search with multiple filters.

        Args:
            query_text: Search in title and description
            status: Filter by status
            importance: Filter by importance
            start_date: Meeting start date from
            end_date: Meeting start date to
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of matching delegations
        """
        query = self._apply_scope(self.query())

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.filter(
                or_(
                    MeetingDelegation.meeting_title.ilike(search_pattern),
                    MeetingDelegation.meeting_description.ilike(search_pattern)
                )
            )

        if status:
            query = query.filter(MeetingDelegation.status == status)

        if importance:
            query = query.filter(MeetingDelegation.importance == importance)

        if start_date:
            query = query.filter(MeetingDelegation.meeting_start_time >= start_date)

        if end_date:
            query = query.filter(MeetingDelegation.meeting_start_time <= end_date)

        return query.order_by(
            MeetingDelegation.meeting_start_time.desc()
        ).offset(skip).limit(limit).all()
