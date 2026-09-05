"""Finance Authority Limit Model (Phase 107).

User/role-level discount authority governance entity for Finance Users.
Represents the maximum discount that a Finance User is authorized to grant or approve.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Numeric, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class FinanceAuthorityLimit(Base):
    __tablename__ = "finance_authority_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    max_authorized_discount: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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
    company: Mapped["Company"] = relationship("Company")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])

    __table_args__ = (
        CheckConstraint(
            "max_authorized_discount >= 0 AND max_authorized_discount <= 100",
            name="ck_finance_auth_limit_range",
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_until >= effective_from",
            name="ck_finance_auth_limit_effective_dates",
        ),
        Index(
            "uq_finance_auth_limits_active",
            "company_id",
            "user_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )
