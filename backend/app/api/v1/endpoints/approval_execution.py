"""Approval Execution API Endpoints (DealFlow360 B06: Phases 156–165).

Provides tenant-isolated, RBAC-protected API endpoints for:
- Phase 156: Auto Approval (POST /api/v1/approvals/requests/{id}/auto-approve)
- Phase 157: Manager Approval (POST /api/v1/approvals/requests/{id}/approve)
- Phase 158: Finance Approval (POST /api/v1/approvals/requests/{id}/approve)
- Phase 159: Multi-Level Approval (POST /api/v1/approvals/requests)
- Phase 160: Approval Escalation (POST /api/v1/approvals/requests/{id}/escalate)
- Phase 161: Approval Timeout (POST /api/v1/approvals/requests/check-timeouts)
- Phase 162: Approval Audit Trail (GET /api/v1/approvals/requests/{id}/audit)
- Phase 163: Approval Notifications (GET /api/v1/approvals/notifications)
- Phase 164: Approval Dashboard (GET /api/v1/approvals/dashboard)
- Phase 165: Approval Decision Engine (POST /api/v1/approvals/decision)
"""
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.approval_execution import (
    ApprovalActionInput,
    ApprovalAuditLogResponse,
    ApprovalDashboardMetrics,
    ApprovalEscalationInput,
    ApprovalNotificationResponse,
    ApprovalRequestResponse,
    ApprovalSubmitRequest,
    DecisionResult,
)
from app.schemas.response import ApiResponse
from app.services.approval_execution import (
    ApprovalAuditService,
    ApprovalDashboardService,
    ApprovalDecisionEngine,
    ApprovalNotificationService,
)

router = APIRouter(prefix="/approvals", tags=["Approval Execution Engine (B06: Phases 156–165)"])


# ==============================================================================
# Phase 159 & 165: Submit Request
# ==============================================================================

