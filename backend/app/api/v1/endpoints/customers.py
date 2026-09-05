"""Customer API Endpoints (Phases 056–060).

Provides:
- Phase 056: Customer CRUD (GET, POST, PUT, DELETE)
- Phase 057: Customer Profile (GET /customers/{id})
- Phase 058: Customer Tier Management (PATCH /customers/{id}/tier)
- Phase 059: Customer Purchase History (GET/POST /customers/{id}/purchase-history)
- Phase 060: Customer Deal History (GET/POST /customers/{id}/deal-history)
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerTierUpdate,
    CustomerUpdate,
    DealHistoryCreate,
    DealHistoryResponse,
    PurchaseHistoryCreate,
    PurchaseHistoryResponse,
)
from app.schemas.response import ApiResponse
from app.services.customer import CustomerService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[CustomerListResponse],
    dependencies=[Depends(require_permission("customers:read"))],
    summary="List customers (Phase 056)",
)
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, code, or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve customers scoped to current organization."""
    customers, total = CustomerService.get_customers(
        db, current_user, skip=skip, limit=limit, search=search, is_active=is_active
    )
    items = [CustomerResponse.model_validate(c) for c in customers]
    return ApiResponse(
        success=True,
        data=CustomerListResponse(items=items, total=total, skip=skip, limit=limit),
    )


@router.post(
    "",
    response_model=ApiResponse[CustomerResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("customers:write"))],
    summary="Create customer (Phase 056)",
)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new customer account in the authenticated user's organization."""
    customer = CustomerService.create_customer(db, current_user, data)
    return ApiResponse(
        success=True,
        data=CustomerResponse.model_validate(customer),
        message=f"Customer '{customer.name}' created successfully",
    )


@router.get(
    "/{customer_id}",
    response_model=ApiResponse[CustomerResponse],
    dependencies=[Depends(require_permission("customers:read"))],
    summary="Get customer profile (Phase 057)",
)
def get_customer_profile(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve complete customer profile including tier details and metadata."""
    customer = CustomerService.get_customer(db, current_user, customer_id)
    return ApiResponse(
        success=True,
        data=CustomerResponse.model_validate(customer),
    )


@router.put(
    "/{customer_id}",
    response_model=ApiResponse[CustomerResponse],
    dependencies=[Depends(require_permission("customers:write"))],
    summary="Update customer (Phase 056)",
)
def update_customer(
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update editable fields of a customer account."""
    customer = CustomerService.update_customer(db, current_user, customer_id, data)
    return ApiResponse(
        success=True,
        data=CustomerResponse.model_validate(customer),
        message="Customer updated successfully",
    )


@router.patch(
    "/{customer_id}/tier",
    response_model=ApiResponse[CustomerResponse],
    dependencies=[Depends(require_permission("customers:write"))],
    summary="Assign customer discount tier (Phase 058)",
)
def update_customer_tier(
    customer_id: uuid.UUID,
    data: CustomerTierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reassign customer discount tier, enforcing tier validation and audit logging."""
    customer = CustomerService.update_customer_tier(db, current_user, customer_id, data.tier_id)
    return ApiResponse(
        success=True,
        data=CustomerResponse.model_validate(customer),
        message="Customer tier updated successfully",
    )


@router.delete(
    "/{customer_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_permission("customers:delete"))],
    summary="Delete customer (Phase 056)",
)
def delete_customer(
    customer_id: uuid.UUID,
    soft: bool = Query(True, description="Perform soft-delete (deactivate) if true"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete (deactivate) or delete a customer record."""
    CustomerService.delete_customer(db, current_user, customer_id, soft_delete=soft)
    return ApiResponse(
        success=True,
        data={"deleted": True, "customer_id": str(customer_id), "soft_delete": soft},
        message="Customer removed successfully",
    )


# ---------------------------------------------------------------------------
# Phase 059: Customer Purchase History Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{customer_id}/purchase-history",
    response_model=ApiResponse[List[PurchaseHistoryResponse]],
    dependencies=[Depends(require_permission("customers:read"))],
    summary="Get customer purchase history (Phase 059)",
)
def get_customer_purchase_history(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve verified purchase history records for a customer."""
    records = CustomerService.get_purchase_history(db, current_user, customer_id)
    items = [PurchaseHistoryResponse.model_validate(r) for r in records]
    return ApiResponse(
        success=True,
        data=items,
    )


@router.post(
    "/{customer_id}/purchase-history",
    response_model=ApiResponse[PurchaseHistoryResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("customers:write"))],
    summary="Add customer purchase history record (Phase 059)",
)
def create_customer_purchase_history(
    customer_id: uuid.UUID,
    data: PurchaseHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a purchase transaction for customer."""
    entry = CustomerService.create_purchase_history_entry(db, current_user, customer_id, data)
    return ApiResponse(
        success=True,
        data=PurchaseHistoryResponse.model_validate(entry),
        message="Purchase history entry recorded successfully",
    )


# ---------------------------------------------------------------------------
# Phase 060: Customer Deal History Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{customer_id}/deal-history",
    response_model=ApiResponse[List[DealHistoryResponse]],
    dependencies=[Depends(require_permission("customers:read"))],
    summary="Get customer deal history (Phase 060)",
)
def get_customer_deal_history(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve deal lifecycle history for a customer."""
    records = CustomerService.get_deal_history(db, current_user, customer_id)
    items = [DealHistoryResponse.model_validate(r) for r in records]
    return ApiResponse(
        success=True,
        data=items,
    )


@router.post(
    "/{customer_id}/deal-history",
    response_model=ApiResponse[DealHistoryResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("customers:write"))],
    summary="Add customer deal history record (Phase 060)",
)
def create_customer_deal_history(
    customer_id: uuid.UUID,
    data: DealHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a deal lifecycle event for customer."""
    entry = CustomerService.create_deal_history_entry(db, current_user, customer_id, data)
    return ApiResponse(
        success=True,
        data=DealHistoryResponse.model_validate(entry),
        message="Deal history entry recorded successfully",
    )
