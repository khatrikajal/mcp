"""
Dependency Injection Container

Provides a lightweight DI container for managing service dependencies.
Supports singleton, scoped, and transient lifetimes.
"""
from typing import TypeVar, Type, Optional, Callable, Any, Dict
from enum import Enum
from functools import wraps
from contextlib import contextmanager
import threading


T = TypeVar('T')


class Lifetime(Enum):
    """Service lifetime options."""
    SINGLETON = 'singleton'  # One instance for entire application
    SCOPED = 'scoped'        # One instance per request/scope
    TRANSIENT = 'transient'  # New instance every time


class ServiceDescriptor:
    """Describes a registered service."""

    def __init__(
        self,
        service_type: Type,
        implementation: Type,
        lifetime: Lifetime,
        factory: Optional[Callable] = None
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory


class Container:
    """
    Dependency Injection Container.

    Manages service registration and resolution with support for
    different lifetimes (singleton, scoped, transient).

    Usage:
        container = Container()
        container.register_singleton(IService, ConcreteService)
        container.register_transient(IRepository, ConcreteRepository)

        service = container.resolve(IService)
    """

    def __init__(self):
        self._registrations: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[int, Dict[Type, Any]] = {}
        self._lock = threading.Lock()
        self._current_scope_id: Optional[int] = None

    def register_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """
        Register a singleton service.

        Args:
            service_type: The interface/abstract type
            implementation: The concrete implementation type
            factory: Optional factory function to create the instance
        """
        impl = implementation or service_type
        self._registrations[service_type] = ServiceDescriptor(
            service_type, impl, Lifetime.SINGLETON, factory
        )
        return self

    def register_scoped(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """
        Register a scoped service (one per request/scope).
        """
        impl = implementation or service_type
        self._registrations[service_type] = ServiceDescriptor(
            service_type, impl, Lifetime.SCOPED, factory
        )
        return self

    def register_transient(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """
        Register a transient service (new instance each time).
        """
        impl = implementation or service_type
        self._registrations[service_type] = ServiceDescriptor(
            service_type, impl, Lifetime.TRANSIENT, factory
        )
        return self

    def register_instance(self, service_type: Type[T], instance: T) -> 'Container':
        """
        Register an existing instance as a singleton.
        """
        self._registrations[service_type] = ServiceDescriptor(
            service_type, type(instance), Lifetime.SINGLETON
        )
        self._singletons[service_type] = instance
        return self

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service by its type.

        Args:
            service_type: The type to resolve

        Returns:
            The service instance

        Raises:
            KeyError: If the service is not registered
        """
        if service_type not in self._registrations:
            raise KeyError(f"Service {service_type.__name__} is not registered")

        descriptor = self._registrations[service_type]

        if descriptor.lifetime == Lifetime.SINGLETON:
            return self._resolve_singleton(service_type, descriptor)
        elif descriptor.lifetime == Lifetime.SCOPED:
            return self._resolve_scoped(service_type, descriptor)
        else:
            return self._create_instance(descriptor)

    def _resolve_singleton(self, service_type: Type, descriptor: ServiceDescriptor) -> Any:
        """Resolve or create a singleton instance."""
        with self._lock:
            if service_type not in self._singletons:
                self._singletons[service_type] = self._create_instance(descriptor)
            return self._singletons[service_type]

    def _resolve_scoped(self, service_type: Type, descriptor: ServiceDescriptor) -> Any:
        """Resolve or create a scoped instance."""
        if self._current_scope_id is None:
            raise RuntimeError("No active scope. Use 'with container.scope():' to create a scope.")

        scope = self._scoped_instances.get(self._current_scope_id, {})
        if service_type not in scope:
            scope[service_type] = self._create_instance(descriptor)
            self._scoped_instances[self._current_scope_id] = scope
        return scope[service_type]

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new service instance."""
        if descriptor.factory:
            return descriptor.factory()

        # Try to resolve constructor dependencies
        import inspect
        sig = inspect.signature(descriptor.implementation.__init__)
        dependencies = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            if param.annotation != inspect.Parameter.empty:
                if param.annotation in self._registrations:
                    dependencies[param_name] = self.resolve(param.annotation)

        return descriptor.implementation(**dependencies)

    @contextmanager
    def scope(self):
        """
        Create a new scope for scoped services.

        Usage:
            with container.scope():
                service = container.resolve(IScopedService)
        """
        scope_id = id(threading.current_thread())
        self._current_scope_id = scope_id
        self._scoped_instances[scope_id] = {}
        try:
            yield self
        finally:
            del self._scoped_instances[scope_id]
            self._current_scope_id = None

    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type in self._registrations


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def configure_services(container: Container) -> None:
    """
    Configure all application services.

    This should be called at application startup to register
    all dependencies.
    """
    from backend.src.core.logging import ContextLogger, get_logger
    from backend.src.services.delegation_service import DelegationService
    from backend.src.services.calendar_service import CalendarService
    from backend.src.services.email_service import EmailService
    from backend.src.services.notetaker_service import NotetakerService

    # Register services
    container.register_singleton(CalendarService)
    container.register_singleton(EmailService)
    container.register_singleton(NotetakerService)

    # Register scoped services (one per request)
    container.register_scoped(DelegationService)


def inject(service_type: Type[T]) -> T:
    """
    Dependency injection decorator helper.

    Usage:
        @app.get("/items")
        def get_items(service: IService = Depends(inject(IService))):
            ...
    """
    def dependency():
        return get_container().resolve(service_type)
    return dependency
