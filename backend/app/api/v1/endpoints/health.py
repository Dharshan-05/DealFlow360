from fastapi import APIRouter
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.response import ApiResponse, DatabaseHealth, HealthData

router = APIRouter()


@router.get(
    "/health",
    response_model=ApiResponse[HealthData],
    summary="API v1 Health Check",
    description="Returns service health, active roadmap phase, runtime environment, and infrastructure DB connectivity.",
)
async def api_health() -> ApiResponse[HealthData]:
    db_connected = check_db_connection()
    return ApiResponse(
        success=True,
        data=HealthData(
            status="healthy",
            service=settings.PROJECT_NAME,
            phase=settings.PHASE,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            database=DatabaseHealth(
                connected=db_connected,
                dialect="postgresql",
            ),
        ),
        message="DealFlow360 API v1 operational",
    )
