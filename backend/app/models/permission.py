import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.role import Role


class Permission(Base):
    """Foundational Permission entity (Phase 017).
    Defines atomic resource-action capabilities.
    """

    __tablename__ = "permissions"

    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    resource: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
    )

    def __repr__(self) -> str:
        return f"<Permission {self.name} ({self.resource}:{self.action})>"