@router.post(
    "/requests",
    response_model=ApiResponse[ApprovalRequestResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("discounts:create"))],
    summary="Submit deal for approval evaluation (Phases 156 & 159)",
)
def submit_approval_request(
    payload: ApprovalSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit deal payload, compute B05 routing, initialize approval chain, and evaluate auto-approval."""
    req = ApprovalDecisionEngine.submit_for_approval(
        db=db,
        company_id=current_user.company_id,
        request_payload=payload.deal_payload,
        actor=current_user,
        expiration_hours=payload.expiration_hours,
    )
    return ApiResponse(
        success=True,
        data=ApprovalRequestResponse.model_validate(req),
    )


# ==============================================================================
# Phase 156: Auto Approval
# ==============================================================================

@router.post(
    "/requests/{id}/auto-approve",
    response_model=ApiResponse[DecisionResult],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Execute verified auto-approval (Phase 156)",
)
def execute_auto_approval(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Automatically mark request as APPROVED if and only if B05 routing determined NO_APPROVAL_REQUIRED."""
    res = ApprovalDecisionEngine.execute_auto_approval(
        db=db,
        company_id=current_user.company_id,
        approval_request_id=id,
        actor=current_user,
    )
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Phases 157 & 158: Approve Step (Manager & Finance)
# ==============================================================================

@router.post(
    "/requests/{id}/approve",
    response_model=ApiResponse[DecisionResult],
    dependencies=[Depends(require_permission("discounts:update"))],
    summary="Approve active approval step (Phases 157 & 158)",
)
def approve_step(
    id: uuid.UUID,
    payload: Optional[ApprovalActionInput] = None,
    step_number: Optional[int] = Query(default=None, description="Optional step number target"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve currently active step in chain; enforces RBAC role matching for Manager / Finance."""
    reason = payload.reason if payload else "Approved"
    res = ApprovalDecisionEngine.execute_approval_decision(
        db=db,
        company_id=current_user.company_id,
        approval_request_id=id,
        actor=current_user,
        decision="APPROVED",
        reason=reason,
        target_step_number=step_number,
    )
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Rejection & Return for Revision Endpoints
# ==============================================================================

@router.post(
    "/requests/{id}/reject",
    response_model=ApiResponse[DecisionResult],
    dependencies=[Depends(require_permission("discounts:update"))],
    summary="Reject approval request (Phase 159)",
)
def reject_step(
    id: uuid.UUID,
    payload: ApprovalActionInput,
    step_number: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject proposal at active step, transitioning entire approval to REJECTED."""
    res = ApprovalDecisionEngine.execute_approval_decision(
        db=db,
        company_id=current_user.company_id,
        approval_request_id=id,
        actor=current_user,
        decision="REJECTED",
        reason=payload.reason,
        target_step_number=step_number,
    )
    return ApiResponse(
        success=True,
        data=res,
    )


@router.post(
    "/requests/{id}/return",
    response_model=ApiResponse[DecisionResult],
    dependencies=[Depends(require_permission("discounts:update"))],
    summary="Return proposal for revision (Phase 159)",
)
def return_for_revision(
    id: uuid.UUID,
    payload: ApprovalActionInput,
    step_number: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return proposal for terms revision, transitioning request to RETURNED_FOR_REVISION."""
    res = ApprovalDecisionEngine.execute_approval_decision(
        db=db,
        company_id=current_user.company_id,
        approval_request_id=id,
        actor=current_user,
        decision="RETURNED_FOR_REVISION",
        reason=payload.reason,
        target_step_number=step_number,
    )
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Phase 160: Approval Escalation
# ==============================================================================

@router.post(
    "/requests/{id}/escalate",
    response_model=ApiResponse[DecisionResult],
    dependencies=[Depends(require_permission("discounts:update"))],
    summary="Escalate approval step to higher authority tier (Phase 160)",
)
def escalate_request(
    id: uuid.UUID,
    payload: ApprovalEscalationInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Escalate active approval step to next higher authority tier in hierarchy."""
    res = ApprovalDecisionEngine.escalate_request(
        db=db,
        company_id=current_user.company_id,
        approval_request_id=id,
        actor=current_user,
        reason=payload.reason,
    )
    return ApiResponse(
        success=True,
        data=res,
    )


# ==============================================================================
# Phase 161: Approval Timeout
# ==============================================================================

@router.post(
    "/requests/check-timeouts",
    response_model=ApiResponse[List[uuid.UUID]],
    dependencies=[Depends(require_permission("discounts:update"))],
    summary="Scan and apply approval timeouts (Phase 161)",
)
def check_timeouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check for expired approval requests past their expiration horizon and mark as TIMED_OUT."""
    timed_out_ids = ApprovalDecisionEngine.check_and_apply_timeouts(
        db=db,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        success=True,
        data=timed_out_ids,
    )


# ==============================================================================
# Phase 162: Approval Audit Trail
# ==============================================================================

@router.get(
    "/requests/{id}/audit",
    response_model=ApiResponse[List[ApprovalAuditLogResponse]],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Get immutable approval audit trail (Phase 162)",
)
def get_approval_audit_trail(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve complete, immutable chronological audit trail for the approval request."""
    logs = ApprovalAuditService.get_audit_trail(
        db=db,
        company_id=current_user.company_id,
        approval_request_id=id,
    )
    return ApiResponse(
        success=True,
        data=[ApprovalAuditLogResponse.model_validate(l) for l in logs],
    )


# ==============================================================================
# Phase 163: Approval Notifications
# ==============================================================================

@router.get(
    "/notifications",
    response_model=ApiResponse[List[ApprovalNotificationResponse]],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Get approval notifications (Phase 163)",
)
def list_notifications(
    only_unread: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve domain approval notifications for authenticated tenant."""
    notifs = ApprovalNotificationService.list_notifications(
        db=db,
        company_id=current_user.company_id,
        user=current_user,
        only_unread=only_unread,
    )
    return ApiResponse(
        success=True,
        data=[ApprovalNotificationResponse.model_validate(n) for n in notifs],
    )


# ==============================================================================
# Phase 164: Approval Dashboard
# ==============================================================================

@router.get(
    "/dashboard",
    response_model=ApiResponse[ApprovalDashboardMetrics],
    dependencies=[Depends(require_permission("discounts:read"))],
    summary="Get approval execution dashboard metrics (Phase 164)",
)
def get_approval_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve aggregated approval statistics, status distributions, and active queue counts."""
    metrics = ApprovalDashboardService.get_dashboard_metrics(
        db=db,
        company_id=current_user.company_id,
    )
    return ApiResponse(
        success=True,
        data=metrics,
    )


# ==============================================================================
# Phase 165: Central Approval Decision Engine Unified Endpoint
# ==============================================================================

@router.post(
    "/decision",
    response_model=ApiResponse[DecisionResult],
    dependencies=[Depends(require_permission("discounts:update"))],
    summary="Central Approval Decision Engine entrypoint (Phase 165)",
)
def execute_central_decision(
    approval_request_id: uuid.UUID,
    decision: str = Query(description="'APPROVED', 'REJECTED', or 'RETURNED_FOR_REVISION'"),
    reason: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute authoritative decision via central Approval Decision Engine."""
    res = ApprovalDecisionEngine.execute_approval_decision(
        db=db,
        company_id=current_user.company_id,
        approval_request_id=approval_request_id,
        actor=current_user,
        decision=decision.upper(),
        reason=reason,
    )
    return ApiResponse(
        success=True,
        data=res,
    )
