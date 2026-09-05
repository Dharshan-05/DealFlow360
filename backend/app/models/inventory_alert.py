import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class InventoryAlert(Base):
    __tablename__ = "inventory_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=True, index=True)

    # OUT_OF_STOCK, LOW_STOCK, BACKORDER
    alert_type = Column(String(32), nullable=False, index=True)
    # CRITICAL, WARNING, INFO
    severity = Column(String(32), nullable=False, default="WARNING")
    message = Column(String(500), nullable=False)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    company = relationship("Company")
    product = relationship("Product")
    warehouse = relationship("Warehouse")

    __table_args__ = (
        Index("ix_inventory_alerts_company_active", "company_id", "is_active"),
        Index("ix_inventory_alerts_product_active", "product_id", "is_active"),
        Index("ix_inventory_alerts_dedup", "company_id", "product_id", "warehouse_id", "alert_type", "is_active"),
    )
