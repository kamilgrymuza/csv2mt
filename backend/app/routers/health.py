from fastapi import APIRouter
from datetime import datetime
from ..schemas import HealthCheck

router = APIRouter(
    prefix="/health",
    tags=["health"]
)


@router.get("/", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now()
    )