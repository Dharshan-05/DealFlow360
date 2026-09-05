"""Quotation Model (DealFlow360 B09: Phases 186–195).

Represents a governed commercial quotation scoped to a tenant company, customer,
and authoring user, tracking line items, multi-tier discounts, taxes, and real-time margins.
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.quotation_line_item import QuotationLineItem
    from app.models.user import User


class QuotationStatus(str, enum.Enum):
    """Lifecycle statuses for quotations (Phase 186)."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Quotation(Base):
    """Quotation Header Entity (Phase 186–195).

    Tracks customer association, unique quote numbering, discounts, taxes,
    and financial margins with strict Decimal numeric precision.
    """

    __tablename__ = "quotations"

    __table_args__ = (
        UniqueConstraint("company_id", "quotation_number", name="uq_quotations_company_quotation_number"),
    )

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
        ForeignKey("customers.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        comment="Author/Sales representative who created the quotation",
    )
    quotation_number: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
        default=QuotationStatus.DRAFT.value,
    )

    # Financial totals (Strict Decimal / Numeric precision)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Sum of gross line subtotals before discounts",
    )
    line_discount_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Aggregated sum of all line item discounts",
    )
    overall_discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Quotation-level overall discount percentage (Phase 194)",
    )
    overall_discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Quotation-level overall discount monetary amount (Phase 194)",
    )
    total_discount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Combined total discounts (line discounts + overall discount)",
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Net taxable base after all discounts applied (Phase 192)",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Aggregated tax amount (Phase 192)",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Final grand total amount payable (taxable + tax)",
    )

    # Margin metrics (Phase 195)
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Aggregated product cost across all line items",
    )
    gross_profit: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Total net revenue excluding tax minus total cost",
    )
    margin_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Gross profit margin percentage",
    )
    is_negative_margin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Flag indicating quotation has negative gross profit",
    )

    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    terms_conditions: Mapped[Optional[str]] = mapped_column(
        Text,
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
    company: Mapped["Company"] = relationship(
        "Company",
        lazy="selectin",
    )
    customer: Mapped["Customer"] = relationship(
        "Customer",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )
    line_items: Mapped[List["QuotationLineItem"]] = relationship(
        "QuotationLineItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="QuotationLineItem.line_number",
    )

    def __repr__(self) -> str:
        return f"<Quotation {self.quotation_number} status={self.status} total={self.total_amount}>"
