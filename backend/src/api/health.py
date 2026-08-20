"""
Health Check Endpoints

Provides comprehensive health checks for monitoring and load balancers.
"""
import time
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.src.db.connection import get_db
from backend.src.core.config import (
    REDIS_URL,
    DATABASE_URL,
    ENVIRONMENT,
)

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


def check_database(db: Session) -> Dict[str, Any]:
    """Check database connectivity."""
    start = time.time()
    try:
        db.execute(text("SELECT 1"))
        latency_ms = int((time.time() - start) * 1000)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    if not REDIS_URL:
        return {
            "status": "not_configured",
            "message": "Redis URL not configured",
        }

    try:
        import redis
        start = time.time()
        r = redis.from_url(REDIS_URL)
        r.ping()
        latency_ms = int((time.time() - start) * 1000)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
        }
    except ImportError:
        return {
            "status": "not_available",
            "message": "Redis package not installed",
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def check_embedding_service() -> Dict[str, Any]:
    """Check embedding service availability."""
    try:
        from backend.src.services.embedding_service import get_embedding_service
        service = get_embedding_service()
        if service.model is not None:
            return {
                "status": "healthy",
                "model": service.model_name,
            }
        else:
            return {
                "status": "not_loaded",
                "message": "Embedding model not loaded",
            }
    except Exception as e:
        return {
            "status": "unavailable",
            "error": str(e),
        }


def check_groq() -> Dict[str, Any]:
    """Check Groq API availability."""
    import os
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "status": "not_configured",
            "message": "GROQ_API_KEY not set",
        }
    return {
        "status": "configured",
        "message": "API key present",
    }


def check_nylas() -> Dict[str, Any]:
    """Check Nylas API configuration."""
    import os
    api_key = os.getenv("NYLAS_API_KEY")
    grant_id = os.getenv("NYLAS_GRANT_ID")

    if not api_key or not grant_id:
        missing = []
        if not api_key:
            missing.append("NYLAS_API_KEY")
        if not grant_id:
            missing.append("NYLAS_GRANT_ID")
        return {
            "status": "not_configured",
            "missing": missing,
        }
    return {
        "status": "configured",
        "message": "Nylas credentials present",
    }


@router.get("/health")
def basic_health_check():
    """
    Basic health check endpoint.

    Returns a simple healthy status for load balancers.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check endpoint.

    Returns comprehensive health status of all services.
    """
    start = time.time()

    checks = {
        "database": check_database(db),
        "redis": check_redis(),
        "embedding_service": check_embedding_service(),
        "groq": check_groq(),
        "nylas": check_nylas(),
    }

    # Determine overall status
    unhealthy_services = [
        name for name, check in checks.items()
        if check.get("status") == "unhealthy"
    ]

    overall_status = "unhealthy" if unhealthy_services else "healthy"

    total_time_ms = int((time.time() - start) * 1000)

    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT,
        "checks": checks,
        "total_time_ms": total_time_ms,
    }

    if unhealthy_services:
        response["unhealthy_services"] = unhealthy_services

    # Log health check result
    logger.info(json.dumps({
        "type": "health_check",
        "status": overall_status,
        "total_time_ms": total_time_ms,
        "unhealthy_services": unhealthy_services,
    }))

    return response


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.

    Returns 200 if the service is ready to accept traffic.
    """
    # Check critical services
    db_check = check_database(db)

    if db_check["status"] != "healthy":
        return {
            "status": "not_ready",
            "reason": "database_unavailable",
        }

    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/live")
def liveness_check():
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the service is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics")
def metrics():
    """
    Basic metrics endpoint.

    Returns application metrics for monitoring.
    In production, integrate with Prometheus or similar.
    """
    import os
    import psutil

    process = psutil.Process(os.getpid())

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "process": {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        },
    }


@router.get("/version")
def version_info():
    """
    Returns version and build information.
    """
    import os

    return {
        "name": "AI Workforce Platform API",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "python_version": os.sys.version,
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "git_commit": os.getenv("GIT_COMMIT", "unknown"),
    }
