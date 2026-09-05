from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import logger

# Centralized SQLAlchemy Engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO_LOG,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    future=True,
)

# Centralized Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding an isolated database session.
    Guarantees session cleanup in the finally block.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Non-blocking infrastructure check to verify PostgreSQL connectivity.
    Returns True if connection succeeds, False if unavailable.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connectivity check failed: {e}")
        return False
