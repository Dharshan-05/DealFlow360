"""Quotation Line Item Model (DealFlow360 B09: Phases 186–195).

Represents an individual itemized line on a quotation, tracking product,
quantity, unit pricing, line discount, line tax, cost, and margin.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.quotation import Quotation


class QuotationLineItem(Base):
    """Quotation Line Item Entity (Phase 186–195).

    Tracks product selection, quantity, unit price, line discounts, taxes,
    line totals, and line-level margins.
    """

    __tablename__ = "quotation_line_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        default=Decimal("1.0000"),
        nullable=False,
        comment="Ordered quantity (Phase 190)",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Selling unit price before discount (Phase 191)",
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Product unit cost at time of quotation (Phase 195)",
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Line item discount percentage (Phase 193)",
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Line item discount monetary amount (Phase 193)",
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Line tax percentage rate (Phase 192)",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Calculated line tax monetary amount (Phase 192)",
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Gross line amount (quantity * unit_price)",
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Line amount after line discount (subtotal - discount_amount)",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Line amount including tax (net_amount + tax_amount)",
    )
    line_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Total cost for line (quantity * unit_cost)",
    )
    gross_profit: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Line gross profit (net_amount - line_cost)",
    )
    margin_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Line gross margin percentage",
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship(
        "Quotation",
        back_populates="line_items",
    )
    product: Mapped["Product"] = relationship(
        "Product",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<QuotationLineItem quote_id={self.quotation_id} product_id={self.product_id} qty={self.quantity} total={self.total_amount}>"
