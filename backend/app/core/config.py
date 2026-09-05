import json
import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator

# Load environment variables from .env if present
load_dotenv()

INSECURE_DEV_JWT_SECRET = "dealflow360-dev-insecure-jwt-secret-key-must-change-in-production-min-32-chars"
DEFAULT_DEV_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/dealflow360"


def parse_cors_origins(origins_str: str | None) -> List[str]:
    if not origins_str:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    origins_str = origins_str.strip()
    if origins_str.startswith("[") and origins_str.endswith("]"):
        try:
            return json.loads(origins_str)
        except json.JSONDecodeError:
            pass
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


class Settings(BaseModel):
    PROJECT_NAME: str = Field(default_factory=lambda: os.getenv("PROJECT_NAME", "DealFlow360"))
    VERSION: str = "0.1.0"
    PHASE: str = Field(default_factory=lambda: os.getenv("PHASE", "G03 (Phases 011-015)"))
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development").lower())
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "true").lower() in ("true", "1", "yes"))
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    API_V1_STR: str = Field(default_factory=lambda: os.getenv("API_V1_STR", "/api/v1"))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: parse_cors_origins(os.getenv("CORS_ORIGINS")))

    # Database Configuration (PostgreSQL)
    DATABASE_URL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", DEFAULT_DEV_DATABASE_URL))
    DB_ECHO_LOG: bool = Field(default_factory=lambda: os.getenv("DB_ECHO_LOG", "false").lower() in ("true", "1", "yes"))
    DB_POOL_PRE_PING: bool = True

    # Security & JWT Authentication (G06: Phases 026–030)
    JWT_SECRET_KEY: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", INSECURE_DEV_JWT_SECRET))
    JWT_ALGORITHM: str = Field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))

    # API Documentation toggle (Phase 456 / 466)
    ENABLE_DOCS: bool = Field(default_factory=lambda: os.getenv(
        "ENABLE_DOCS",
        "false" if os.getenv("ENVIRONMENT", "development").lower() == "production" else "true",
    ).lower() in ("true", "1", "yes"))

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        """
        Phase 456 & 465 Strict Production Guardrails:
        Production configuration must fail safely when required secrets are missing
        or insecure development defaults are detected.
        """
        if self.ENVIRONMENT == "production":
            # 1. Debug flag must never silently remain enabled in production
            if self.DEBUG:
                raise ValueError(
                    "Production safety violation: DEBUG mode must be disabled in production environment."
                )

            # 2. Insecure JWT secret rejection
            if self.JWT_SECRET_KEY == INSECURE_DEV_JWT_SECRET:
                raise ValueError(
                    "Production safety violation: Insecure development JWT_SECRET_KEY detected. "
                    "A secure 256-bit cryptographically random secret is required for production."
                )
            if len(self.JWT_SECRET_KEY) < 32:
                raise ValueError(
                    "Production safety violation: JWT_SECRET_KEY must be at least 32 characters in production."
                )

            # 3. Dedicated database URL check
            if not self.DATABASE_URL or self.DATABASE_URL == DEFAULT_DEV_DATABASE_URL:
                raise ValueError(
                    "Production safety violation: Dedicated production DATABASE_URL must be explicitly provided."
                )

            # 4. CORS validation for production
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "Production safety violation: Wildcard CORS origin ('*') is forbidden in production."
                )

        return self


settings = Settings()

