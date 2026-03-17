"""Health check endpoints."""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check - verifies configuration."""
    return {
        "status": "ready" if settings.is_configured else "not_configured",
        "api_keys_configured": settings.is_configured,
    }
