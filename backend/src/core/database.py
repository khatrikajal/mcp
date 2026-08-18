"""
Database utilities and resource helpers.

Provides:
- Common database operations
- Resource fetching with ownership checks
- Transaction helpers
"""
from typing import Any, Callable, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import Column

from backend.src.core.exceptions import NotFoundError, ForbiddenError

T = TypeVar('T')


class ResourceFetcher(Generic[T]):
    """
    Generic resource fetcher with ownership checks.

    Reduces code duplication for common patterns like:
    - Fetching a resource by ID
    - Checking user/organization ownership
    - Raising 404 if not found
    """

    def __init__(
        self,
        db: Session,
        model: Type[T],
        resource_name: str
    ):
        self.db = db
        self.model = model
        self.resource_name = resource_name

    def get_by_id(self, resource_id: int) -> Optional[T]:
        """
        Get resource by ID without any ownership check.

        Args:
            resource_id: Resource ID

        Returns:
            Resource or None
        """
        return self.db.query(self.model).filter(
            self.model.id == resource_id
        ).first()

    def get_or_404(self, resource_id: int) -> T:
        """
        Get resource by ID or raise 404.

        Args:
            resource_id: Resource ID

        Returns:
            Resource

        Raises:
            NotFoundError: If resource not found
        """
        resource = self.get_by_id(resource_id)
        if not resource:
            raise NotFoundError(self.resource_name, resource_id)
        return resource

    def get_for_user(
        self,
        resource_id: int,
        user_id: int,
        user_field: str = "user_id"
    ) -> T:
        """
        Get resource by ID with user ownership check.

        Args:
            resource_id: Resource ID
            user_id: User ID to check ownership
            user_field: Field name for user ID on model

        Returns:
            Resource

        Raises:
            NotFoundError: If resource not found
            ForbiddenError: If user doesn't own resource
        """
        resource = self.get_or_404(resource_id)

        if getattr(resource, user_field, None) != user_id:
            raise ForbiddenError(f"Access denied to {self.resource_name}")

        return resource

    def get_for_organization(
        self,
        resource_id: int,
        organization_id: int,
        org_field: str = "organization_id"
    ) -> T:
        """
        Get resource by ID with organization ownership check.

        Args:
            resource_id: Resource ID
            organization_id: Organization ID to check ownership
            org_field: Field name for organization ID on model

        Returns:
            Resource

        Raises:
            NotFoundError: If resource not found
            ForbiddenError: If organization doesn't own resource
        """
        resource = self.get_or_404(resource_id)

        if getattr(resource, org_field, None) != organization_id:
            raise ForbiddenError(f"Access denied to {self.resource_name}")

        return resource

    def get_for_user_and_org(
        self,
        resource_id: int,
        user_id: int,
        organization_id: int
    ) -> T:
        """
        Get resource with both user and organization check.

        Args:
            resource_id: Resource ID
            user_id: User ID
            organization_id: Organization ID

        Returns:
            Resource

        Raises:
            NotFoundError: If resource not found
            ForbiddenError: If access denied
        """
        resource = self.db.query(self.model).filter(
            self.model.id == resource_id,
            self.model.organization_id == organization_id
        ).first()

        if not resource:
            raise NotFoundError(self.resource_name, resource_id)

        return resource

    def list_for_organization(
        self,
        organization_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[T]:
        """
        List resources for an organization.

        Args:
            organization_id: Organization ID
            limit: Maximum results
            offset: Results offset

        Returns:
            List of resources
        """
        return self.db.query(self.model).filter(
            self.model.organization_id == organization_id
        ).limit(limit).offset(offset).all()

    def list_for_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[T]:
        """
        List resources for a user.

        Args:
            user_id: User ID
            limit: Maximum results
            offset: Results offset

        Returns:
            List of resources
        """
        return self.db.query(self.model).filter(
            self.model.user_id == user_id
        ).limit(limit).offset(offset).all()


def create_resource_fetcher(
    db: Session,
    model: Type[T],
    resource_name: str
) -> ResourceFetcher[T]:
    """
    Factory function for creating ResourceFetcher instances.

    Args:
        db: Database session
        model: SQLAlchemy model class
        resource_name: Human-readable resource name

    Returns:
        ResourceFetcher instance
    """
    return ResourceFetcher(db, model, resource_name)


class TransactionManager:
    """
    Context manager for database transactions.

    Usage:
        with TransactionManager(db) as tx:
            tx.add(new_record)
            # Auto-commits on exit, rolls back on exception
    """

    def __init__(self, db: Session):
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
            return False

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return False
