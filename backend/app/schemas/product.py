"""Product, Category, Units, Variants, and Attributes Pydantic Schemas (Phases 071–080).

Provides validation and response contracts for:
- Phase 071: Product CRUD
- Phase 072: Product Categories
- Phase 073: Product Pricing
- Phase 074: Product Cost
- Phase 075: Product Margin
- Phase 076: Product Tax (tax_rate >= 0, Decimal precision)
- Phase 077: Product Units (code, name, active, catalog)
- Phase 078: Product Variants (SKU uniqueness, price/cost overrides)
- Phase 079: Product Attributes (code, name, values/options, variant associations)
- Phase 080: Subscription Products (is_subscription bool flag)
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
# Phase 077: Product Unit Schemas
# ---------------------------------------------------------------------------

class ProductUnitBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Unit code e.g. UNIT, BOX, KG, LICENSE")
    name: str = Field(..., min_length=1, max_length=100, description="Display name e.g. Standard Unit, Box, License")
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class ProductUnitCreate(ProductUnitBase):
    pass


class ProductUnitUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class ProductUnitResponse(ProductUnitBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Phase 079: Product Attribute & Value Schemas
# ---------------------------------------------------------------------------

class ProductAttributeValueBase(BaseModel):
    value: str = Field(..., min_length=1, max_length=100)
    display_order: int = Field(default=0, ge=0)


class ProductAttributeValueCreate(ProductAttributeValueBase):
    pass


class ProductAttributeValueResponse(ProductAttributeValueBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    attribute_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProductAttributeBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Attribute code e.g. COLOR, SIZE, EDITION")
    name: str = Field(..., min_length=1, max_length=100, description="Display name e.g. Color, Size, Edition")
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class ProductAttributeCreate(ProductAttributeBase):
    pass


class ProductAttributeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class ProductAttributeResponse(ProductAttributeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    values: List[ProductAttributeValueResponse] = []


# ---------------------------------------------------------------------------
# Phase 078: Product Variant Schemas
# ---------------------------------------------------------------------------

class ProductVariantBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    cost: Optional[Decimal] = Field(default=None, ge=0, description="Optional cost override")
    base_price: Optional[Decimal] = Field(default=None, ge=0, description="Optional selling price override")
    is_active: bool = True

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: str) -> str:
        return v.strip().upper()


class ProductVariantCreate(ProductVariantBase):
    attribute_value_ids: Optional[List[uuid.UUID]] = Field(default_factory=list)


class ProductVariantUpdate(BaseModel):
    sku: Optional[str] = Field(default=None, min_length=1, max_length=100)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    cost: Optional[Decimal] = Field(default=None, ge=0)
    base_price: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    attribute_value_ids: Optional[List[uuid.UUID]] = None

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().upper()
        return v


class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    sku: str
    name: str
    cost: Optional[Decimal] = None
    base_price: Optional[Decimal] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    attribute_values: List[ProductAttributeValueResponse] = []


# ---------------------------------------------------------------------------
# Phases 071, 073, 074, 075, 076, 077, 080: Product Schemas
# ---------------------------------------------------------------------------

class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    cost: Decimal = Field(default=Decimal("0.00"), ge=0, description="Product base unit cost (Phase 074)")
    base_price: Decimal = Field(default=Decimal("0.00"), ge=0, description="Product base selling price (Phase 073)")
    unit: str = Field(default="unit", min_length=1, max_length=50, description="Unit of measure (Phase 077)")
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, description="Tax rate percentage >= 0 (Phase 076)")
    is_subscription: bool = Field(default=False, description="Subscription product flag (Phase 080)")
    is_active: bool = True

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("unit")
    @classmethod
    def normalize_unit(cls, v: str) -> str:
        return v.strip().lower()


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    cost: Optional[Decimal] = Field(default=None, ge=0)
    base_price: Optional[Decimal] = Field(default=None, ge=0)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=50)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0)
    is_subscription: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator("unit")
    @classmethod
    def normalize_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().lower()
        return v


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
    is_subscription: bool = False
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategoryResponse] = None
    variants: List[ProductVariantResponse] = []

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
