"""Fulfillments API Router (Phases 097 & 098)."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.fulfillment import (
    FulfillmentCreate,
    FulfillmentDeliveryStatusUpdate,
    FulfillmentListResponse,
    FulfillmentResponse,
)
from app.services.fulfillment import FulfillmentService

router = APIRouter(prefix="/fulfillments", tags=["Fulfillments"])


@router.get("", response_model=FulfillmentListResponse)
def list_fulfillments(
    product_id: Optional[UUID] = Query(None, description="Filter by product ID"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, PARTIALLY_FULFILLED, FULFILLED)"),
    delivery_status: Optional[str] = Query(
        None, description="Filter by delivery status (NOT_STARTED, READY, DISPATCHED, IN_TRANSIT, DELIVERED, CANCELLED)"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List fulfillments for current company."""
    return FulfillmentService.list_fulfillments(
        db=db,
        company_id=current_user.company_id,
        product_id=product_id,
        status=status,
        delivery_status=delivery_status,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=FulfillmentResponse, status_code=status.HTTP_201_CREATED)
def create_fulfillment(
    payload: FulfillmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create fulfillment, atomically allocate & reserve stock across warehouses, and record backorders for shortages."""
    return FulfillmentService.create_fulfillment(
        db=db,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )


@router.get("/{fulfillment_id}", response_model=FulfillmentResponse)
def get_fulfillment(
    fulfillment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch fulfillment details."""
    return FulfillmentService.get_fulfillment(
        db=db,
        fulfillment_id=fulfillment_id,
        company_id=current_user.company_id,
    )


@router.put("/{fulfillment_id}/delivery-status", response_model=FulfillmentResponse)
def update_delivery_status(
    fulfillment_id: UUID,
    payload: FulfillmentDeliveryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Advance or update delivery status obeying the strict Delivery State Machine."""
    return FulfillmentService.update_delivery_status(
        db=db,
        fulfillment_id=fulfillment_id,
        company_id=current_user.company_id,
        payload=payload,
        current_user=current_user,
    )
