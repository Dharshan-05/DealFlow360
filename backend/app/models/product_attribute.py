"""Product Attribute ORM Models (Phase 079: Product Attributes).

Defines reusable attribute definitions (e.g. COLOR, SIZE, EDITION) and their
concrete attribute values/options for catalog products and variants.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product_variant import ProductVariant


class ProductAttribute(Base):
    """Product attribute definition (e.g. Color, Size, Edition) (Phase 079)."""

    __tablename__ = "product_attributes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
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
    values: Mapped[List["ProductAttributeValue"]] = relationship(
        "ProductAttributeValue",
        back_populates="attribute",
        cascade="all, delete-orphan",
        order_by="ProductAttributeValue.display_order",
    )

    def __repr__(self) -> str:
        return f"<ProductAttribute {self.name} ({self.code})>"


class ProductAttributeValue(Base):
    """Specific option or value for a ProductAttribute (e.g. Red, XL, Enterprise) (Phase 079)."""

    __tablename__ = "product_attribute_values"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    attribute_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_attributes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    value: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
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
    attribute: Mapped["ProductAttribute"] = relationship(
        "ProductAttribute",
        back_populates="values",
    )

    def __repr__(self) -> str:
        return f"<ProductAttributeValue {self.value} (attr={self.attribute_id})>"
