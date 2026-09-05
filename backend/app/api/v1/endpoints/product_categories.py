"""Product Categories API Endpoints (Phase 072).

Provides endpoints for managing product catalog categories:
- GET /product-categories: List product categories
- POST /product-categories: Create a new category
- GET /product-categories/{id}: Get category by ID
- PUT /product-categories/{id}: Update category
- DELETE /product-categories/{id}: Delete/deactivate category safely
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.product import (
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCategoryUpdate,
)
from app.schemas.response import ApiResponse
from app.services.product import ProductCategoryService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[List[ProductCategoryResponse]],
    dependencies=[Depends(require_permission("products:read"))],
    summary="List product categories (Phase 072)",
)
def list_categories(
    include_inactive: bool = Query(default=False, description="Include inactive categories"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all product categories."""
    categories = ProductCategoryService.get_categories(db, include_inactive=include_inactive)
    items = [ProductCategoryResponse.model_validate(c) for c in categories]
    return ApiResponse(success=True, data=items)


@router.post(
    "",
    response_model=ApiResponse[ProductCategoryResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:write"))],
    summary="Create product category (Phase 072)",
)
def create_category(
    data: ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product category."""
    category = ProductCategoryService.create_category(db, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductCategoryResponse.model_validate(category),
        message=f"Product category '{category.name}' created successfully.",
    )


@router.get(
    "/{category_id}",
    response_model=ApiResponse[ProductCategoryResponse],
    dependencies=[Depends(require_permission("products:read"))],
    summary="Get product category by ID (Phase 072)",
)
def get_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of a single product category."""
    category = ProductCategoryService.get_category_by_id(db, category_id)
    return ApiResponse(
        success=True,
        data=ProductCategoryResponse.model_validate(category),
    )


@router.put(
    "/{category_id}",
    response_model=ApiResponse[ProductCategoryResponse],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Update product category (Phase 072)",
)
def update_category(
    category_id: uuid.UUID,
    data: ProductCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing product category."""
    category = ProductCategoryService.update_category(db, category_id, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductCategoryResponse.model_validate(category),
        message=f"Product category '{category.name}' updated successfully.",
    )


@router.delete(
    "/{category_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Delete product category (Phase 072)",
)
def delete_category(
    category_id: uuid.UUID,
    soft: bool = Query(default=True, description="Soft delete (deactivate) or hard delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete or deactivate a product category safely."""
    ProductCategoryService.delete_category(db, category_id, current_user, soft=soft)
    return ApiResponse(
        success=True,
        data={"id": str(category_id), "deleted": True, "soft": soft},
        message="Product category removed successfully.",
    )
