"""Recommendation Event Model (DealFlow360 B08: Phase 183).

Tracks lifecycle events for AI Upsell and Cross-Sell recommendations:
GENERATED -> VIEWED -> SELECTED -> ADDED_TO_QUOTE -> ACCEPTED / REJECTED / DISMISSED.
Strictly isolated by company_id.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.user import User


class RecommendationEvent(Base):
    """Lifecycle tracking model for recommendation interactions (Phase 183)."""

    __tablename__ = "recommendation_events"

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
    recommendation_id: Mapped[str] = mapped_column(
        String(100),
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
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    recommendation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # UPSELL, CROSS_SELL, REPEAT_PURCHASE
    event_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )  # GENERATED, VIEWED, SELECTED, ADDED_TO_QUOTE, ACCEPTED, REJECTED, DISMISSED
    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    quote_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    context_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
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
    actor: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index(
            "ix_rec_events_company_created",
            "company_id",
            "created_at",
        ),
        Index(
            "ix_rec_events_company_type_event",
            "company_id",
            "recommendation_type",
            "event_type",
        ),
    )

    def __repr__(self) -> str:
        return f"<RecommendationEvent {self.recommendation_id} [{self.event_type}] on prod {self.product_id}>"
