"""
API Middleware for security, logging, and rate limiting.

Provides:
- Security headers middleware
- Rate limiting middleware (with Redis support)
- Request logging middleware
- Error handling middleware
- IP blocking middleware
- Prompt injection detection middleware
- Audit logging middleware
"""
from typing import Callable, Optional
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import uuid
import json

from backend.src.core.security import (
    rate_limiter,
    SECURITY_HEADERS,
    check_injection
)
from backend.src.core.exceptions import AppException, RateLimitError

logger = logging.getLogger(__name__)

# Try to import advanced security services
try:
    from backend.src.services.security_service import get_security_service
    SECURITY_SERVICE_AVAILABLE = True
except ImportError:
    SECURITY_SERVICE_AVAILABLE = False
    get_security_service = None


def get_client_ip(request: Request) -> str:
    """Get client IP from request, handling proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


class IPBlockingMiddleware(BaseHTTPMiddleware):
    """
    Check if client IP is blocked.

    Uses SecurityService for IP blocking/whitelisting.
    """

    # Paths to skip IP checking (health checks, etc.)
    SKIP_PATHS = {"/health", "/"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        if not SECURITY_SERVICE_AVAILABLE:
            return await call_next(request)

        try:
            security_service = get_security_service()
            client_ip = get_client_ip(request)

            is_allowed, reason = security_service.is_ip_allowed(client_ip)

            if not is_allowed:
                logger.warning(f"Blocked IP {client_ip}: {reason}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": "Access denied",
                        "reason": reason
                    }
                )
        except Exception as e:
            # Don't block requests if IP check fails
            logger.error(f"IP blocking check failed: {e}")

        return await call_next(request)


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
    Uses Redis if available, falls back to in-memory.
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
        client_ip = get_client_ip(request)

        # Check if authenticated (look for auth header)
        auth_header = request.headers.get("Authorization")
        is_authenticated = auth_header and auth_header.startswith("Bearer ")

        # Determine rate limit
        max_requests = (
            self.requests_per_minute_authenticated
            if is_authenticated
            else self.requests_per_minute
        )

        # Try to use SecurityService with Redis, fall back to in-memory
        is_allowed = True
        remaining = max_requests
        current = 0

        if SECURITY_SERVICE_AVAILABLE:
            try:
                security_service = get_security_service()
                rate_key = f"ip:{client_ip}"
                is_allowed, current, remaining = security_service.check_rate_limit(
                    rate_key, max_requests, 60
                )
            except Exception as e:
                logger.error(f"Redis rate limit check failed: {e}")
                # Fall back to in-memory
                rate_key = f"ip:{client_ip}"
                is_allowed = rate_limiter.is_allowed(rate_key, max_requests, 60)
                remaining = rate_limiter.get_remaining(rate_key, max_requests, 60)
        else:
            # Use in-memory rate limiter
            rate_key = f"ip:{client_ip}"
            is_allowed = rate_limiter.is_allowed(rate_key, max_requests, 60)
            remaining = rate_limiter.get_remaining(rate_key, max_requests, 60)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
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
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing information in structured format."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Get client info
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")[:100]

        # Log request (structured format)
        logger.info(json.dumps({
            "type": "request_start",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": user_agent
        }))

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log response (structured format)
            logger.info(json.dumps({
                "type": "request_complete",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms
            }))

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Log error (structured format)
            logger.error(json.dumps({
                "type": "request_error",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "duration_ms": duration_ms
            }))
            raise


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate input for potential injection attacks."""

    # Paths to skip validation (e.g., file uploads)
    SKIP_PATHS = {"/api/v1/upload", "/health", "/"}

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


