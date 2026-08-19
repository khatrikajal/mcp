"""
Core Interfaces and Protocols

This module defines abstract base classes and protocols that establish
contracts for the application's core components. Following SOLID principles,
particularly Interface Segregation and Dependency Inversion.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any, Dict
from datetime import datetime

# Generic type variables for repository pattern
T = TypeVar('T')
ID = TypeVar('ID')


class IRepository(ABC, Generic[T, ID]):
    """
    Generic Repository Interface.

    Provides a standard contract for data access operations following
    the Repository pattern. All concrete repositories must implement
    this interface.
    """

    @abstractmethod
    def get_by_id(self, id: ID) -> Optional[T]:
        """Retrieve an entity by its unique identifier."""
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve all entities with pagination."""
        pass

    @abstractmethod
    def add(self, entity: T) -> T:
        """Add a new entity to the repository."""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    def delete(self, id: ID) -> bool:
        """Delete an entity by its identifier."""
        pass

    @abstractmethod
    def exists(self, id: ID) -> bool:
        """Check if an entity exists."""
        pass


class IUnitOfWork(ABC):
    """
    Unit of Work Interface.

    Manages transactions across multiple repositories, ensuring
    atomic operations and maintaining data consistency.
    """

    @abstractmethod
    def __enter__(self) -> 'IUnitOfWork':
        """Enter the unit of work context."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the unit of work context."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit all changes in the current transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback all changes in the current transaction."""
        pass


class ICacheService(ABC):
    """
    Cache Service Interface.

    Provides caching capabilities for frequently accessed data
    to improve performance and reduce database load.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Store a value in cache with optional TTL."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove a value from cache."""
        pass

    @abstractmethod
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        pass


class IEventPublisher(ABC):
    """
    Event Publisher Interface.

    Enables event-driven architecture by publishing domain events
    for asynchronous processing.
    """

    @abstractmethod
    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event to the event bus."""
        pass

    @abstractmethod
    async def publish_batch(self, events: List[Dict[str, Any]]) -> None:
        """Publish multiple events in a batch."""
        pass


class ILogger(ABC):
    """
    Structured Logger Interface.

    Provides structured logging with correlation ID support
    for distributed tracing.
    """

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log an informational message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log an error message with optional exception."""
        pass

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        pass

    @abstractmethod
    def with_correlation_id(self, correlation_id: str) -> 'ILogger':
        """Create a logger instance with a specific correlation ID."""
        pass


class IHealthCheck(ABC):
    """
    Health Check Interface.

    Provides health status for service dependencies.
    """

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the component.

        Returns:
            Dictionary containing:
            - status: 'healthy', 'degraded', or 'unhealthy'
            - latency_ms: Response time in milliseconds
            - details: Additional information
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the health check component."""
        pass


class INotificationService(ABC):
    """
    Notification Service Interface.

    Handles sending notifications through various channels.
    """

    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """Send an email notification."""
        pass

    @abstractmethod
    async def send_push(
        self,
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> bool:
        """Send a push notification."""
        pass


class IAuditLogger(ABC):
    """
    Audit Logger Interface.

    Records audit trail for compliance and security monitoring.
    """

    @abstractmethod
    def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Any,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log an auditable action."""
        pass

    @abstractmethod
    def get_audit_trail(
        self,
        resource_type: str,
        resource_id: Any,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Retrieve audit trail for a resource."""
        pass
