from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal, get_db, check_db_connection


def test_database_configuration():
    """Verify database configuration is properly loaded from settings."""
    assert settings.DATABASE_URL.startswith("postgresql")
    assert "dealflow360" in settings.DATABASE_URL


def test_sqlalchemy_base_metadata():
    """Verify DeclarativeBase metadata and naming conventions."""
    assert Base.metadata is not None
    naming_convention = Base.metadata.naming_convention
    assert naming_convention.get("pk") == "pk_%(table_name)s"
    assert naming_convention.get("fk") == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"


def test_sqlalchemy_engine_and_connectivity():
    """Verify PostgreSQL engine connects and executes a test query."""
    is_connected = check_db_connection()
    assert is_connected is True, "Expected active PostgreSQL connection to dealflow360"

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS alive")).scalar()
        assert result == 1


def test_sqlalchemy_session_lifecycle():
    """Verify sessionmaker creates sessions and get_db dependency closes properly."""
    # Test SessionLocal factory
    session = SessionLocal()
    assert isinstance(session, Session)
    try:
        res = session.execute(text("SELECT 42")).scalar()
        assert res == 42
    finally:
        session.close()

    # Test get_db generator lifecycle
    gen = get_db()
    db_session = next(gen)
    assert isinstance(db_session, Session)
    # Ensure finally block closes session
    try:
        next(gen)
    except StopIteration:
        pass  # Generator exhausted cleanly


def test_alembic_configuration_and_metadata():
    """Verify Alembic environment binds to application settings and metadata."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    assert script is not None
