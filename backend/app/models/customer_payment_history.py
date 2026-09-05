import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer import Customer


class CustomerPaymentHistory(Base):
    """Customer-level historical payment record (Phase 062).
    Append-only normalized record of financial settlements and payments from a customer.
    """

    __tablename__ = "customer_payment_history"

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
    payment_reference: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="COMPLETED",
        nullable=False,
    )
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
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

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="payment_history")

    def __repr__(self) -> str:
        return f"<CustomerPaymentHistory {self.payment_reference} ({self.amount})>"
