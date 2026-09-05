"""Quotation Management Endpoints (DealFlow360 B09 & B10: Phases 186–205).

Provides tenant-isolated, RBAC-governed endpoints for quotation lifecycle,
itemized products, discounts, taxes, real-time margins, versioning, approvals,
PDF generation, email dispatch, tracking, acceptance, rejection, and deal conversion.
"""
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.quotation import (
    QuotationAcceptRequest,
    QuotationAcceptResponse,
    QuotationApprovalSubmitRequest,
    QuotationApprovalSubmitResponse,
    QuotationCalculationRequest,
    QuotationCalculationResponse,
    QuotationConvertDealRequest,
    QuotationConvertDealResponse,
    QuotationCreate,
    QuotationDetailResponse,
    QuotationEmailRequest,
    QuotationEmailResponse,
    QuotationExpireRequest,
    QuotationRejectRequest,
    QuotationRejectResponse,
    QuotationSendLogResponse,
    QuotationStatusUpdate,
    QuotationSummaryResponse,
    QuotationUpdate,
    QuotationVersionCreate,
    QuotationVersionResponse,
)
from app.schemas.response import ApiResponse
from app.services.quotation import (
    QuotationAcceptanceService,
    QuotationApprovalService,
    QuotationDealConversionService,
    QuotationEmailService,
    QuotationExpirationService,
    QuotationPdfService,
    QuotationRejectionService,
    QuotationSendTrackingService,
    QuotationService,
    QuotationStatusTransitionValidator,
    QuotationVersioningService,
)

router = APIRouter(prefix="/quotations", tags=["Quotation Engine (B09 & B10: Phases 186–205)"])


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


# ==============================================================================
# Phase 196: Quotation Status Transition
# ==============================================================================

