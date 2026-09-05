from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Standard naming convention for PostgreSQL constraint identifiers
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Foundational declarative base for all future DealFlow360 ORM models.
    Provides metadata with deterministic PostgreSQL constraint naming conventions.
    """
    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)
