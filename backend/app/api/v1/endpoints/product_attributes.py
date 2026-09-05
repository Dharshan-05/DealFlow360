"""Product Attributes API Endpoints (Phase 079: Product Attributes).

Provides endpoints for product attributes and option values:
- GET /product-attributes: List attributes with options
- GET /product-attributes/{id}: Get attribute by ID
- POST /product-attributes: Create attribute
- PUT /product-attributes/{id}: Update attribute
- DELETE /product-attributes/{id}: Delete attribute
- POST /product-attributes/{id}/values: Add value/option
- DELETE /product-attributes/{id}/values/{val_id}: Delete value/option
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.product import (
    ProductAttributeCreate,
    ProductAttributeResponse,
    ProductAttributeUpdate,
    ProductAttributeValueCreate,
    ProductAttributeValueResponse,
)
from app.schemas.response import ApiResponse
from app.services.product import ProductAttributeService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[List[ProductAttributeResponse]],
    dependencies=[Depends(require_permission("products:read"))],
    summary="List product attributes (Phase 079)",
)
def list_attributes(
    include_inactive: bool = Query(default=False, description="Include inactive attributes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List product attributes and their configured values."""
    attrs = ProductAttributeService.get_attributes(db, include_inactive=include_inactive)
    return ApiResponse(
        success=True,
        data=[ProductAttributeResponse.model_validate(a) for a in attrs],
    )


@router.get(
    "/{attr_id}",
    response_model=ApiResponse[ProductAttributeResponse],
    dependencies=[Depends(require_permission("products:read"))],
    summary="Get product attribute by ID (Phase 079)",
)
def get_attribute(
    attr_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve single product attribute definition."""
    attr = ProductAttributeService.get_attribute_by_id(db, attr_id)
    return ApiResponse(
        success=True,
        data=ProductAttributeResponse.model_validate(attr),
    )


@router.post(
    "",
    response_model=ApiResponse[ProductAttributeResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:write"))],
    summary="Create product attribute (Phase 079)",
)
def create_attribute(
    data: ProductAttributeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product attribute definition."""
    attr = ProductAttributeService.create_attribute(db, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductAttributeResponse.model_validate(attr),
        message=f"Product attribute '{attr.code}' created successfully.",
    )


@router.put(
    "/{attr_id}",
    response_model=ApiResponse[ProductAttributeResponse],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Update product attribute (Phase 079)",
)
def update_attribute(
    attr_id: uuid.UUID,
    data: ProductAttributeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update product attribute definition."""
    attr = ProductAttributeService.update_attribute(db, attr_id, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductAttributeResponse.model_validate(attr),
        message=f"Product attribute '{attr.code}' updated successfully.",
    )


@router.delete(
    "/{attr_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Delete product attribute (Phase 079)",
)
def delete_attribute(
    attr_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a product attribute definition and all its values."""
    ProductAttributeService.delete_attribute(db, attr_id, current_user)
    return ApiResponse(
        success=True,
        data={"id": str(attr_id), "deleted": True},
        message="Product attribute deleted successfully.",
    )


@router.post(
    "/{attr_id}/values",
    response_model=ApiResponse[ProductAttributeValueResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:write"))],
    summary="Add attribute value (Phase 079)",
)
def add_attribute_value(
    attr_id: uuid.UUID,
    data: ProductAttributeValueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a concrete option/value to an attribute."""
    val = ProductAttributeService.add_attribute_value(db, attr_id, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductAttributeValueResponse.model_validate(val),
        message=f"Attribute value '{val.value}' added successfully.",
    )


@router.delete(
    "/{attr_id}/values/{val_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Delete attribute value (Phase 079)",
)
def delete_attribute_value(
    attr_id: uuid.UUID,
    val_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an attribute value option."""
    ProductAttributeService.delete_attribute_value(db, attr_id, val_id, current_user)
    return ApiResponse(
        success=True,
        data={"attribute_id": str(attr_id), "value_id": str(val_id), "deleted": True},
        message="Attribute value deleted successfully.",
    )