@router.patch(
    "/{quotation_id}/status",
    response_model=ApiResponse[QuotationDetailResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Transition Quotation Status (Phase 196)",
)
def transition_quotation_status(
    quotation_id: uuid.UUID,
    payload: QuotationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explicitly transition quotation status through centralized state machine validator."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    prev = quotation.status
    QuotationStatusTransitionValidator.validate_transition(prev, payload.status.value)

    quotation.status = payload.status.value
    QuotationStatusTransitionValidator.record_transition_audit(
        db=db,
        quotation=quotation,
        actor=current_user,
        previous_status=prev,
        new_status=payload.status.value,
        reason=payload.reason,
    )
    db.commit()
    db.refresh(quotation)
    return ApiResponse(
        data=QuotationService._to_detail_dto(quotation),
        message=f"Quotation {quotation.quotation_number} status updated to {payload.status.value}",
    )


# ==============================================================================
# Phase 197: Quotation Versioning & Revisions
# ==============================================================================

@router.post(
    "/{quotation_id}/versions",
    response_model=ApiResponse[QuotationVersionResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Create Quotation Revision/Version (Phase 197)",
)
def create_quotation_version(
    quotation_id: uuid.UUID,
    payload: QuotationVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Snapshot current quotation state into immutable history and increment active version."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    version = QuotationVersioningService.create_revision(
        db=db,
        quotation=quotation,
        actor=current_user,
        change_reason=payload.change_reason,
    )
    db.commit()
    db.refresh(version)
    return ApiResponse(
        data=QuotationVersionResponse.model_validate(version),
        message=f"Created snapshot version v{version.version_number} for {quotation.quotation_number}",
    )


@router.get(
    "/{quotation_id}/versions",
    response_model=ApiResponse[List[QuotationVersionResponse]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:read"))],
    summary="List Quotation Versions (Phase 197)",
)
def list_quotation_versions(
    quotation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all immutable historical snapshot versions for a quotation."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    versions = QuotationVersioningService.list_versions(
        db=db,
        company_id=current_user.company_id,
        quotation_id=quotation.id,
    )
    return ApiResponse(
        data=[QuotationVersionResponse.model_validate(v) for v in versions],
        message=f"Retrieved {len(versions)} historical versions",
    )


# ==============================================================================
# Phase 198: Quotation Expiration
# ==============================================================================

@router.post(
    "/{quotation_id}/expire",
    response_model=ApiResponse[QuotationDetailResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Expire Quotation (Phase 198)",
)
def expire_quotation(
    quotation_id: uuid.UUID,
    payload: Optional[QuotationExpireRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explicitly trigger or evaluate quotation expiration."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    reason = payload.reason if payload else "Manual expiration request"
    updated = QuotationExpirationService.expire_manually(
        db=db,
        quotation=quotation,
        actor=current_user,
        reason=reason,
    )
    db.commit()
    db.refresh(updated)
    return ApiResponse(
        data=QuotationService._to_detail_dto(updated),
        message=f"Quotation {updated.quotation_number} marked EXPIRED",
    )


# ==============================================================================
# Phase 199: Quote Approval Integration
# ==============================================================================

@router.post(
    "/{quotation_id}/submit-approval",
    response_model=ApiResponse[QuotationApprovalSubmitResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Submit Quotation for Approval (Phase 199)",
)
def submit_quotation_for_approval(
    quotation_id: uuid.UUID,
    payload: Optional[QuotationApprovalSubmitRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit quotation financials to existing B05/B06 Approval Decision Engine."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    notes = payload.notes if payload else None
    approval_req, auto_approved = QuotationApprovalService.submit_for_approval(
        db=db,
        quotation=quotation,
        actor=current_user,
        notes=notes,
    )
    db.commit()
    db.refresh(quotation)
    return ApiResponse(
        data=QuotationApprovalSubmitResponse(
            quotation_id=quotation.id,
            approval_request_id=approval_req.id,
            status=quotation.status,
            required_level=approval_req.required_level,
            auto_approved=auto_approved,
            message=(
                f"Quotation auto-approved immediately ({approval_req.required_level})"
                if auto_approved
                else f"Quotation submitted for {approval_req.required_level} approval"
            ),
        ),
        message="Approval evaluation completed successfully",
    )


# ==============================================================================
# Phase 200: Quote PDF Generation
# ==============================================================================

@router.get(
    "/{quotation_id}/pdf",
    dependencies=[Depends(require_permission("quotations:read"))],
    summary="Generate Quotation PDF (Phase 200)",
)
def generate_quotation_pdf(
    quotation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compile and stream production-quality vector PDF for active quotation version."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    pdf_bytes = QuotationPdfService.generate_pdf(quotation)
    filename = f"Quotation-{quotation.quotation_number}-v{quotation.version_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ==============================================================================
# Phase 201: Quote Email Dispatch
# ==============================================================================

@router.post(
    "/{quotation_id}/email",
    response_model=ApiResponse[QuotationEmailResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Email Quotation with PDF Attachment (Phase 201)",
)
def email_quotation(
    quotation_id: uuid.UUID,
    payload: QuotationEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispatch quotation email with attached PDF, recording dispatch and token."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    result = QuotationEmailService.send_quotation_email(
        db=db,
        quotation=quotation,
        recipient_email=payload.recipient_email,
        actor=current_user,
        subject=payload.subject,
        notes=payload.notes,
    )
    db.commit()
    return ApiResponse(
        data=result,
        message=result.message,
    )


# ==============================================================================
# Phase 202: Quote Send Tracking & History
# ==============================================================================

@router.get(
    "/{quotation_id}/send-history",
    response_model=ApiResponse[List[QuotationSendLogResponse]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:read"))],
    summary="Get Quotation Send History (Phase 202)",
)
def get_quotation_send_history(
    quotation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve audit history of quotation email dispatches and view timestamps."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    logs = QuotationSendTrackingService.get_send_history(
        db=db,
        company_id=current_user.company_id,
        quotation_id=quotation.id,
    )
    return ApiResponse(
        data=[QuotationSendLogResponse.model_validate(l) for l in logs],
        message=f"Retrieved {len(logs)} dispatch records",
    )


@router.post(
    "/{quotation_id}/track-view",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:read"))],
    summary="Track Quotation View Event (Phase 202)",
)
def track_quotation_view(
    quotation_id: uuid.UUID,
    token: Optional[str] = Query(None, description="Tracking token from email link"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record customer viewing or opening the quotation."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    updated = QuotationSendTrackingService.record_view(
        db=db,
        quotation=quotation,
        tracking_token=token,
    )
    db.commit()
    return ApiResponse(
        data={"viewed": True, "status": quotation.status, "updated": updated},
        message="Quotation view event recorded",
    )


# ==============================================================================
# Phase 203: Quote Acceptance
# ==============================================================================

@router.post(
    "/{quotation_id}/accept",
    response_model=ApiResponse[QuotationAcceptResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Accept Quotation (Phase 203)",
)
def accept_quotation(
    quotation_id: uuid.UUID,
    payload: Optional[QuotationAcceptRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept quotation proposal, transitioning status to ACCEPTED."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    notes = payload.acceptance_notes if payload else None
    result = QuotationAcceptanceService.accept_quotation(
        db=db,
        quotation=quotation,
        actor=current_user,
        acceptance_notes=notes,
    )
    db.commit()
    return ApiResponse(
        data=result,
        message=result.message,
    )


# ==============================================================================
# Phase 204: Quote Rejection
# ==============================================================================

@router.post(
    "/{quotation_id}/reject",
    response_model=ApiResponse[QuotationRejectResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Reject Quotation (Phase 204)",
)
def reject_quotation(
    quotation_id: uuid.UUID,
    payload: QuotationRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject quotation proposal with mandatory justification, transitioning status to REJECTED."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    result = QuotationRejectionService.reject_quotation(
        db=db,
        quotation=quotation,
        actor=current_user,
        reason=payload.reason,
    )
    db.commit()
    return ApiResponse(
        data=result,
        message=result.message,
    )


# ==============================================================================
# Phase 205: Quote Conversion to Deal
# ==============================================================================

@router.post(
    "/{quotation_id}/convert",
    response_model=ApiResponse[QuotationConvertDealResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("quotations:write"))],
    summary="Convert Accepted Quotation to Deal (Phase 205)",
)
def convert_quotation_to_deal(
    quotation_id: uuid.UUID,
    payload: Optional[QuotationConvertDealRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convert an ACCEPTED quotation into an official CustomerDealHistory deal record."""
    quotation = QuotationService.get_quotation_entity(db, current_user, quotation_id)
    title_override = payload.title_override if payload else None
    notes = payload.notes if payload else None
    deal = QuotationDealConversionService.convert_to_deal(
        db=db,
        quotation=quotation,
        actor=current_user,
        title_override=title_override,
        notes=notes,
    )
    db.commit()
    db.refresh(deal)
    return ApiResponse(
        data=QuotationConvertDealResponse(
            quotation_id=quotation.id,
            deal_id=deal.id,
            deal_code=deal.deal_code,
            deal_value=deal.deal_value,
            status=deal.status,
            converted_at=quotation.converted_at or datetime.now(timezone.utc),
            message=f"Quotation {quotation.quotation_number} converted to Deal {deal.deal_code} successfully",
        ),
        message="Quotation converted to Deal successfully",
    )