class PromptInjectionMiddleware(BaseHTTPMiddleware):
    """
    Advanced prompt injection detection middleware.

    Uses SecurityService for multi-layer detection.
    Only checks POST/PUT requests to chat/conversation endpoints.
    """

    # Endpoints that process user prompts
    PROMPT_ENDPOINTS = {
        "/api/v1/conversations/",
        "/api/v1/chat",
        "/api/v1/agents/",
    }

    # Paths to skip
    SKIP_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only check POST/PUT requests
        if request.method not in ["POST", "PUT"]:
            return await call_next(request)

        # Skip certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Check if this is a prompt-processing endpoint
        is_prompt_endpoint = any(
            request.url.path.startswith(endpoint)
            for endpoint in self.PROMPT_ENDPOINTS
        )

        if not is_prompt_endpoint:
            return await call_next(request)

        if not SECURITY_SERVICE_AVAILABLE:
            return await call_next(request)

        try:
            # Read request body
            body = await request.body()
            if not body:
                return await call_next(request)

            # Parse JSON body
            try:
                data = json.loads(body.decode())
            except json.JSONDecodeError:
                return await call_next(request)

            # Check for prompt-like fields
            text_to_check = ""
            for field in ["message", "content", "prompt", "text", "query", "user_input"]:
                if field in data and isinstance(data[field], str):
                    text_to_check += data[field] + " "

            if not text_to_check.strip():
                return await call_next(request)

            # Use SecurityService for detection
            security_service = get_security_service()
            is_injection, threat_level, patterns = security_service.detect_prompt_injection(
                text_to_check,
                use_llm=False  # Don't use LLM in middleware (too slow)
            )

            if is_injection:
                client_ip = get_client_ip(request)
                logger.warning(json.dumps({
                    "type": "prompt_injection_detected",
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "threat_level": threat_level.value,
                    "patterns": patterns
                }))

                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "detail": "Request contains potentially harmful content",
                        "threat_level": threat_level.value
                    }
                )

        except Exception as e:
            # Don't block requests if injection check fails
            logger.error(f"Prompt injection check failed: {e}")

        return await call_next(request)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Audit logging middleware for security-sensitive endpoints.

    Logs all authentication, data modification, and sensitive operations.
    """

    # Endpoints that require audit logging
    AUDIT_ENDPOINTS = {
        "/api/v1/auth/": ["POST"],
        "/api/v1/agents": ["POST", "PUT", "DELETE"],
        "/api/v1/conversations": ["DELETE"],
        "/api/v1/approvals": ["POST", "PUT"],
        "/api/v1/delegations": ["POST", "PUT"],
        "/api/v1/interviews": ["POST", "PUT", "DELETE"],
        "/api/v1/security": ["POST", "PUT", "DELETE"],
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this request should be audited
        should_audit = False
        for endpoint, methods in self.AUDIT_ENDPOINTS.items():
            if request.url.path.startswith(endpoint) and request.method in methods:
                should_audit = True
                break

        if not should_audit:
            return await call_next(request)

        # Get request info before processing
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")[:500]
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])

        start_time = time.time()

        # Process request
        response = await call_next(request)

        duration_ms = int((time.time() - start_time) * 1000)

        # Log audit event (this could also be written to database)
        logger.info(json.dumps({
            "type": "audit_log",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }))

        return response


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for AppException and general errors."""

    request_id = getattr(request.state, 'request_id', 'unknown')

    if isinstance(exc, AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "request_id": request_id,
                **exc.details
            }
        )

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "request_id": request_id
            }
        )

    # Log unexpected errors (structured format)
    logger.error(json.dumps({
        "type": "unhandled_exception",
        "request_id": request_id,
        "error": str(exc),
        "error_type": type(exc).__name__
    }))

    # Don't leak internal error details
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal error occurred",
            "request_id": request_id
        }
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
    # Order: IP Blocking -> Security Headers -> Audit Logging -> Request Logging
    #        -> Rate Limiting -> Input Validation -> Prompt Injection
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AuditLoggingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(PromptInjectionMiddleware)
    app.add_middleware(IPBlockingMiddleware)

    # Add exception handlers
    app.add_exception_handler(AppException, exception_handler)
    app.add_exception_handler(Exception, exception_handler)
