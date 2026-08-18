"""
FastAPI Application - Main Entry Point

This module configures the FastAPI application with all routers and middleware.
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from backend.src.db.connection import init_db
from backend.src.api.auth import router as auth_router
from backend.src.api.agents import router as agents_router
from backend.src.api.conversations import router as conversations_router
from backend.src.api.planning import router as planning_router
from backend.src.api.approvals import router as approvals_router
from backend.src.api.delegations import router as delegations_router
from backend.src.api.middleware import setup_middleware
from backend.src.core.config import API_HOST, API_PORT, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized!")

    yield

    # Shutdown: cleanup if needed
    logger.info("Shutting down...")


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


@app.get("/")
def root():
    """Root endpoint - API info."""
    return {
        "name": "AI Workforce Platform API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.src.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
