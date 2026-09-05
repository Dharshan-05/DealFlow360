import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Fulfillment(Base):
    __tablename__ = "fulfillments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    requested_quantity = Column(Integer, nullable=False)
    fulfilled_quantity = Column(Integer, nullable=False, default=0)
    remaining_quantity = Column(Integer, nullable=False, default=0)

    # Fulfillment status: PENDING, PARTIALLY_FULFILLED, FULFILLED
    status = Column(String(32), nullable=False, default="PENDING", index=True)

    # Delivery status: NOT_STARTED, READY, DISPATCHED, IN_TRANSIT, DELIVERED, CANCELLED
    delivery_status = Column(String(32), nullable=False, default="NOT_STARTED", index=True)

    backorder_id = Column(UUID(as_uuid=True), ForeignKey("backorders.id", ondelete="SET NULL"), nullable=True, index=True)
    tracking_number = Column(String(100), nullable=True)
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    company = relationship("Company")
    product = relationship("Product")
    backorder = relationship("Backorder", back_populates="fulfillments")

    __table_args__ = (
        CheckConstraint("requested_quantity > 0", name="ck_fulfillments_requested_qty_positive"),
        CheckConstraint("fulfilled_quantity >= 0", name="ck_fulfillments_fulfilled_qty_non_negative"),
        CheckConstraint("remaining_quantity >= 0", name="ck_fulfillments_remaining_qty_non_negative"),
        CheckConstraint("fulfilled_quantity <= requested_quantity", name="ck_fulfillments_fulfilled_lte_requested"),
        CheckConstraint("remaining_quantity = requested_quantity - fulfilled_quantity", name="ck_fulfillments_remaining_calc"),
        Index("ix_fulfillments_company_status", "company_id", "status"),
        Index("ix_fulfillments_company_delivery_status", "company_id", "delivery_status"),
    )
