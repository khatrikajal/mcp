"""
Backend Configuration

All environment variables and settings are centralized here.
"""
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env from backend directory or project root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# =============================================================================
# MCP Server Configuration
# =============================================================================
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# =============================================================================
# API Server Configuration
# =============================================================================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8001))

# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:post123@localhost:5432/AI_Workforce")

# PostgreSQL Pool Settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", 30))

# =============================================================================
# Authentication (JWT)
# =============================================================================
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# =============================================================================
# External API Keys
# =============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NYLAS_API_KEY = os.getenv("NYLAS_API_KEY")
NYLAS_GRANT_ID = os.getenv("NYLAS_GRANT_ID")

# =============================================================================
# Logging
# =============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =============================================================================
# Redis Configuration (for rate limiting and caching)
# =============================================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# =============================================================================
# Security Configuration
# =============================================================================
# Rate Limiting (requests per minute)
RATE_LIMIT_DEFAULT = int(os.getenv("RATE_LIMIT_DEFAULT", 60))
RATE_LIMIT_CHAT = int(os.getenv("RATE_LIMIT_CHAT", 30))
RATE_LIMIT_EMAIL = int(os.getenv("RATE_LIMIT_EMAIL", 10))
RATE_LIMIT_CALENDAR = int(os.getenv("RATE_LIMIT_CALENDAR", 20))
RATE_LIMIT_MEETING = int(os.getenv("RATE_LIMIT_MEETING", 5))

# Session Settings
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", 60))
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", 5))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", 15))

# IP Blocking
IP_WHITELIST = os.getenv("IP_WHITELIST", "").split(",") if os.getenv("IP_WHITELIST") else []
IP_BLACKLIST = os.getenv("IP_BLACKLIST", "").split(",") if os.getenv("IP_BLACKLIST") else []

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

# =============================================================================
# Monitoring & Observability
# =============================================================================
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
