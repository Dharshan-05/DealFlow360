import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.deal import DealActivity, DealProduct
    from app.models.quotation import Quotation
    from app.models.user import User


class CustomerDealHistory(Base):
    """Foundational CustomerDealHistory entity (Phase 060 / B11 Phases 206–215).

    Represents commercial deal lifecycle, quotation conversion lineage, product line items,
    stage progression, deterministic probability, forecasting, and activity tracking.
    """

    __tablename__ = "customer_deal_history"

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
    deal_code: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    deal_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="WON",
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(
        String(50),
        default="NEW",
        nullable=False,
        index=True,
    )
    sales_rep_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quotation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quotation_version: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Financial & Margin Precision (Phases 208 & 209)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    gross_profit: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    margin_percentage: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Probability & Forecasting (Phases 211 & 212)
    probability: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )
    expected_revenue: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    closed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
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
    company: Mapped["Company"] = relationship("Company")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="deal_history")
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id], lazy="selectin")
    quotation: Mapped[Optional["Quotation"]] = relationship("Quotation", foreign_keys=[quotation_id], lazy="selectin")
    products: Mapped[List["DealProduct"]] = relationship(
        "DealProduct",
        back_populates="deal",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    activities: Mapped[List["DealActivity"]] = relationship(
        "DealActivity",
        back_populates="deal",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DealActivity.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<CustomerDealHistory {self.deal_code} ({self.deal_value}) stage={self.stage}>"
