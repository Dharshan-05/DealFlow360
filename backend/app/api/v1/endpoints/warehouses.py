"""Warehouse and Inventory Management API Endpoints (G18: Phases 086–090).

Provides endpoints for:
- Phase 086: Warehouse CRUD (List, Detail, Create, Update, Soft Deactivate)
- Phase 087: Warehouse Stock (List Stock, Set/Update Stock)
- Phase 088: Stock Availability API (Check Product Stock & Availability in Warehouse)
- Phase 089: Reserved Stock (Reserve / Release Stock)
- Phase 090: Available-to-Promise (ATP Calculation API)
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.warehouse import (
    AllocationRequest,
    AllocationResponse,
    ATPResponse,
    MultiWarehouseReleaseRequest,
    MultiWarehouseReleaseResponse,
    MultiWarehouseReservationResponse,
    MultiWarehouseStockResponse,
    ReservationAllocationRequest,
    StockAvailabilityResponse,
    StockReleaseRequest,
    StockReserveRequest,
    WarehouseCreate,
    WarehouseListResponse,
    WarehouseResponse,
    WarehouseSelectionResponse,
    WarehouseStockCreate,
    WarehouseStockListResponse,
    WarehouseStockResponse,
    WarehouseStockUpdate,
    WarehouseUpdate,
)
from app.services.atp import AvailableToPromiseService
from app.services.fulfillment_allocation import FulfillmentAllocationService
from app.services.multi_warehouse_stock import MultiWarehouseStockService
from app.services.stock_reservation import StockReservationService
from app.services.warehouse import WarehouseService
from app.services.warehouse_selection import WarehouseSelectionService

router = APIRouter()


# ==============================================================================
# Phase 086 — Warehouse CRUD Endpoints
# ==============================================================================

@router.get(
    "",
    response_model=ApiResponse[WarehouseListResponse],
    dependencies=[Depends(require_permission("warehouses:read"))],
    summary="List warehouses (Phase 086)",
)
def list_warehouses(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    search: Optional[str] = Query(default=None, description="Search by code, name, city, or state"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List warehouses for the current user's company with stock summaries."""
    result = WarehouseService.get_warehouses(
        db=db,
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        is_active=is_active,
        search=search,
    )
    return ApiResponse(
        success=True,
        data=result,
        message="Warehouses retrieved successfully",
    )


