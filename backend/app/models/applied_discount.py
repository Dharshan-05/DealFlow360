"""Applied Discount Model (DealFlow360 G24: Phase 120).

Immutable, audit-trailed record of automated discount execution resulting from
the Discount Decision Engine evaluation.
Strictly isolated by company_id.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.user import User


class AppliedDiscount(Base):
    """Immutable audit record for automated discount application (Phase 120)."""

    __tablename__ = "applied_discounts"

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
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    deal_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    decision_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    requested_discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    applied_discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    discounted_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    margin_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        default="LOW",
        nullable=False,
    )
    reason_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    decision_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    context_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    customer: Mapped["Customer"] = relationship("Customer")
    product: Mapped["Product"] = relationship("Product")
    user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "requested_discount >= 0 AND requested_discount <= 100",
            name="ck_applied_discount_requested_range",
        ),
        CheckConstraint(
            "applied_discount >= 0 AND applied_discount <= 100",
            name="ck_applied_discount_applied_range",
        ),
        Index(
            "ix_applied_discounts_company_deal_product",
            "company_id",
            "deal_reference",
            "product_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<AppliedDiscount {self.deal_reference}: {self.applied_discount}% on product {self.product_id}>"
