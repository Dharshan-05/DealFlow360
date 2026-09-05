from fastapi import APIRouter
from app.core.config import settings
from app.schemas.response import ApiResponse, HealthData

router = APIRouter()


@router.get(
    "/health",
    response_model=ApiResponse[HealthData],
    summary="API v1 Health Check",
    description="Returns service health, active roadmap phase, and runtime environment.",
)
async def api_health() -> ApiResponse[HealthData]:
    return ApiResponse(
        success=True,
        data=HealthData(
            status="healthy",
            service=settings.PROJECT_NAME,
            phase=settings.PHASE,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
        ),
        message="DealFlow360 API v1 operational",
    )
