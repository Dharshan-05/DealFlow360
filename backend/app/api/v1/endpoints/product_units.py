"""Product Units API Endpoints (Phase 077: Product Units).

Provides endpoints for units of measure catalog:
- GET /product-units: List active or all units
- GET /product-units/{id}: Get unit by ID
- POST /product-units: Create new unit
- PUT /product-units/{id}: Update unit
- DELETE /product-units/{id}: Deactivate/delete unit
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.product import (
    ProductUnitCreate,
    ProductUnitResponse,
    ProductUnitUpdate,
)
from app.schemas.response import ApiResponse
from app.services.product import ProductUnitService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[List[ProductUnitResponse]],
    dependencies=[Depends(require_permission("products:read"))],
    summary="List product units (Phase 077)",
)
def list_units(
    include_inactive: bool = Query(default=False, description="Include inactive units"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List standard units of measure."""
    units = ProductUnitService.get_units(db, include_inactive=include_inactive)
    return ApiResponse(
        success=True,
        data=[ProductUnitResponse.model_validate(u) for u in units],
    )


@router.get(
    "/{unit_id}",
    response_model=ApiResponse[ProductUnitResponse],
    dependencies=[Depends(require_permission("products:read"))],
    summary="Get product unit by ID (Phase 077)",
)
def get_unit(
    unit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve single unit of measure."""
    unit = ProductUnitService.get_unit_by_id(db, unit_id)
    return ApiResponse(
        success=True,
        data=ProductUnitResponse.model_validate(unit),
    )


@router.post(
    "",
    response_model=ApiResponse[ProductUnitResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:write"))],
    summary="Create product unit (Phase 077)",
)
def create_unit(
    data: ProductUnitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new unit of measure."""
    unit = ProductUnitService.create_unit(db, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductUnitResponse.model_validate(unit),
        message=f"Product unit '{unit.code}' created successfully.",
    )


@router.put(
    "/{unit_id}",
    response_model=ApiResponse[ProductUnitResponse],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Update product unit (Phase 077)",
)
def update_unit(
    unit_id: uuid.UUID,
    data: ProductUnitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update unit of measure details."""
    unit = ProductUnitService.update_unit(db, unit_id, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductUnitResponse.model_validate(unit),
        message=f"Product unit '{unit.code}' updated successfully.",
    )


@router.delete(
    "/{unit_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Delete product unit (Phase 077)",
)
def delete_unit(
    unit_id: uuid.UUID,
    soft: bool = Query(default=True, description="Soft delete (deactivate) or hard delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate or delete a unit of measure."""
    ProductUnitService.delete_unit(db, unit_id, current_user, soft=soft)
    return ApiResponse(
        success=True,
        data={"id": str(unit_id), "deleted": True, "soft": soft},
        message="Product unit deactivated successfully.",
    )
