import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ==============================================================================
# Warehouse Schemas (Phase 086)
# ==============================================================================

class WarehouseBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Unique warehouse code identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Human-readable warehouse facility name")
    description: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    is_active: bool = Field(default=True, description="Whether warehouse is active for operations")


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    total_stock_items: int = 0
    total_physical_stock: int = 0
    total_reserved_stock: int = 0
    total_atp: int = 0


class WarehouseListResponse(BaseModel):
    items: List[WarehouseResponse]
    total: int
    page: int
    size: int
    pages: int


# ==============================================================================
# Warehouse Stock Schemas (Phase 087)
# ==============================================================================

class WarehouseStockCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=0, ge=0, description="Physical stock quantity on hand")
    reserved_quantity: int = Field(default=0, ge=0, description="Stock allocated/reserved")

    @model_validator(mode="after")
    def validate_reservation_not_exceed_quantity(self):
        if self.reserved_quantity > self.quantity:
            raise ValueError("reserved_quantity cannot exceed physical stock quantity")
        return self


class WarehouseStockUpdate(BaseModel):
    quantity: int = Field(..., ge=0, description="New physical stock quantity")


class WarehouseStockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    reserved_quantity: int
    available_to_promise: int
    is_available: bool
    product_sku: Optional[str] = None
    product_name: Optional[str] = None
    product_unit: Optional[str] = None
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WarehouseStockListResponse(BaseModel):
    warehouse_id: uuid.UUID
    warehouse_code: str
    warehouse_name: str
    items: List[WarehouseStockResponse]
    total: int
    total_physical: int
    total_reserved: int
    total_atp: int


# ==============================================================================
# Stock Availability Schemas (Phase 088)
# ==============================================================================

class StockAvailabilityResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    product_sku: str
    warehouse_id: uuid.UUID
    warehouse_name: str
    warehouse_code: str
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int
    is_available: bool


# ==============================================================================
# Reserved Stock Schemas (Phase 089)
# ==============================================================================

class StockReserveRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity to reserve (must be strictly positive)")


class StockReleaseRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity to release from reservation (must be strictly positive)")


# ==============================================================================
# Available-to-Promise (ATP) Schemas (Phase 090)
# ==============================================================================

class ATPResponse(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    physical_stock: int
    reserved_stock: int
    available_to_promise: int
    is_available: bool
