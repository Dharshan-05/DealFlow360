import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.session import SessionLocal
from app.models.user import User


def test_user_model_import_and_metadata():
    """Verify User model is registered in Base.metadata with correct table name."""
    assert "users" in Base.metadata.tables
    table = Base.metadata.tables["users"]
    assert table.name == "users"


def test_user_columns_definition():
    """Verify required column definitions and constraints on User model."""
    columns = {col.name: col for col in User.__table__.columns}
    assert "id" in columns
    assert "email" in columns
    assert "first_name" in columns
    assert "last_name" in columns
    assert "is_active" in columns
    assert "created_at" in columns
    assert "updated_at" in columns

    # Verify column constraints
    assert columns["id"].primary_key is True
    assert columns["email"].unique is True
    assert columns["email"].nullable is False
    assert columns["first_name"].nullable is False
    assert columns["last_name"].nullable is False
    assert columns["is_active"].nullable is False
    assert columns["created_at"].nullable is False
    assert columns["updated_at"].nullable is False


def test_user_persistence_and_retrieval():
    """Verify a User entity can be created, persisted, and queried by ID and email."""
    session = SessionLocal()
    unique_email = f"test_{uuid.uuid4().hex[:8]}@dealflow360.com"

    try:
        user = User(
            email=unique_email,
            first_name="Jane",
            last_name="Doe",
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == unique_email
        assert user.first_name == "Jane"
        assert user.last_name == "Doe"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

        # Query by ID
        stmt = select(User).where(User.id == user.id)
        queried = session.scalars(stmt).first()
        assert queried is not None
        assert queried.email == unique_email

        # Clean up
        session.delete(user)
        session.commit()
    finally:
        session.close()


def test_user_email_uniqueness_enforced():
    """Verify duplicate email insertion triggers IntegrityError."""
    session = SessionLocal()
    duplicate_email = f"dup_{uuid.uuid4().hex[:8]}@dealflow360.com"

    user1 = User(
        email=duplicate_email,
        first_name="First",
        last_name="User",
    )
    user2 = User(
        email=duplicate_email,
        first_name="Second",
        last_name="User",
    )

    try:
        session.add(user1)
        session.commit()

        session.add(user2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Clean up user1
        session.delete(user1)
        session.commit()
    finally:
        session.close()


def test_user_representation():
    """Verify __repr__ provides clean debugging information."""
    test_id = uuid.uuid4()
    user = User(id=test_id, email="rep@dealflow360.com", first_name="Sales", last_name="Rep")
    repr_str = repr(user)
    assert "rep@dealflow360.com" in repr_str
    assert str(test_id) in repr_str
