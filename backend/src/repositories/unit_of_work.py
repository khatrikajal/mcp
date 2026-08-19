"""
Unit of Work Implementation

Provides transaction management across multiple repositories,
ensuring atomic operations and data consistency.
"""
from typing import Optional
from contextlib import contextmanager

from sqlalchemy.orm import Session

from backend.src.core.interfaces import IUnitOfWork
from backend.src.db.connection import SessionLocal
from backend.src.repositories.delegation_repository import DelegationRepository


class UnitOfWork(IUnitOfWork):
    """
    Unit of Work implementation with SQLAlchemy.

    Manages database transactions and provides access to repositories.
    Ensures all changes within a unit of work are committed or
    rolled back atomically.

    Usage:
        with UnitOfWork() as uow:
            delegation = uow.delegations.get_by_id(1)
            delegation.status = DelegationStatus.APPROVED
            uow.commit()
    """

    def __init__(
        self,
        session: Optional[Session] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ):
        self._session = session
        self._owns_session = session is None
        self._user_id = user_id
        self._organization_id = organization_id

        # Repository instances (lazy loaded)
        self._delegations: Optional[DelegationRepository] = None

    def __enter__(self) -> 'UnitOfWork':
        if self._owns_session:
            self._session = SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        if self._owns_session and self._session:
            self._session.close()

    @property
    def session(self) -> Session:
        """Get the current session."""
        if not self._session:
            raise RuntimeError("UnitOfWork must be used as context manager")
        return self._session

    @property
    def delegations(self) -> DelegationRepository:
        """Get the delegations repository."""
        if self._delegations is None:
            self._delegations = DelegationRepository(
                self.session,
                user_id=self._user_id,
                organization_id=self._organization_id
            )
        return self._delegations

    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self._session.commit()
        except Exception:
            self.rollback()
            raise

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session:
            self._session.rollback()

    def flush(self) -> None:
        """Flush pending changes to the database."""
        self._session.flush()


class ScopedUnitOfWork(UnitOfWork):
    """
    Unit of Work with automatic user/organization scoping.

    Use this when you need all repository queries to be
    automatically filtered by user and organization.
    """

    @classmethod
    def for_user(
        cls,
        user_id: int,
        organization_id: int,
        session: Optional[Session] = None
    ) -> 'ScopedUnitOfWork':
        """Create a scoped unit of work for a specific user."""
        return cls(
            session=session,
            user_id=user_id,
            organization_id=organization_id
        )


@contextmanager
def unit_of_work(
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None
):
    """
    Context manager for unit of work operations.

    Usage:
        with unit_of_work(user_id=1, org_id=1) as uow:
            delegations = uow.delegations.get_pending()
            uow.commit()
    """
    uow = UnitOfWork(user_id=user_id, organization_id=organization_id)
    try:
        with uow:
            yield uow
    except Exception:
        raise