@router.post(
    "",
    response_model=ApiResponse[WarehouseResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("warehouses:write"))],
    summary="Create warehouse (Phase 086)",
)
def create_warehouse(
    warehouse_in: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new warehouse facility."""
    warehouse = WarehouseService.create_warehouse(
        db=db,
        company_id=current_user.company_id,
        warehouse_in=warehouse_in,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=warehouse,
        message="Warehouse created successfully",
    )


@router.get(
    "/{warehouse_id}",
    response_model=ApiResponse[WarehouseResponse],
    dependencies=[Depends(require_permission("warehouses:read"))],
    summary="Get warehouse details (Phase 086)",
)
def get_warehouse(
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed information for a specific warehouse."""
    warehouse = WarehouseService.get_warehouse(
        db=db,
        warehouse_id=warehouse_id,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        success=True,
        data=warehouse,
        message="Warehouse retrieved successfully",
    )


@router.put(
    "/{warehouse_id}",
    response_model=ApiResponse[WarehouseResponse],
    dependencies=[Depends(require_permission("warehouses:write"))],
    summary="Update warehouse (Phase 086)",
)
def update_warehouse(
    warehouse_id: uuid.UUID,
    warehouse_in: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update warehouse details."""
    warehouse = WarehouseService.update_warehouse(
        db=db,
        warehouse_id=warehouse_id,
        warehouse_in=warehouse_in,
        company_id=current_user.company_id,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=warehouse,
        message="Warehouse updated successfully",
    )


@router.delete(
    "/{warehouse_id}",
    response_model=ApiResponse[WarehouseResponse],
    dependencies=[Depends(require_permission("warehouses:write"))],
    summary="Soft-deactivate warehouse (Phase 086)",
)
def deactivate_warehouse(
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deactivate a warehouse without breaking historical stock records."""
    warehouse = WarehouseService.deactivate_warehouse(
        db=db,
        warehouse_id=warehouse_id,
        company_id=current_user.company_id,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=warehouse,
        message="Warehouse deactivated successfully",
    )


# ==============================================================================
# Phase 087 — Warehouse Stock Endpoints
# ==============================================================================

@router.get(
    "/{warehouse_id}/stock",
    response_model=ApiResponse[WarehouseStockListResponse],
    dependencies=[Depends(require_permission("warehouses:read"))],
    summary="List warehouse stock records (Phase 087)",
)
def list_warehouse_stock(
    warehouse_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all stock inventory records in a warehouse with ATP and product details."""
    # Ensure warehouse belongs to company
    WarehouseService.get_warehouse(db, warehouse_id, current_user.company_id)
    stocks = WarehouseService.get_warehouse_stocks(db=db, warehouse_id=warehouse_id)
    return ApiResponse(
        success=True,
        data=stocks,
        message="Warehouse stock retrieved successfully",
    )


@router.post(
    "/{warehouse_id}/stock",
    response_model=ApiResponse[WarehouseStockResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("warehouses:write"))],
    summary="Set product stock in warehouse (Phase 087)",
)
def set_warehouse_stock(
    warehouse_id: uuid.UUID,
    stock_in: WarehouseStockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set physical and reserved stock for a product in a warehouse."""
    WarehouseService.get_warehouse(db, warehouse_id, current_user.company_id)
    stock = WarehouseService.set_stock(
        db=db,
        warehouse_id=warehouse_id,
        stock_in=stock_in,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=stock,
        message="Warehouse stock configured successfully",
    )


@router.put(
    "/{warehouse_id}/stock/{product_id}",
    response_model=ApiResponse[WarehouseStockResponse],
    dependencies=[Depends(require_permission("warehouses:write"))],
    summary="Update physical stock quantity (Phase 087)",
)
def update_warehouse_stock_quantity(
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    stock_update: WarehouseStockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update physical stock on hand for a product in a warehouse."""
    WarehouseService.get_warehouse(db, warehouse_id, current_user.company_id)
    stock = WarehouseService.update_stock_quantity(
        db=db,
        warehouse_id=warehouse_id,
        product_id=product_id,
        new_quantity=stock_update.quantity,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=stock,
        message="Stock quantity updated successfully",
    )


# ==============================================================================
# Phase 088 — Stock Availability API
# ==============================================================================

@router.get(
    "/{warehouse_id}/stock/{product_id}/availability",
    response_model=ApiResponse[StockAvailabilityResponse],
    dependencies=[Depends(require_permission("warehouses:read"))],
    summary="Check stock availability (Phase 088)",
)
def check_stock_availability(
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate product stock, reserved quantity, and availability status."""
    WarehouseService.get_warehouse(db, warehouse_id, current_user.company_id)
    availability = AvailableToPromiseService.check_availability(
        db=db,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )
    return ApiResponse(
        success=True,
        data=availability,
        message="Stock availability evaluated successfully",
    )


# ==============================================================================
# Phase 089 — Reserved Stock Operations
# ==============================================================================

@router.post(
    "/{warehouse_id}/stock/{product_id}/reserve",
    response_model=ApiResponse[WarehouseStockResponse],
    dependencies=[Depends(require_permission("warehouses:write"))],
    summary="Reserve stock (Phase 089)",
)
def reserve_stock(
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    reserve_req: StockReserveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reserve a specified quantity of product stock."""
    WarehouseService.get_warehouse(db, warehouse_id, current_user.company_id)
    stock = WarehouseService.reserve_stock(
        db=db,
        warehouse_id=warehouse_id,
        product_id=product_id,
        amount=reserve_req.quantity,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=stock,
        message=f"Successfully reserved {reserve_req.quantity} units",
    )


@router.post(
    "/{warehouse_id}/stock/{product_id}/release",
    response_model=ApiResponse[WarehouseStockResponse],
    dependencies=[Depends(require_permission("warehouses:write"))],
    summary="Release reserved stock (Phase 089)",
)
def release_stock(
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    release_req: StockReleaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Release a specified quantity from reserved stock."""
    WarehouseService.get_warehouse(db, warehouse_id, current_user.company_id)
    stock = WarehouseService.release_stock(
        db=db,
        warehouse_id=warehouse_id,
        product_id=product_id,
        amount=release_req.quantity,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=stock,
        message=f"Successfully released {release_req.quantity} units from reservation",
    )


# ==============================================================================
# Phase 090 — Available-to-Promise (ATP) API
# ==============================================================================

@router.get(
    "/{warehouse_id}/stock/{product_id}/atp",
    response_model=ApiResponse[ATPResponse],
    dependencies=[Depends(require_permission("warehouses:read"))],
    summary="Calculate Available-to-Promise (Phase 090)",
)
def get_available_to_promise(
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate deterministic Available-to-Promise (ATP = physical - reserved)."""
    WarehouseService.get_warehouse(db, warehouse_id, current_user.company_id)
    atp = AvailableToPromiseService.get_atp(
        db=db,
        warehouse_id=warehouse_id,
        product_id=product_id,
    )
    return ApiResponse(
        success=True,
        data=atp,
        message="Available-to-Promise calculated successfully",
    )


# ==============================================================================
# Phase 092 — Warehouse Selection API
# ==============================================================================

@router.get(
    "/selection/product/{product_id}",
    response_model=ApiResponse[WarehouseSelectionResponse],
    dependencies=[Depends(require_permission("warehouses:read"))],
    summary="Select preferred warehouse for product quantity (Phase 092)",
)
def select_warehouse_for_product(
    product_id: uuid.UUID,
    quantity: int = Query(..., gt=0, description="Requested quantity to fulfill"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate and select the preferred warehouse based on priority ordering and ATP."""
    selection = WarehouseSelectionService.select_warehouse(
        db=db,
        product_id=product_id,
        requested_quantity=quantity,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        success=True,
        data=selection,
        message="Warehouse selection evaluated successfully",
    )


# ==============================================================================
# Phase 093 — Multi-Warehouse Stock API
# ==============================================================================

@router.get(
    "/multi-stock/product/{product_id}",
    response_model=ApiResponse[MultiWarehouseStockResponse],
    dependencies=[Depends(require_permission("warehouses:read"))],
    summary="Get multi-warehouse stock breakdown for a product (Phase 093)",
)
def get_multi_warehouse_stock(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated and facility-by-facility inventory breakdown across all active company warehouses."""
    multi_stock = MultiWarehouseStockService.get_product_multi_warehouse_stock(
        db=db,
        product_id=product_id,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        success=True,
        data=multi_stock,
        message="Multi-warehouse stock retrieved successfully",
    )


# ==============================================================================
# Phase 094 — Fulfillment Allocation API
# ==============================================================================

@router.post(
    "/allocation/product/{product_id}",
    response_model=ApiResponse[AllocationResponse],
    dependencies=[Depends(require_permission("warehouses:read"))],
    summary="Calculate fulfillment allocation across priority warehouses (Phase 094)",
)
def calculate_fulfillment_allocation(
    product_id: uuid.UUID,
    allocation_req: AllocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministically allocate requested quantity across priority warehouses up to ATP."""
    allocation = FulfillmentAllocationService.calculate_allocation(
        db=db,
        product_id=product_id,
        requested_quantity=allocation_req.requested_quantity,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        success=True,
        data=allocation,
        message="Fulfillment allocation calculated successfully",
    )


# ==============================================================================
# Phase 095 — Multi-Warehouse Stock Reservation & Release API
# ==============================================================================

@router.post(
    "/reservation/product/{product_id}",
    response_model=ApiResponse[MultiWarehouseReservationResponse],
    dependencies=[Depends(require_permission("warehouses:write"))],
    summary="Atomically reserve stock across warehouses based on priority allocation (Phase 095)",
)
def reserve_multi_warehouse_stock(
    product_id: uuid.UUID,
    reserve_req: ReservationAllocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atomically allocate and reserve stock across warehouses with pessimistic row locking."""
    reservation = StockReservationService.reserve_allocation(
        db=db,
        product_id=product_id,
        requested_quantity=reserve_req.requested_quantity,
        company_id=current_user.company_id,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=reservation,
        message=f"Successfully reserved {reservation.total_reserved} units across warehouses",
    )


@router.post(
    "/release/product/{product_id}",
    response_model=ApiResponse[MultiWarehouseReleaseResponse],
    dependencies=[Depends(require_permission("warehouses:write"))],
    summary="Atomically release stock reservations across warehouses (Phase 095)",
)
def release_multi_warehouse_stock(
    product_id: uuid.UUID,
    release_req: MultiWarehouseReleaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atomically release specified quantities from warehouse stock reservations."""
    release_resp = StockReservationService.release_allocation(
        db=db,
        product_id=product_id,
        release_req=release_req,
        company_id=current_user.company_id,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=release_resp,
        message=f"Successfully released {release_resp.total_released} units across warehouses",
    )

