"""Products and Product Variants API Endpoints (Phases 071, 073, 074, 075, 076, 077, 078, 080).

Provides endpoints for product catalog and variant operations:
- GET /products: Paginated list of products with tax, unit, subscription, and margin
- POST /products: Create a new product
- GET /products/{id}: Get product details including margin and variants
- PUT /products/{id}: Update product details, price, cost, tax, unit, or subscription
- DELETE /products/{id}: Deactivate/delete product safely
- GET /products/{id}/variants: List variants of a product
- POST /products/{id}/variants: Create a variant for a product
- GET /products/variants/{variant_id}: Get variant details
- PUT /products/variants/{variant_id}: Update variant
- DELETE /products/variants/{variant_id}: Deactivate/delete variant
"""
import uuid
from typing import List, Optional
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
    ProductVariantCreate,
    ProductVariantResponse,
    ProductVariantUpdate,
)
from app.schemas.response import ApiResponse
from app.services.product import ProductService, ProductVariantService

router = APIRouter()


# ===========================================================================
# Product CRUD Endpoints
# ===========================================================================

@router.get(
    "",
    response_model=ApiResponse[ProductListResponse],
    dependencies=[Depends(require_permission("products:read"))],
    summary="List products (Phases 071, 076, 077, 080)",
)
def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    category_id: Optional[uuid.UUID] = Query(default=None, description="Filter by category ID"),
    is_subscription: Optional[bool] = Query(default=None, description="Filter by subscription flag"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated product catalog with derived margin, tax, unit, and subscription."""
    items, total = ProductService.get_products(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        is_subscription=is_subscription,
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
    summary="Create product (Phases 071, 073, 074, 075, 076, 077, 080)",
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product with selling price, unit cost, tax, unit, and subscription."""
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
    summary="Get product by ID (Phases 071, 076, 077, 078, 080)",
)
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of a single product including pricing, margin, and variants."""
    product = ProductService.get_product_by_id(db, product_id)
    return ApiResponse(
        success=True,
        data=ProductResponse.model_validate(product),
    )


@router.put(
    "/{product_id}",
    response_model=ApiResponse[ProductResponse],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Update product (Phases 071, 073, 074, 075, 076, 077, 080)",
)
def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update product information, pricing, cost, tax rate, unit, or subscription."""
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


# ===========================================================================
# Phase 078: Product Variants Endpoints
# ===========================================================================

@router.get(
    "/{product_id}/variants",
    response_model=ApiResponse[List[ProductVariantResponse]],
    dependencies=[Depends(require_permission("products:read"))],
    summary="List product variants (Phase 078)",
)
def list_product_variants(
    product_id: uuid.UUID,
    include_inactive: bool = Query(default=False, description="Include inactive variants"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List variants associated with a parent product."""
    variants = ProductVariantService.get_variants_by_product(db, product_id, include_inactive=include_inactive)
    return ApiResponse(
        success=True,
        data=[ProductVariantResponse.model_validate(v) for v in variants],
    )


@router.post(
    "/{product_id}/variants",
    response_model=ApiResponse[ProductVariantResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("products:write"))],
    summary="Create product variant (Phase 078, 079)",
)
def create_product_variant(
    product_id: uuid.UUID,
    data: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new variant under a parent product."""
    variant = ProductVariantService.create_variant(db, product_id, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductVariantResponse.model_validate(variant),
        message=f"Product variant '{variant.sku}' created successfully.",
    )


@router.get(
    "/variants/{variant_id}",
    response_model=ApiResponse[ProductVariantResponse],
    dependencies=[Depends(require_permission("products:read"))],
    summary="Get variant by ID (Phase 078)",
)
def get_variant(
    variant_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve variant details by ID."""
    variant = ProductVariantService.get_variant_by_id(db, variant_id)
    return ApiResponse(
        success=True,
        data=ProductVariantResponse.model_validate(variant),
    )


@router.put(
    "/variants/{variant_id}",
    response_model=ApiResponse[ProductVariantResponse],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Update product variant (Phase 078, 079)",
)
def update_variant(
    variant_id: uuid.UUID,
    data: ProductVariantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update variant information, price/cost override, or attributes."""
    variant = ProductVariantService.update_variant(db, variant_id, data, current_user)
    return ApiResponse(
        success=True,
        data=ProductVariantResponse.model_validate(variant),
        message=f"Product variant '{variant.sku}' updated successfully.",
    )


@router.delete(
    "/variants/{variant_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_permission("products:write"))],
    summary="Delete product variant (Phase 078)",
)
def delete_variant(
    variant_id: uuid.UUID,
    soft: bool = Query(default=True, description="Soft delete (deactivate) or hard delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate or delete a product variant."""
    ProductVariantService.delete_variant(db, variant_id, current_user, soft=soft)
    return ApiResponse(
        success=True,
        data={"id": str(variant_id), "deleted": True, "soft": soft},
        message="Product variant deactivated successfully.",
    )
