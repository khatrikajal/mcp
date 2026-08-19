"""
Structured Logging Infrastructure

Provides structured logging with correlation ID support for
distributed tracing, JSON formatting for log aggregation,
and context-aware logging.
"""
import logging
import json
import sys
import traceback
import uuid
from datetime import datetime
from typing import Optional, Any, Dict
from contextvars import ContextVar
from functools import wraps

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_context_var: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


def get_correlation_id() -> str:
    """Get current correlation ID or generate a new one."""
    cid = correlation_id_var.get()
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    """Set the correlation ID for the current context."""
    correlation_id_var.set(cid)


def set_request_context(**kwargs) -> None:
    """Set additional request context for logging."""
    current = request_context_var.get()
    request_context_var.set({**current, **kwargs})


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log
    aggregation systems like ELK, Splunk, or CloudWatch.
    """

    def __init__(self, include_traceback: bool = True):
        super().__init__()
        self.include_traceback = include_traceback

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': correlation_id_var.get(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add request context
        ctx = request_context_var.get()
        if ctx:
            log_entry['context'] = ctx

        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Add exception info
        if record.exc_info and self.include_traceback:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info) if record.exc_info[0] else None
            }

        return json.dumps(log_entry, default=str)


class ContextLogger:
    """
    Context-aware logger wrapper.

    Provides structured logging with automatic correlation ID
    and context injection.
    """

    def __init__(self, name: str, correlation_id: Optional[str] = None):
        self._logger = logging.getLogger(name)
        self._correlation_id = correlation_id
        self._extra_context: Dict[str, Any] = {}

    def _log(self, level: int, message: str, exc_info=None, **kwargs):
        """Internal logging method with context injection."""
        # Set correlation ID if provided
        if self._correlation_id:
            set_correlation_id(self._correlation_id)

        # Create log record with extra fields
        extra = {'extra_fields': {**self._extra_context, **kwargs}}
        self._logger.log(level, message, exc_info=exc_info, extra=extra)

    def info(self, message: str, **kwargs) -> None:
        """Log an informational message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log an error message with optional exception."""
        exc_info = exception if exception else None
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log a critical message."""
        exc_info = exception if exception else None
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)

    def with_correlation_id(self, correlation_id: str) -> 'ContextLogger':
        """Create a new logger with a specific correlation ID."""
        logger = ContextLogger(self._logger.name, correlation_id)
        logger._extra_context = self._extra_context.copy()
        return logger

    def with_context(self, **kwargs) -> 'ContextLogger':
        """Create a new logger with additional context."""
        logger = ContextLogger(self._logger.name, self._correlation_id)
        logger._extra_context = {**self._extra_context, **kwargs}
        return logger

    def bind(self, **kwargs) -> 'ContextLogger':
        """Bind additional context to the logger."""
        self._extra_context.update(kwargs)
        return self


def get_logger(name: str) -> ContextLogger:
    """Get a context-aware logger instance."""
    return ContextLogger(name)


def setup_logging(
    level: str = 'INFO',
    json_output: bool = True,
    include_traceback: bool = True
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output logs in JSON format
        include_traceback: If True, include full traceback in error logs
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Set formatter
    if json_output:
        handler.setFormatter(StructuredFormatter(include_traceback))
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
        ))

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def log_execution_time(logger: Optional[ContextLogger] = None):
    """
    Decorator to log function execution time.

    Usage:
        @log_execution_time()
        async def my_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = datetime.utcnow()
            _logger = logger or get_logger(func.__module__)
            try:
                result = await func(*args, **kwargs)
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                _logger.debug(
                    f"{func.__name__} completed",
                    function=func.__name__,
                    duration_ms=round(elapsed, 2)
                )
                return result
            except Exception as e:
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                _logger.error(
                    f"{func.__name__} failed",
                    exception=e,
                    function=func.__name__,
                    duration_ms=round(elapsed, 2)
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = datetime.utcnow()
            _logger = logger or get_logger(func.__module__)
            try:
                result = func(*args, **kwargs)
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                _logger.debug(
                    f"{func.__name__} completed",
                    function=func.__name__,
                    duration_ms=round(elapsed, 2)
                )
                return result
            except Exception as e:
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                _logger.error(
                    f"{func.__name__} failed",
                    exception=e,
                    function=func.__name__,
                    duration_ms=round(elapsed, 2)
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
