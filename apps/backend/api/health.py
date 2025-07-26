from datetime import datetime, tzinfo
from typing import Dict, Any
from fastapi import APIRouter
from config import settings

HealthRouter = APIRouter(prefix="/health", tags=["Health"])


@HealthRouter.get("", summary="Basic Health Check", include_in_schema=False)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint that returns API status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Personal Knowledge AI Backend",
        "version": "0.1.0",
    }
