"""
Security utilities for input validation, sanitization, and protection.

Provides:
- Input sanitization
- SQL injection protection
- XSS prevention
- Rate limiting helpers
- Security headers
"""
import re
import html
from typing import Any, Dict, List, Optional
from functools import wraps
import time
from collections import defaultdict
import threading


# Patterns that might indicate injection attempts
INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",  # SQL keywords
    r"(--|;|\/\*|\*\/)",  # SQL comments
    r"(<script|javascript:|on\w+\s*=)",  # XSS patterns
    r"(\{\{|\}\}|\$\{)",  # Template injection
]

# Compiled regex for performance
INJECTION_REGEX = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def sanitize_string(value: str, max_length: int = 10000) -> str:
    """
    Sanitize a string input.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)

    # Trim to max length
    value = value[:max_length]

    # Strip leading/trailing whitespace
    value = value.strip()

    # Escape HTML entities for XSS prevention
    value = html.escape(value)

    return value


def sanitize_html(value: str) -> str:
    """
    Remove all HTML tags from string.

    Args:
        value: String to sanitize

    Returns:
        String with HTML removed
    """
    if not isinstance(value, str):
        return str(value)

    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', value)

    # Escape remaining special characters
    clean = html.escape(clean)

    return clean


def check_injection(value: str) -> bool:
    """
    Check if string contains potential injection patterns.

    Args:
        value: String to check

    Returns:
        True if suspicious patterns found
    """
    if not isinstance(value, str):
        return False

    return bool(INJECTION_REGEX.search(value))


def sanitize_dict(data: Dict[str, Any], max_string_length: int = 10000) -> Dict[str, Any]:
    """
    Recursively sanitize all string values in a dictionary.

    Args:
        data: Dictionary to sanitize
        max_string_length: Maximum length for string values

    Returns:
        Sanitized dictionary
    """
    result = {}

    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_string(value, max_string_length)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, max_string_length)
        elif isinstance(value, list):
            result[key] = sanitize_list(value, max_string_length)
        else:
            result[key] = value

    return result


def sanitize_list(data: List[Any], max_string_length: int = 10000) -> List[Any]:
    """
    Recursively sanitize all string values in a list.

    Args:
        data: List to sanitize
        max_string_length: Maximum length for string values

    Returns:
        Sanitized list
    """
    result = []

    for value in data:
        if isinstance(value, str):
            result.append(sanitize_string(value, max_string_length))
        elif isinstance(value, dict):
            result.append(sanitize_dict(value, max_string_length))
        elif isinstance(value, list):
            result.append(sanitize_list(value, max_string_length))
        else:
            result.append(value)

    return result


class RateLimiter:
    """
    Simple in-memory rate limiter.

    For production, use Redis-based rate limiting.
    """

    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier (e.g., user_id, ip_address)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if request is allowed
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        with self.lock:
            # Clean old requests
            self.requests[key] = [
                t for t in self.requests[key]
                if t > window_start
            ]

            # Check limit
            if len(self.requests[key]) >= max_requests:
                return False

            # Record request
            self.requests[key].append(current_time)
            return True

    def get_remaining(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> int:
        """
        Get remaining requests in current window.

        Args:
            key: Unique identifier
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        with self.lock:
            recent_requests = [
                t for t in self.requests[key]
                if t > window_start
            ]
            return max(0, max_requests - len(recent_requests))

    def clear(self, key: str) -> None:
        """Clear rate limit data for a key."""
        with self.lock:
            if key in self.requests:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


# Security headers for responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if len(password) > 128:
        return False, "Password must be less than 128 characters"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    return True, ""


def validate_email_format(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email to validate

    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
