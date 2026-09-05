"""Product Variant ORM Models (Phase 078: Product Variants).

Provides parent-child product variations with SKU uniqueness, price/cost overrides,
and attribute value associations.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.product_attribute import ProductAttributeValue


# Association table between variants and attribute values (many-to-many)
product_variant_attribute_values = Table(
    "product_variant_attribute_values",
    Base.metadata,
    Column(
        "variant_id",
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "attribute_value_id",
        UUID(as_uuid=True),
        ForeignKey("product_attribute_values.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ProductVariant(Base):
    """Parent-child product variant entity (Phase 078)."""

    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Optional override for parent product cost",
    )
    base_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="Optional override for parent product base price",
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
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="variants",
    )
    attribute_values: Mapped[List["ProductAttributeValue"]] = relationship(
        "ProductAttributeValue",
        secondary=product_variant_attribute_values,
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<ProductVariant {self.name} (SKU: {self.sku})>"
