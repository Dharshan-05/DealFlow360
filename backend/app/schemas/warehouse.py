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
    priority: int = Field(default=1, ge=1, description="Fulfillment priority (1 = highest priority)")


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
    priority: Optional[int] = Field(None, ge=1, description="Fulfillment priority (1 = highest priority)")


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


# ==============================================================================
# Warehouse Selection Schemas (Phase 092)
# ==============================================================================

class WarehouseSelectionCandidate(BaseModel):
    warehouse_id: uuid.UUID
    warehouse_code: str
    warehouse_name: str
    priority: int
    physical_quantity: int
    reserved_quantity: int
    available_to_promise: int
    can_fulfill_full: bool


class WarehouseSelectionResponse(BaseModel):
    product_id: uuid.UUID
    requested_quantity: int
    selected_warehouse_id: Optional[uuid.UUID] = None
    selected_warehouse_code: Optional[str] = None
    selected_warehouse_name: Optional[str] = None
    selected_warehouse_priority: Optional[int] = None
    is_fully_fulfillable: bool
    requires_multi_warehouse: bool
    candidates: List[WarehouseSelectionCandidate]


# ==============================================================================
# Multi-Warehouse Stock Schemas (Phase 093)
# ==============================================================================

class WarehouseStockDetailItem(BaseModel):
    warehouse_id: uuid.UUID
    warehouse_code: str
    warehouse_name: str
    priority: int
    physical_quantity: int
    reserved_quantity: int
    available_to_promise: int
    is_available: bool


class MultiWarehouseStockResponse(BaseModel):
    product_id: uuid.UUID
    product_sku: str
    product_name: str
    total_physical_quantity: int
    total_reserved_quantity: int
    total_available_quantity: int
    warehouses_count: int
    warehouses: List[WarehouseStockDetailItem]


# ==============================================================================
# Fulfillment Allocation Schemas (Phase 094)
# ==============================================================================

class AllocationItem(BaseModel):
    warehouse_id: uuid.UUID
    warehouse_code: str
    warehouse_name: str
    priority: int
    available_to_promise: int
    allocated_quantity: int


class AllocationRequest(BaseModel):
    requested_quantity: int = Field(..., gt=0, description="Requested quantity to allocate (must be strictly positive)")


class AllocationResponse(BaseModel):
    product_id: uuid.UUID
    requested_quantity: int
    total_allocated: int
    unallocated_quantity: int
    is_fully_allocated: bool
    allocations: List[AllocationItem]


# ==============================================================================
# Multi-Warehouse Stock Reservation Schemas (Phase 095)
# ==============================================================================

class WarehouseReservationItem(BaseModel):
    warehouse_id: uuid.UUID
    warehouse_code: str
    reserved_quantity: int
    remaining_atp: int


class ReservationAllocationRequest(BaseModel):
    requested_quantity: int = Field(..., gt=0, description="Quantity to allocate and reserve across warehouses")


class MultiWarehouseReservationResponse(BaseModel):
    product_id: uuid.UUID
    requested_quantity: int
    total_reserved: int
    unallocated_quantity: int
    is_fully_reserved: bool
    reservations: List[WarehouseReservationItem]


class WarehouseReleaseItem(BaseModel):
    warehouse_id: uuid.UUID
    quantity: int = Field(..., gt=0, description="Quantity to release from this warehouse")


class MultiWarehouseReleaseRequest(BaseModel):
    releases: List[WarehouseReleaseItem] = Field(..., min_length=1, description="List of warehouse release specifications")


class MultiWarehouseReleaseResponse(BaseModel):
    product_id: uuid.UUID
    total_released: int
    releases: List[WarehouseReservationItem]

