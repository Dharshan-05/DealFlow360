"""Discount Governance Endpoints (Phases 101–105).

Provides REST APIs for:
- Phase 101: Discount Configuration
- Phase 102: Customer Discount Ceiling
- Phase 103: Category Discount Ceiling
- Phase 104: Product Discount Ceiling
- Phase 105: Sales Rep Authority Limit
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.discount_governance import (
    CategoryDiscountCeilingCreate,
    CategoryDiscountCeilingListResponse,
    CategoryDiscountCeilingResponse,
    CategoryDiscountCeilingUpdate,
    CustomerDiscountCeilingCreate,
    CustomerDiscountCeilingListResponse,
    CustomerDiscountCeilingResponse,
    CustomerDiscountCeilingUpdate,
    DiscountConfigurationCreate,
    DiscountConfigurationListResponse,
    DiscountConfigurationResponse,
    DiscountConfigurationUpdate,
    ProductDiscountCeilingCreate,
    ProductDiscountCeilingListResponse,
    ProductDiscountCeilingResponse,
    ProductDiscountCeilingUpdate,
    SalesRepAuthorityLimitCreate,
    SalesRepAuthorityLimitListResponse,
    SalesRepAuthorityLimitResponse,
    SalesRepAuthorityLimitUpdate,
)
from app.services.discount_governance import (
    CategoryDiscountCeilingService,
    CustomerDiscountCeilingService,
    DiscountConfigurationService,
    ProductDiscountCeilingService,
    SalesRepAuthorityLimitService,
)

router = APIRouter(prefix="/governance/discounts", tags=["Discount Governance"])


# ==============================================================================
# Phase 101: Discount Configuration Endpoints
# ==============================================================================

@router.get("/configurations", response_model=DiscountConfigurationListResponse)
def list_discount_configurations(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """List discount configurations for the authenticated company."""
    return DiscountConfigurationService.list(
        db=db,
        company_id=current_user.company_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/configurations",
    response_model=DiscountConfigurationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_discount_configuration(
    payload: DiscountConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Create a new company-wide baseline discount configuration."""
    return DiscountConfigurationService.create(
        db=db,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.get("/configurations/{config_id}", response_model=DiscountConfigurationResponse)
def get_discount_configuration(
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Get details of a specific discount configuration."""
    return DiscountConfigurationService.get(
        db=db,
        config_id=config_id,
        company_id=current_user.company_id,
    )


@router.put("/configurations/{config_id}", response_model=DiscountConfigurationResponse)
def update_discount_configuration(
    config_id: uuid.UUID,
    payload: DiscountConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Update a discount configuration."""
    return DiscountConfigurationService.update(
        db=db,
        config_id=config_id,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.delete("/configurations/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discount_configuration(
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Soft-deactivate a discount configuration."""
    DiscountConfigurationService.deactivate(
        db=db,
        config_id=config_id,
        company_id=current_user.company_id,
        current_user=current_user,
    )
    return None


# ==============================================================================
# Phase 102: Customer Discount Ceiling Endpoints
# ==============================================================================

@router.get("/customer-ceilings", response_model=CustomerDiscountCeilingListResponse)
def list_customer_discount_ceilings(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """List customer discount ceilings for the company."""
    return CustomerDiscountCeilingService.list(
        db=db,
        company_id=current_user.company_id,
        customer_id=customer_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/customer-ceilings",
    response_model=CustomerDiscountCeilingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_discount_ceiling(
    payload: CustomerDiscountCeilingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Create a customer discount ceiling."""
    return CustomerDiscountCeilingService.create(
        db=db,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.get("/customer-ceilings/{ceiling_id}", response_model=CustomerDiscountCeilingResponse)
def get_customer_discount_ceiling(
    ceiling_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Get customer discount ceiling details."""
    return CustomerDiscountCeilingService.get(
        db=db,
        ceiling_id=ceiling_id,
        company_id=current_user.company_id,
    )


@router.put("/customer-ceilings/{ceiling_id}", response_model=CustomerDiscountCeilingResponse)
def update_customer_discount_ceiling(
    ceiling_id: uuid.UUID,
    payload: CustomerDiscountCeilingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Update a customer discount ceiling."""
    return CustomerDiscountCeilingService.update(
        db=db,
        ceiling_id=ceiling_id,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.delete("/customer-ceilings/{ceiling_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_discount_ceiling(
    ceiling_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Soft-deactivate a customer discount ceiling."""
    CustomerDiscountCeilingService.deactivate(
        db=db,
        ceiling_id=ceiling_id,
        company_id=current_user.company_id,
        current_user=current_user,
    )
    return None


# ==============================================================================
# Phase 103: Category Discount Ceiling Endpoints
# ==============================================================================

@router.get("/category-ceilings", response_model=CategoryDiscountCeilingListResponse)
def list_category_discount_ceilings(
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """List product category discount ceilings."""
    return CategoryDiscountCeilingService.list(
        db=db,
        company_id=current_user.company_id,
        category_id=category_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/category-ceilings",
    response_model=CategoryDiscountCeilingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category_discount_ceiling(
    payload: CategoryDiscountCeilingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Create a product category discount ceiling."""
    return CategoryDiscountCeilingService.create(
        db=db,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.get("/category-ceilings/{ceiling_id}", response_model=CategoryDiscountCeilingResponse)
def get_category_discount_ceiling(
    ceiling_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Get category discount ceiling details."""
    return CategoryDiscountCeilingService.get(
        db=db,
        ceiling_id=ceiling_id,
        company_id=current_user.company_id,
    )


@router.put("/category-ceilings/{ceiling_id}", response_model=CategoryDiscountCeilingResponse)
def update_category_discount_ceiling(
    ceiling_id: uuid.UUID,
    payload: CategoryDiscountCeilingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Update a category discount ceiling."""
    return CategoryDiscountCeilingService.update(
        db=db,
        ceiling_id=ceiling_id,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.delete("/category-ceilings/{ceiling_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_discount_ceiling(
    ceiling_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Soft-deactivate a category discount ceiling."""
    CategoryDiscountCeilingService.deactivate(
        db=db,
        ceiling_id=ceiling_id,
        company_id=current_user.company_id,
        current_user=current_user,
    )
    return None


# ==============================================================================
# Phase 104: Product Discount Ceiling Endpoints
# ==============================================================================

@router.get("/product-ceilings", response_model=ProductDiscountCeilingListResponse)
def list_product_discount_ceilings(
    product_id: Optional[uuid.UUID] = Query(None, description="Filter by product ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """List product discount ceilings."""
    return ProductDiscountCeilingService.list(
        db=db,
        company_id=current_user.company_id,
        product_id=product_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/product-ceilings",
    response_model=ProductDiscountCeilingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_discount_ceiling(
    payload: ProductDiscountCeilingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Create a product discount ceiling."""
    return ProductDiscountCeilingService.create(
        db=db,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.get("/product-ceilings/{ceiling_id}", response_model=ProductDiscountCeilingResponse)
def get_product_discount_ceiling(
    ceiling_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Get product discount ceiling details."""
    return ProductDiscountCeilingService.get(
        db=db,
        ceiling_id=ceiling_id,
        company_id=current_user.company_id,
    )


@router.put("/product-ceilings/{ceiling_id}", response_model=ProductDiscountCeilingResponse)
def update_product_discount_ceiling(
    ceiling_id: uuid.UUID,
    payload: ProductDiscountCeilingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Update a product discount ceiling."""
    return ProductDiscountCeilingService.update(
        db=db,
        ceiling_id=ceiling_id,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.delete("/product-ceilings/{ceiling_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_discount_ceiling(
    ceiling_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Soft-deactivate a product discount ceiling."""
    ProductDiscountCeilingService.deactivate(
        db=db,
        ceiling_id=ceiling_id,
        company_id=current_user.company_id,
        current_user=current_user,
    )
    return None


# ==============================================================================
# Phase 105: Sales Rep Authority Limit Endpoints
# ==============================================================================

@router.get("/sales-rep-limits", response_model=SalesRepAuthorityLimitListResponse)
def list_sales_rep_authority_limits(
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user/sales rep ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """List sales rep authority limits."""
    return SalesRepAuthorityLimitService.list(
        db=db,
        company_id=current_user.company_id,
        user_id=user_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/sales-rep-limits",
    response_model=SalesRepAuthorityLimitResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sales_rep_authority_limit(
    payload: SalesRepAuthorityLimitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Create a sales rep authority limit.

    Strict security rule: A Sales Rep is forbidden from configuring or self-escalating their own limit.
    """
    # Self-modification prohibition check: Cannot configure or escalate one's own discount limit
    user_role_names = [r.name for r in current_user.roles]
    if payload.user_id == current_user.id and "Admin" not in user_role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users cannot assign or modify their own discount authority limits.",
        )

    return SalesRepAuthorityLimitService.create(
        db=db,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.get("/sales-rep-limits/{limit_id}", response_model=SalesRepAuthorityLimitResponse)
def get_sales_rep_authority_limit(
    limit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:read")),
):
    """Get sales rep authority limit details."""
    return SalesRepAuthorityLimitService.get(
        db=db,
        limit_id=limit_id,
        company_id=current_user.company_id,
    )


@router.put("/sales-rep-limits/{limit_id}", response_model=SalesRepAuthorityLimitResponse)
def update_sales_rep_authority_limit(
    limit_id: uuid.UUID,
    payload: SalesRepAuthorityLimitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Update a sales rep authority limit.

    Strict security rule: A Sales Rep cannot self-modify their authority limit.
    """
    existing_limit = SalesRepAuthorityLimitService.get(db, limit_id, current_user.company_id)
    user_role_names = [r.name for r in current_user.roles]
    if existing_limit.user_id == current_user.id and "Admin" not in user_role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users cannot assign or modify their own discount authority limits.",
        )

    return SalesRepAuthorityLimitService.update(
        db=db,
        limit_id=limit_id,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.delete("/sales-rep-limits/{limit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_rep_authority_limit(
    limit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discounts:write")),
):
    """Soft-deactivate a sales rep authority limit."""
    existing_limit = SalesRepAuthorityLimitService.get(db, limit_id, current_user.company_id)
    user_role_names = [r.name for r in current_user.roles]
    if existing_limit.user_id == current_user.id and "Admin" not in user_role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users cannot assign or modify their own discount authority limits.",
        )

    SalesRepAuthorityLimitService.deactivate(
        db=db,
        limit_id=limit_id,
        company_id=current_user.company_id,
        current_user=current_user,
    )
    return None
