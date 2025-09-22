from fastapi import APIRouter
from datetime import datetime
from ..schemas import HealthCheck

router = APIRouter(
    prefix="/health",
    tags=["health"]
)


@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }