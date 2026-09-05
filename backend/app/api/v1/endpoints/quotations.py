"""Quotation Management Endpoints (DealFlow360 B09: Phases 186–195).

Provides tenant-isolated, RBAC-governed endpoints for quotation lifecycle,
itemized products, line/overall discounts, tax, and real-time margin computations.
"""
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.quotation import (
    QuotationCalculationRequest,
    QuotationCalculationResponse,
    QuotationCreate,
    QuotationDetailResponse,
    QuotationSummaryResponse,
    QuotationUpdate,
)
from app.schemas.response import ApiResponse
from app.services.quotation import QuotationService

router = APIRouter(prefix="/quotations", tags=["Quotation Engine (B09: Phases 186–195)"])


@router.post(
    "",
    response_model=ApiResponse[QuotationDetailResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Create Quotation (Phase 186–195)",
)
def create_quotation(
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new commercial quotation with line items, tax, discounts, and real-time margins."""
    quotation = QuotationService.create_quotation(
        db=db,
        current_user=current_user,
        payload=payload,
    )
    return ApiResponse(
        data=quotation,
        message=f"Quotation {quotation.quotation_number} created successfully",
    )


@router.get(
    "",
    response_model=ApiResponse[List[QuotationSummaryResponse]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:read"))],
    summary="List Quotations (Phase 186)",
)
def list_quotations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    customer_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated, tenant-isolated list of commercial quotations."""
    items, total = QuotationService.list_quotations(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        status=status,
        search=search,
        customer_id=customer_id,
    )
    return ApiResponse(
        data=items,
        message=f"Retrieved {len(items)} quotations (total {total})",
    )


@router.get(
    "/{quotation_id}",
    response_model=ApiResponse[QuotationDetailResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:read"))],
    summary="Get Quotation Detail (Phase 186)",
)
def get_quotation(
    quotation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full quotation details including itemized lines, discounts, and margin breakdown."""
    quotation = QuotationService.get_quotation(
        db=db,
        current_user=current_user,
        quotation_id=quotation_id,
    )
    return ApiResponse(
        data=quotation,
        message="Quotation retrieved successfully",
    )


@router.put(
    "/{quotation_id}",
    response_model=ApiResponse[QuotationDetailResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Update Quotation (Phase 186–195)",
)
def update_quotation(
    quotation_id: uuid.UUID,
    payload: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update draft quotation metadata and line items, recalculating all financials."""
    quotation = QuotationService.update_quotation(
        db=db,
        current_user=current_user,
        quotation_id=quotation_id,
        payload=payload,
    )
    return ApiResponse(
        data=quotation,
        message=f"Quotation {quotation.quotation_number} updated successfully",
    )


@router.post(
    "/{quotation_id}/cancel",
    response_model=ApiResponse[QuotationDetailResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Cancel Quotation (Phase 186)",
)
def cancel_quotation(
    quotation_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition quotation to CANCELLED status."""
    quotation = QuotationService.cancel_quotation(
        db=db,
        current_user=current_user,
        quotation_id=quotation_id,
        reason=reason,
    )
    return ApiResponse(
        data=quotation,
        message=f"Quotation {quotation.quotation_number} cancelled",
    )


@router.delete(
    "/{quotation_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Delete Quotation (Phase 186)",
)
def delete_quotation(
    quotation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a quotation in DRAFT or CANCELLED status."""
    QuotationService.delete_quotation(
        db=db,
        current_user=current_user,
        quotation_id=quotation_id,
    )
    return ApiResponse(
        data={"deleted": True, "id": str(quotation_id)},
        message="Quotation deleted successfully",
    )


@router.post(
    "/calculate",
    response_model=ApiResponse[QuotationCalculationResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:read"))],
    summary="Dry-Run Real-Time Quotation Calculation (Phase 190–195)",
)
def calculate_quotation(
    payload: QuotationCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dry-run calculate line amounts, discounts, taxes, and real-time margins without persistence."""
    result = QuotationService.calculate_transient(
        db=db,
        current_user=current_user,
        payload=payload,
    )
    return ApiResponse(
        data=result,
        message="Quotation calculated successfully",
    )
