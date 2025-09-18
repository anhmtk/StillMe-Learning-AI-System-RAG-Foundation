# StillMe Gateway - Health Routes
"""
Health check endpoints
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter
from services.notification_service import NotificationService
from services.stillme_integration import StillMeIntegration

from core.config import Settings
from core.redis_client import RedisClient

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances
settings = Settings()
stillme_integration = StillMeIntegration()
notification_service = NotificationService()
redis_client = RedisClient()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "StillMe Gateway",
        "version": settings.VERSION,
        "timestamp": "2024-01-01T00:00:00Z",
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with component status"""
    try:
        # Check StillMe Core
        stillme_status = await stillme_integration.get_status()

        # Check Redis
        redis_healthy = redis_client.is_healthy()

        # Check notification service
        notification_healthy = notification_service.is_healthy()

        # Overall health
        overall_healthy = (
            stillme_status.get("status") == "healthy"
            and redis_healthy
            and notification_healthy
        )

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "StillMe Gateway",
            "version": settings.VERSION,
            "timestamp": "2024-01-01T00:00:00Z",
            "components": {
                "stillme_core": stillme_status,
                "redis": {"status": "healthy" if redis_healthy else "unhealthy"},
                "notifications": {
                    "status": "healthy" if notification_healthy else "unhealthy"
                },
            },
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "StillMe Gateway",
            "version": settings.VERSION,
            "timestamp": "2024-01-01T00:00:00Z",
            "error": str(e),
        }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check for Kubernetes"""
    try:
        # Check if all critical components are ready
        stillme_ready = stillme_integration.is_healthy()
        redis_ready = redis_client.is_healthy()

        ready = stillme_ready and redis_ready

        return {"ready": ready, "timestamp": "2024-01-01T00:00:00Z"}

    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        return {"ready": False, "error": str(e), "timestamp": "2024-01-01T00:00:00Z"}


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes"""
    return {"alive": True, "timestamp": "2024-01-01T00:00:00Z"}
