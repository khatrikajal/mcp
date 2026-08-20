"""
FastAPI Application - Main Entry Point

This module configures the FastAPI application with all routers and middleware.
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import json
import sys
from datetime import datetime

from backend.src.db.connection import init_db
from backend.src.api.auth import router as auth_router
from backend.src.api.agents import router as agents_router
from backend.src.api.conversations import router as conversations_router
from backend.src.api.planning import router as planning_router
from backend.src.api.approvals import router as approvals_router
from backend.src.api.delegations import router as delegations_router
from backend.src.api.interviews import router as interviews_router
from backend.src.api.memory import router as memory_router
from backend.src.api.analytics import router as analytics_router
from backend.src.api.security import router as security_router
from backend.src.api.health import router as health_router
from backend.src.api.middleware import setup_middleware
from backend.src.core.config import API_HOST, API_PORT, LOG_LEVEL, ENVIRONMENT


class StructuredLogFormatter(logging.Formatter):
    """
    Custom log formatter that outputs JSON-structured logs.

    Useful for log aggregation services like ELK, CloudWatch, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Check if the message is already JSON
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, TypeError):
            pass

        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_logging():
    """Configure structured logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)

    if ENVIRONMENT == "production":
        # Use structured JSON format in production
        console_handler.setFormatter(StructuredLogFormatter())
    else:
        # Use human-readable format in development
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

    root_logger.addHandler(console_handler)


# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database
    logger.info(json.dumps({
        "type": "startup",
        "event": "database_init_start",
        "timestamp": datetime.utcnow().isoformat()
    }))
    init_db()
    logger.info(json.dumps({
        "type": "startup",
        "event": "database_init_complete",
        "timestamp": datetime.utcnow().isoformat()
    }))

    # Initialize RBAC permissions
    try:
        from backend.src.db.connection import get_db
        from backend.src.services.rbac_service import RBACService
        db = next(get_db())
        rbac = RBACService(db)
        rbac.initialize_permissions()
        logger.info(json.dumps({
            "type": "startup",
            "event": "rbac_init_complete",
            "timestamp": datetime.utcnow().isoformat()
        }))
    except Exception as e:
        logger.warning(f"RBAC initialization skipped: {e}")

    yield

    # Shutdown: cleanup if needed
    logger.info(json.dumps({
        "type": "shutdown",
        "event": "application_shutdown",
        "timestamp": datetime.utcnow().isoformat()
    }))


# Create FastAPI application
app = FastAPI(
    title="AI Workforce Platform API",
    description="REST API for managing AI agents, conversations, and automations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware (security headers, rate limiting, logging, CORS)
setup_middleware(app)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(planning_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(delegations_router, prefix="/api/v1")
app.include_router(interviews_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(health_router)  # Health endpoints at root level


@app.get("/")
def root():
    """Root endpoint - API info."""
    return {
        "name": "AI Workforce Platform API",
        "version": "1.0.0",
        "status": "running",
        "environment": ENVIRONMENT,
        "docs": "/docs",
        "health": "/health/detailed"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.src.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
