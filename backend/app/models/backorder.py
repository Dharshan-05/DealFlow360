import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Backorder(Base):
    __tablename__ = "backorders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    requested_quantity = Column(Integer, nullable=False)
    allocated_quantity = Column(Integer, nullable=False, default=0)
    backordered_quantity = Column(Integer, nullable=False)

    status = Column(String(32), nullable=False, default="OPEN", index=True)  # OPEN, FULFILLED, CANCELLED
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
    fulfillments = relationship("Fulfillment", back_populates="backorder")

    __table_args__ = (
        CheckConstraint("requested_quantity > 0", name="ck_backorders_requested_qty_positive"),
        CheckConstraint("allocated_quantity >= 0", name="ck_backorders_allocated_qty_non_negative"),
        CheckConstraint("backordered_quantity > 0", name="ck_backorders_backordered_qty_positive"),
        CheckConstraint("backordered_quantity = requested_quantity - allocated_quantity", name="ck_backorders_backordered_calc"),
        Index("ix_backorders_company_status", "company_id", "status"),
    )
