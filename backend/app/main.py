from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup logging
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} "
        f"[Environment: {settings.ENVIRONMENT}, Phase: {settings.PHASE}]"
    )
    yield
    # Application shutdown logging
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="DealFlow360 Continuous Deal and Discount Governance Platform API",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
)

# Register centralized global error handlers
register_error_handlers(app)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register versioned API router (/api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root discovery endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "DealFlow360 API Foundation Operational",
        "phase": settings.PHASE,
        "docs_url": "/docs",
        "v1_health": f"{settings.API_V1_STR}/health",
    }


# G01 backward-compatibility health endpoint
@app.get("/health", tags=["Health"])
async def legacy_health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "phase": settings.PHASE,
        "version": settings.VERSION,
    }
