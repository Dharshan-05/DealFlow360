import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product_category import ProductCategory
    from app.models.product_variant import ProductVariant


class Product(Base):
    """Foundational Product entity (Phase 021, updated for G16 Phases 076–080).
    Represents catalog offerings with foundational cost, price, tax, unit, and subscription baselines.
    """

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    base_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(
        String(50),
        default="unit",
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    is_subscription: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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
    category: Mapped[Optional["ProductCategory"]] = relationship(
        "ProductCategory",
        back_populates="products",
    )
    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.sku",
    )

    def __repr__(self) -> str:
        return f"<Product {self.name} (SKU: {self.sku})>"
