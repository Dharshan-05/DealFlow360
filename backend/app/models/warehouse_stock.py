import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.warehouse import Warehouse
    from app.models.product import Product


class WarehouseStock(Base):
    """Foundational Warehouse Stock entity (Phase 087, 089, 090).
    Tracks inventory quantities, reserved amounts, and available-to-promise
    per warehouse and product pairing.
    """

    __tablename__ = "warehouse_stocks"

    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", name="uq_warehouse_stocks_warehouse_product"),
        CheckConstraint("quantity >= 0", name="ck_warehouse_stocks_qty_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_warehouse_stocks_reserved_non_negative"),
        CheckConstraint("reserved_quantity <= quantity", name="ck_warehouse_stocks_reserved_lte_qty"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    reserved_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
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
    warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse",
        back_populates="stocks",
    )
    product: Mapped["Product"] = relationship(
        "Product",
    )

    @property
    def available_to_promise(self) -> int:
        """Deterministic Available-to-Promise (ATP) calculation (Phase 090).
        ATP = max(quantity - reserved_quantity, 0)
        """
        return max(self.quantity - self.reserved_quantity, 0)

    @property
    def is_available(self) -> bool:
        """Boolean availability indicator (Phase 088)."""
        return self.available_to_promise > 0

    def __repr__(self) -> str:
        return (
            f"<WarehouseStock warehouse_id={self.warehouse_id} product_id={self.product_id} "
            f"qty={self.quantity} reserved={self.reserved_quantity} atp={self.available_to_promise}>"
        )
