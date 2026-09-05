"""Products API Endpoints (Phases 071, 073, 074, 075).

Provides endpoints for product catalog operations:
- GET /products: Paginated list of products with margin computations
- POST /products: Create a new product with selling price and cost
- GET /products/{id}: Get product details including margin
- PUT /products/{id}: Update product details, price, or cost
- DELETE /products/{id}: Deactivate/delete product safely
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.schemas.response import ApiResponse
from app.services.product import ProductService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[ProductListResponse],
    dependencies=[Depends(require_permission("products:read"))],
    summary="List products (Phase 071)",
)
def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    category_id: Optional[uuid.UUID] = Query(default=None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated product catalog with derived margin figures."""
    items, total = ProductService.get_products(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        is_active=is_active,
    )
    product_responses = [ProductResponse.model_validate(p) for p in items]
    return ApiResponse(
        success=True,
        data=ProductListResponse(
            items=product_responses,
            total=total,
            skip=skip,
            limit=limit,
        ),
    )


@router.post(
    "",
    response_model=ApiResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:write"))],
    summary="Create product (Phase 071, 073, 074, 075)",
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product with selling price and unit cost."""
    product = ProductService.create_product(db, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductResponse.model_validate(product),
        message=f"Product '{product.name}' ({product.sku}) created successfully.",
    )


@router.get(
    "/{product_id}",
    response_model=ApiResponse[ProductResponse],
    dependencies=[Depends(require_permission("products:read"))],
    summary="Get product by ID (Phase 071)",
)
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of a single product including pricing and margin."""
    product = ProductService.get_product_by_id(db, product_id)
    return ApiResponse(
        success=True,
        data=ProductResponse.model_validate(product),
    )


@router.put(
    "/{product_id}",
    response_model=ApiResponse[ProductResponse],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Update product (Phase 071, 073, 074, 075)",
)
def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update product information, pricing, or cost."""
    product = ProductService.update_product(db, product_id, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductResponse.model_validate(product),
        message=f"Product '{product.name}' ({product.sku}) updated successfully.",
    )


@router.delete(
    "/{product_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Delete product (Phase 071)",
)
def delete_product(
    product_id: uuid.UUID,
    soft: bool = Query(default=True, description="Soft delete (deactivate) or hard delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate or delete a product safely."""
    ProductService.delete_product(db, product_id, current_user, soft=soft)
    return ApiResponse(
        success=True,
        data={"id": str(product_id), "deleted": True, "soft": soft},
        message="Product deactivated successfully.",
    )
