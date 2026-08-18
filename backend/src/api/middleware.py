"""
API Middleware for security, logging, and rate limiting.

Provides:
- Security headers middleware
- Rate limiting middleware
- Request logging middleware
- Error handling middleware
"""
from typing import Callable, Optional
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import uuid

from backend.src.core.security import (
    rate_limiter,
    SECURITY_HEADERS,
    check_injection
)
from backend.src.core.exceptions import AppException, RateLimitError

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Limits requests per IP and per user.
    """

    def __init__(
        self,
        app: FastAPI,
        requests_per_minute: int = 100,
        requests_per_minute_authenticated: int = 300
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_minute_authenticated = requests_per_minute_authenticated

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifier
        client_ip = self._get_client_ip(request)

        # Check if authenticated (look for auth header)
        auth_header = request.headers.get("Authorization")
        is_authenticated = auth_header and auth_header.startswith("Bearer ")

        # Determine rate limit
        max_requests = (
            self.requests_per_minute_authenticated
            if is_authenticated
            else self.requests_per_minute
        )

        # Check rate limit
        rate_key = f"ip:{client_ip}"
        if not rate_limiter.is_allowed(rate_key, max_requests, 60):
            remaining = rate_limiter.get_remaining(rate_key, max_requests, 60)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": 60
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": str(remaining),
                    "Retry-After": "60"
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        remaining = rate_limiter.get_remaining(rate_key, max_requests, 60)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request, handling proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing information."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - Started"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"{response.status_code} ({duration:.3f}s)"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Error: {str(e)} ({duration:.3f}s)"
            )
            raise


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate input for potential injection attacks."""

    # Paths to skip validation (e.g., file uploads)
    SKIP_PATHS = {"/api/v1/upload", "/health"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Check query parameters
        for key, value in request.query_params.items():
            if check_injection(value):
                logger.warning(
                    f"Potential injection in query param '{key}': {value[:100]}"
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid characters in request"}
                )

        return await call_next(request)


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for AppException and general errors."""

    if isinstance(exc, AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                **exc.details
            }
        )

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    # Log unexpected errors
    logger.exception(f"Unexpected error: {exc}")

    # Don't leak internal error details
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"}
    )


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the application.

    Args:
        app: FastAPI application instance
    """
    # CORS - configure for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
    )

    # Add middleware in order (last added runs first)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(InputValidationMiddleware)

    # Add exception handlers
    app.add_exception_handler(AppException, exception_handler)
    app.add_exception_handler(Exception, exception_handler)
