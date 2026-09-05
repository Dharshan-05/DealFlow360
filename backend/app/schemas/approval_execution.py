"""Approval Execution Schemas (DealFlow360 B06: Phases 156–165).

Defines strongly-typed schemas for:
- Phase 156: Auto Approval
- Phase 157: Manager Approval
- Phase 158: Finance Approval
- Phase 159: Multi-Level Approval
- Phase 160: Approval Escalation
- Phase 161: Approval Timeout
- Phase 162: Approval Audit Trail
- Phase 163: Approval Notifications
- Phase 164: Approval Dashboard
- Phase 165: Approval Decision Engine

Strictly typed, Decimal-safe, multi-tenant isolated.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.approval_routing import (
    ApprovalChainType,
    ApprovalLevel,
    ComprehensiveApprovalEvaluationRequest,
    ComprehensiveApprovalEvaluationResponse,
)


# ==============================================================================
# Domain State Enums
# ==============================================================================

class ApprovalRequestStatus(str, Enum):
    """Lifecycle states for an approval request (Phases 156–165)."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED_FOR_REVISION = "RETURNED_FOR_REVISION"
    ESCALATED = "ESCALATED"
    TIMED_OUT = "TIMED_OUT"


class StepStatus(str, Enum):
    """Lifecycle states for an individual approval step (Phase 159)."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED_FOR_REVISION = "RETURNED_FOR_REVISION"
    SKIPPED = "SKIPPED"
    ESCALATED = "ESCALATED"


class ApprovalAction(str, Enum):
    """Actions recorded in immutable audit trails (Phase 162)."""
    CREATED = "CREATED"
    AUTO_APPROVED = "AUTO_APPROVED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED_FOR_REVISION = "RETURNED_FOR_REVISION"
    ESCALATED = "ESCALATED"
    TIMED_OUT = "TIMED_OUT"


class NotificationEventType(str, Enum):
    """Event types triggering internal notifications (Phase 163)."""
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    STEP_ACTIVATED = "STEP_ACTIVATED"
    MANAGER_APPROVAL_REQUIRED = "MANAGER_APPROVAL_REQUIRED"
    FINANCE_APPROVAL_REQUIRED = "FINANCE_APPROVAL_REQUIRED"
    APPROVAL_COMPLETED = "APPROVAL_COMPLETED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    RETURNED_FOR_REVISION = "RETURNED_FOR_REVISION"
    APPROVAL_ESCALATED = "APPROVAL_ESCALATED"
    APPROVAL_TIMED_OUT = "APPROVAL_TIMED_OUT"


# ==============================================================================
# Request & Response Payloads
# ==============================================================================

class ApprovalStepResponse(BaseModel):
    """Structured response representing an approval step (Phase 159)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    approval_request_id: uuid.UUID
    company_id: uuid.UUID
    step_number: int
    step_name: str
    required_level: str
    assigned_role: str
    status: str
    is_required: bool
    sla_hours: int
    due_at: Optional[datetime] = None
    actioned_by_id: Optional[uuid.UUID] = None
    actioned_at: Optional[datetime] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    escalated_to_level: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ApprovalAuditLogResponse(BaseModel):
    """Structured response for immutable audit events (Phase 162)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    approval_request_id: uuid.UUID
    company_id: uuid.UUID
    deal_reference: str
    step_number: Optional[int] = None
    approval_level: str
    action: str
    actor_id: Optional[uuid.UUID] = None
    previous_status: str
    new_status: str
    reason: Optional[str] = None
    context_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ApprovalNotificationResponse(BaseModel):
    """Structured response for domain notifications (Phase 163)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    approval_request_id: uuid.UUID
    company_id: uuid.UUID
    deal_reference: str
    event_type: str
    recipient_role: str
    recipient_user_id: Optional[uuid.UUID] = None
    title: str
    message: str
    is_read: bool
    created_at: datetime


class ApprovalRequestResponse(BaseModel):
    """Structured response representing the primary approval request entity."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    deal_reference: str
    deal_value: Decimal
    selling_price: Decimal
    unit_cost: Decimal
    requested_discount_pct: Decimal
    customer_id: Optional[uuid.UUID] = None
    status: str
    required_level: str
    required_chain_type: str
    current_step_number: int
    total_steps: int
    blended_risk_score: float
    blended_risk_classification: str
    routing_metadata: Dict[str, Any] = Field(default_factory=dict)
    submitted_by_id: Optional[uuid.UUID] = None
    decision_reason: Optional[str] = None
    final_actioned_by_id: Optional[uuid.UUID] = None
    final_actioned_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    steps: List[ApprovalStepResponse] = Field(default_factory=list)


# ==============================================================================
# Action Inputs
# ==============================================================================

class ApprovalSubmitRequest(BaseModel):
    """Payload for submitting a deal into the approval execution engine."""
    model_config = ConfigDict(from_attributes=True)

    deal_payload: ComprehensiveApprovalEvaluationRequest
    expiration_hours: int = Field(default=72, ge=1, le=720, description="Absolute expiration horizon in hours")


class ApprovalActionInput(BaseModel):
    """Payload for approving, rejecting, or returning an active approval step."""
    model_config = ConfigDict(from_attributes=True)

    reason: Optional[str] = Field(default=None, description="Explanation or justification for the decision")


class ApprovalEscalationInput(BaseModel):
    """Payload for explicitly escalating a step."""
    model_config = ConfigDict(from_attributes=True)

    reason: str = Field(description="Operational rationale for escalation")


# ==============================================================================
# Phase 164: Approval Dashboard Schemas
# ==============================================================================

class ApprovalStatusCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    count: int


class ApprovalLevelCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    level: str
    count: int


class ApprovalDashboardMetrics(BaseModel):
    """Real-time aggregated metrics for the approval dashboard (Phase 164)."""
    model_config = ConfigDict(from_attributes=True)

    company_id: uuid.UUID
    total_requests: int
    pending_count: int
    in_progress_count: int
    approved_count: int
    rejected_count: int
    returned_count: int
    escalated_count: int
    timed_out_count: int
    avg_approval_time_hours: float
    counts_by_status: List[ApprovalStatusCount]
    counts_by_level: List[ApprovalLevelCount]
    recent_requests: List[ApprovalRequestResponse]
    generated_at: datetime


# ==============================================================================
# Phase 165: Unified Decision Result
# ==============================================================================

class DecisionResult(BaseModel):
    """Authoritative decision output from the central Approval Decision Engine (Phase 165)."""
    model_config = ConfigDict(from_attributes=True)

    approval_request_id: uuid.UUID
    status: str
    decision: str
    current_level: str
    next_level: Optional[str] = None
    required_chain: str
    risk_score: float
    blended_risk_score: float
    audit_event_id: Optional[uuid.UUID] = None
    notification_event_id: Optional[uuid.UUID] = None
    message: str
