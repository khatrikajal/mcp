"""
Custom exceptions and error handling utilities.

Provides consistent error responses across the application.
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message, status.HTTP_404_NOT_FOUND)
        self.resource = resource
        self.resource_id = resource_id


class UnauthorizedError(AppException):
    """Unauthorized access error."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppException):
    """Forbidden access error."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class ConflictError(AppException):
    """Resource conflict error (e.g., duplicate)."""

    def __init__(self, message: str):
        super().__init__(message, status.HTTP_409_CONFLICT)


class RateLimitError(AppException):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


def raise_not_found(resource: str, resource_id: Any = None) -> None:
    """Raise HTTPException for not found resource."""
    message = f"{resource} not found"
    if resource_id:
        message = f"{resource} with id '{resource_id}' not found"
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def raise_forbidden(message: str = "Access denied") -> None:
    """Raise HTTPException for forbidden access."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


def raise_unauthorized(message: str = "Unauthorized") -> None:
    """Raise HTTPException for unauthorized access."""
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


def raise_bad_request(message: str) -> None:
    """Raise HTTPException for bad request."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def raise_conflict(message: str) -> None:
    """Raise HTTPException for conflict."""
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
