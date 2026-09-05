"""Backorders API Router (Phase 096)."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.backorder import (
    BackorderCreate,
    BackorderListResponse,
    BackorderResponse,
    BackorderStatusUpdate,
    BackorderCancelRequest,
)

from app.services.backorder import BackorderService

router = APIRouter(prefix="/backorders", tags=["Backorders"])


@router.get("", response_model=BackorderListResponse)
def list_backorders(
    product_id: Optional[UUID] = Query(None, description="Filter by product ID"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, FULFILLED, CANCELLED)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List backorders for current company."""
    return BackorderService.list_backorders(
        db=db,
        company_id=current_user.company_id,
        product_id=product_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=BackorderResponse, status_code=status.HTTP_201_CREATED)
def create_backorder(
    payload: BackorderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually record a backorder."""
    return BackorderService.create_backorder(
        db=db,
        company_id=current_user.company_id,
        product_id=payload.product_id,
        requested_quantity=payload.requested_quantity,
        allocated_quantity=payload.allocated_quantity,
        notes=payload.notes,
    )


@router.get("/{backorder_id}", response_model=BackorderResponse)
def get_backorder(
    backorder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch backorder details."""
    return BackorderService.get_backorder(
        db=db,
        backorder_id=backorder_id,
        company_id=current_user.company_id,
    )


@router.post("/{backorder_id}/cancel", response_model=BackorderResponse)
def cancel_backorder(
    backorder_id: UUID,
    payload: Optional[BackorderCancelRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    """Cancel an open backorder."""
    notes = payload.notes if payload else None
    return BackorderService.cancel_backorder(
        db=db,
        backorder_id=backorder_id,
        company_id=current_user.company_id,
        notes=notes,
    )
