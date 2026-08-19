"""
Repository Layer

Provides data access abstractions following the Repository pattern.
"""
from backend.src.repositories.base import (
    BaseRepository,
    ScopedRepository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
)
from backend.src.repositories.delegation_repository import DelegationRepository
from backend.src.repositories.unit_of_work import UnitOfWork, ScopedUnitOfWork, unit_of_work

__all__ = [
    # Base classes
    "BaseRepository",
    "ScopedRepository",
    # Exceptions
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    # Repositories
    "DelegationRepository",
    # Unit of Work
    "UnitOfWork",
    "ScopedUnitOfWork",
    "unit_of_work",
]
