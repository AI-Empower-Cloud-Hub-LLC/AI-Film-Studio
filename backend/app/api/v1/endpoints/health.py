"""
Health Check Endpoint
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import redis
from app.db.session import get_db
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=dict)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    Verifies database and Redis connectivity
    """
    health_status = {
        "status": "healthy",
        "services": {
            "database": "unknown",
            "redis": "unknown",
            "api": "healthy"
        }
    }

    # Check database
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Set overall status
    if health_status["status"] != "degraded":
        health_status["status"] = "healthy"

    status_code = 200 if health_status["status"] == "healthy" else 503
    if status_code == 503:
        raise HTTPException(status_code=status_code, detail=health_status)

    return health_status


@router.get("/liveness", response_model=dict)
async def liveness_check():
    """
    Liveness probe - checks if service is running
    Used by Kubernetes/Container Apps
    """
    return {"status": "alive"}


@router.get("/readiness", response_model=dict)
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe - checks if service is ready to handle requests
    """
    try:
        db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Not ready")
