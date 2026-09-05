import json
import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env if present
load_dotenv()


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
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "DealFlow360")
    VERSION: str = "0.1.0"
    PHASE: str = "G02 (Phases 006-010)"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    CORS_ORIGINS: List[str] = parse_cors_origins(os.getenv("CORS_ORIGINS"))


settings = Settings()
