"""
Health Check Routes
System health and status endpoints
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from api.config import settings
from api.schemas import HealthCheckResponse


router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check if the API is running"
)
async def health_check():
    """
    Health check endpoint.
    
    Use this for:
    - Load balancer health checks
    - Monitoring systems
    - Verifying the API is up
    """
    return HealthCheckResponse(
        status="healthy",
        version=settings.version,
        timestamp=datetime.now(timezone.utc)
    )


@router.get(
    "/",
    summary="API root",
    description="Welcome message and API info"
)
async def root():
    """API root - returns basic info"""
    return {
        "name": settings.title,
        "version": settings.version,
        "description": settings.description,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/health"
    }
