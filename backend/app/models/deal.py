import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer_deal_history import CustomerDealHistory
    from app.models.product import Product
    from app.models.quotation_line_item import QuotationLineItem
    from app.models.user import User


class DealStage(str, enum.Enum):
    """Canonical deal lifecycle stages (Phase 210)."""
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    PROPOSAL = "PROPOSAL"
    NEGOTIATION = "NEGOTIATION"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"


class DealActivityType(str, enum.Enum):
    """Supported commercial deal activity classifications (Phase 213)."""
    NOTE = "NOTE"
    CALL = "CALL"
    EMAIL = "EMAIL"
    MEETING = "MEETING"
    TASK = "TASK"
    FOLLOW_UP = "FOLLOW_UP"
    STAGE_CHANGE = "STAGE_CHANGE"
    APPROVAL = "APPROVAL"
    QUOTE_SENT = "QUOTE_SENT"
    QUOTE_ACCEPTED = "QUOTE_ACCEPTED"
    QUOTE_REJECTED = "QUOTE_REJECTED"


class DealProduct(Base):
    """Explicit product line item linked to a commercial deal (Phase 207).

    Preserves transactional product snapshots, quantities, pricing, costs, discounts,
    taxes, and gross margins using Decimal arithmetic.
    """

    __tablename__ = "deal_products"

    __table_args__ = (
        UniqueConstraint("deal_id", "product_id", name="uq_deal_products_deal_product"),
        CheckConstraint("quantity > 0", name="chk_deal_product_quantity_pos"),
        CheckConstraint("unit_price >= 0", name="chk_deal_product_unit_price_nonneg"),
        CheckConstraint("unit_cost >= 0", name="chk_deal_product_unit_cost_nonneg"),
        CheckConstraint("discount_percent >= 0 AND discount_percent <= 100", name="chk_deal_product_discount_pct_range"),
        CheckConstraint("tax_rate >= 0 AND tax_rate <= 100", name="chk_deal_product_tax_rate_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_deal_history.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    quotation_line_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotation_line_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    gross_profit: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    margin_percentage: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    deal: Mapped["CustomerDealHistory"] = relationship(
        "CustomerDealHistory",
        back_populates="products",
    )
    company: Mapped["Company"] = relationship("Company")
    product: Mapped["Product"] = relationship("Product", lazy="selectin")
    quotation_line_item: Mapped[Optional["QuotationLineItem"]] = relationship("QuotationLineItem", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DealProduct deal={self.deal_id} prod={self.product_id} qty={self.quantity} total={self.total_amount}>"


class DealActivity(Base):
    """Append-only audit and interaction record for a commercial deal (Phase 213).

    Tracks sales calls, notes, emails, meetings, tasks, follow-ups, and stage changes
    with actor accountability and tenant isolation.
    """

    __tablename__ = "deal_activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_deal_history.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    activity_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    deal: Mapped["CustomerDealHistory"] = relationship(
        "CustomerDealHistory",
        back_populates="activities",
    )
    company: Mapped["Company"] = relationship("Company")
    actor: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DealActivity {self.activity_type} deal={self.deal_id} title={self.title}>"
