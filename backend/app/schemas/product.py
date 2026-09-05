"""Product and Product Category Pydantic Schemas (Phases 071–075).

Provides validation and response contracts for:
- Phase 071: Product CRUD
- Phase 072: Product Categories
- Phase 073: Product Pricing (Base selling price >= 0, Decimal precision)
- Phase 074: Product Cost (Product cost >= 0, Decimal precision)
- Phase 075: Product Margin (Deterministic derivation: margin_amount, margin_percentage with zero-division safety)
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


# ---------------------------------------------------------------------------
# Phase 072: Product Category Schemas
# ---------------------------------------------------------------------------

class ProductCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class ProductCategoryResponse(ProductCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Phases 071, 073, 074, 075: Product Schemas
# ---------------------------------------------------------------------------

class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    cost: Decimal = Field(default=Decimal("0.00"), ge=0, description="Product base unit cost (Phase 074)")
    base_price: Decimal = Field(default=Decimal("0.00"), ge=0, description="Product base selling price (Phase 073)")
    is_active: bool = True

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: str) -> str:
        return v.strip().upper()


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    cost: Optional[Decimal] = Field(default=None, ge=0)
    base_price: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Product response model with deterministically computed margin metrics (Phase 075)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    cost: Decimal
    base_price: Decimal
    unit: str = "unit"
    tax_rate: Decimal = Decimal("0.00")
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategoryResponse] = None

    @computed_field
    def margin_amount(self) -> Decimal:
        """Phase 075: Basic gross margin amount (selling_price - cost)."""
        price = Decimal(str(self.base_price))
        cost = Decimal(str(self.cost))
        return (price - cost).quantize(Decimal("0.01"))

    @computed_field
    def margin_percentage(self) -> Optional[Decimal]:
        """Phase 075: Margin percentage ((selling_price - cost) / selling_price) * 100.
        Returns None when selling_price is 0 to avoid division-by-zero.
        """
        price = Decimal(str(self.base_price))
        cost = Decimal(str(self.cost))
        if price <= 0:
            return None
        pct = ((price - cost) / price) * Decimal("100.00")
        return pct.quantize(Decimal("0.01"))


class ProductListResponse(BaseModel):
    """Paginated product list response container."""
    items: List[ProductResponse]
    total: int
    skip: int
    limit: int
