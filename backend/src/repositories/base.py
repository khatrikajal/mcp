"""
Base Repository Implementation

Provides abstract base classes for the repository pattern with
SQLAlchemy integration. Includes common CRUD operations and
query building capabilities.
"""
from abc import abstractmethod
from typing import Generic, TypeVar, Optional, List, Type, Any, Dict, Callable
from datetime import datetime

from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import IntegrityError

from backend.src.core.interfaces import IRepository
from backend.src.db.models import Base

T = TypeVar('T', bound=Base)


class BaseRepository(IRepository[T, int], Generic[T]):
    """
    Base Repository with SQLAlchemy implementation.

    Provides common CRUD operations and query building capabilities
    for all domain entities.
    """

    def __init__(self, session: Session, model_class: Type[T]):
        self._session = session
        self._model_class = model_class

    @property
    def session(self) -> Session:
        return self._session

    def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve an entity by its primary key."""
        return self._session.query(self._model_class).filter(
            self._model_class.id == id
        ).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve all entities with pagination."""
        return self._session.query(self._model_class).offset(skip).limit(limit).all()

    def add(self, entity: T) -> T:
        """Add a new entity and return it with generated ID."""
        try:
            self._session.add(entity)
            self._session.flush()
            self._session.refresh(entity)
            return entity
        except IntegrityError as e:
            self._session.rollback()
            raise RepositoryError(f"Failed to add entity: {str(e)}")

    def add_many(self, entities: List[T]) -> List[T]:
        """Add multiple entities in a batch."""
        try:
            self._session.add_all(entities)
            self._session.flush()
            for entity in entities:
                self._session.refresh(entity)
            return entities
        except IntegrityError as e:
            self._session.rollback()
            raise RepositoryError(f"Failed to add entities: {str(e)}")

    def update(self, entity: T) -> T:
        """Update an existing entity."""
        try:
            merged = self._session.merge(entity)
            self._session.flush()
            return merged
        except IntegrityError as e:
            self._session.rollback()
            raise RepositoryError(f"Failed to update entity: {str(e)}")

    def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        entity = self.get_by_id(id)
        if entity:
            self._session.delete(entity)
            self._session.flush()
            return True
        return False

    def delete_entity(self, entity: T) -> None:
        """Delete a specific entity instance."""
        self._session.delete(entity)
        self._session.flush()

    def exists(self, id: int) -> bool:
        """Check if an entity with the given ID exists."""
        return self._session.query(
            self._session.query(self._model_class).filter(
                self._model_class.id == id
            ).exists()
        ).scalar()

    def count(self) -> int:
        """Get total count of entities."""
        return self._session.query(self._model_class).count()

    def find_by(self, **kwargs) -> List[T]:
        """Find entities by attribute values."""
        query = self._session.query(self._model_class)
        for key, value in kwargs.items():
            if hasattr(self._model_class, key):
                query = query.filter(getattr(self._model_class, key) == value)
        return query.all()

    def find_one_by(self, **kwargs) -> Optional[T]:
        """Find a single entity by attribute values."""
        query = self._session.query(self._model_class)
        for key, value in kwargs.items():
            if hasattr(self._model_class, key):
                query = query.filter(getattr(self._model_class, key) == value)
        return query.first()

    def query(self) -> Query:
        """Get a new query builder for this model."""
        return self._session.query(self._model_class)


class ScopedRepository(BaseRepository[T], Generic[T]):
    """
    Repository with organization and user scoping.

    Automatically applies organization/user filters to ensure
    multi-tenant data isolation.
    """

    def __init__(
        self,
        session: Session,
        model_class: Type[T],
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ):
        super().__init__(session, model_class)
        self._user_id = user_id
        self._organization_id = organization_id

    def _apply_scope(self, query: Query) -> Query:
        """Apply user and organization scope to query."""
        if self._organization_id and hasattr(self._model_class, 'organization_id'):
            query = query.filter(
                self._model_class.organization_id == self._organization_id
            )
        if self._user_id and hasattr(self._model_class, 'user_id'):
            query = query.filter(
                self._model_class.user_id == self._user_id
            )
        return query

    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID within scope."""
        query = self._session.query(self._model_class).filter(
            self._model_class.id == id
        )
        return self._apply_scope(query).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities within scope."""
        query = self._apply_scope(self._session.query(self._model_class))
        return query.offset(skip).limit(limit).all()

    def count(self) -> int:
        """Count entities within scope."""
        query = self._apply_scope(self._session.query(self._model_class))
        return query.count()


class RepositoryError(Exception):
    """Repository operation error."""
    pass


class EntityNotFoundError(RepositoryError):
    """Entity not found in repository."""

    def __init__(self, entity_type: str, entity_id: Any):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID {entity_id} not found")


class DuplicateEntityError(RepositoryError):
    """Duplicate entity error."""

    def __init__(self, entity_type: str, field: str, value: Any):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"{entity_type} with {field}='{value}' already exists")
