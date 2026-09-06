"""Approval Execution Services (DealFlow360 B06: Phases 156–165).

Implements the complete approval execution engine:
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

Strictly isolated by company_id. Safe database transactions with immutable audit logging.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import ApplicationError
from app.models.approval_execution import (
    ApprovalAuditLog,
    ApprovalNotification,
    ApprovalRequest,
    ApprovalStep,
)
from app.models.user import User
from app.schemas.approval_execution import (
    ApprovalAction,
    ApprovalDashboardMetrics,
    ApprovalLevelCount,
    ApprovalRequestResponse,
    ApprovalRequestStatus,
    ApprovalStatusCount,
    DecisionResult,
    NotificationEventType,
    StepStatus,
)
from app.schemas.approval_routing import (
    ApprovalChainDefinition,
    ApprovalChainType,
    ApprovalLevel,
    ComprehensiveApprovalEvaluationRequest,
    ComprehensiveApprovalEvaluationResponse,
)
from app.services.approval_routing import (
    ApprovalChainService,
    ApprovalLevelHierarchyService,
    BlendedRiskScoreService,
)
from app.services.rbac import RBACRoleNames, RBACService


# ==============================================================================
# Phase 162: Approval Audit Service
# ==============================================================================

class ApprovalAuditService:
    """Service writing immutable, append-only approval audit trail entries (Phase 162)."""

    @classmethod
    def record(
        cls,
        db: Session,
        approval_request: ApprovalRequest,
        action: ApprovalAction,
        approval_level: str,
        previous_status: str,
        new_status: str,
        actor_id: Optional[uuid.UUID] = None,
        step_number: Optional[int] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApprovalAuditLog:
        """Create and flush an append-only audit log record."""
        log = ApprovalAuditLog(
            approval_request_id=approval_request.id,
            company_id=approval_request.company_id,
            deal_reference=approval_request.deal_reference,
            step_number=step_number,
            approval_level=approval_level,
            action=action.value,
            actor_id=actor_id,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            context_metadata=metadata or {},
        )
        db.add(log)
        db.flush()
        return log

    @classmethod
    def get_audit_trail(
        cls,
        db: Session,
        company_id: uuid.UUID,
        approval_request_id: uuid.UUID,
    ) -> List[ApprovalAuditLog]:
        """Fetch chronological immutable audit logs for an approval request."""
        return list(
            db.execute(
                select(ApprovalAuditLog)
                .where(
                    ApprovalAuditLog.approval_request_id == approval_request_id,
                    ApprovalAuditLog.company_id == company_id,
                )
                .order_by(ApprovalAuditLog.created_at.asc())
            ).scalars().all()
        )


# ==============================================================================
# Phase 163: Approval Notifications Service
# ==============================================================================

class ApprovalNotificationService:
    """Service creating domain notification events with deduplication (Phase 163)."""

    @classmethod
    def notify(
        cls,
        db: Session,
        approval_request: ApprovalRequest,
        event_type: NotificationEventType,
        recipient_role: str,
        title: str,
        message: str,
        recipient_user_id: Optional[uuid.UUID] = None,
    ) -> Optional[ApprovalNotification]:
        """Create internal notification event record, preventing duplicate identical unread events."""
        # Deduplication check: check if an unread notification with identical event_type & request exists
        existing = db.execute(
            select(ApprovalNotification).where(
                ApprovalNotification.approval_request_id == approval_request.id,
                ApprovalNotification.event_type == event_type.value,
                ApprovalNotification.recipient_role == recipient_role,
                ApprovalNotification.is_read == False,
            )
        ).scalar_one_or_none()

        if existing:
            return existing

        notif = ApprovalNotification(
            approval_request_id=approval_request.id,
            company_id=approval_request.company_id,
            deal_reference=approval_request.deal_reference,
            event_type=event_type.value,
            recipient_role=recipient_role,
            recipient_user_id=recipient_user_id,
            title=title,
            message=message,
            is_read=False,
        )
        db.add(notif)
        db.flush()

        try:
            from app.services.event_bus import event_bus
            from app.schemas.realtime import EventEnvelope
            event_bus.publish_sync(
                EventEnvelope(
                    event_type=f"approval.{event_type.value.lower()}",
                    company_id=approval_request.company_id,
                    actor_id=recipient_user_id,
                    entity_type="approval_request",
                    entity_id=str(approval_request.id),
                    payload={
                        "deal_reference": approval_request.deal_reference,
                        "event_type": event_type.value,
                        "title": title,
                        "message": message,
                        "status": approval_request.status,
                    },
                )
            )
        except Exception:
            pass

        return notif

    @classmethod
    def list_notifications(
        cls,
        db: Session,
        company_id: uuid.UUID,
        user: Optional[User] = None,
        only_unread: bool = False,
    ) -> List[ApprovalNotification]:
        """List notifications relevant to the authenticated tenant and role."""
        query = select(ApprovalNotification).where(
            ApprovalNotification.company_id == company_id
        )
        if only_unread:
            query = query.where(ApprovalNotification.is_read == False)

        if user:
            user_roles = [r.name for r in user.roles if r.is_active]
            query = query.where(
                or_(
                    ApprovalNotification.recipient_user_id == user.id,
                    ApprovalNotification.recipient_role.in_(user_roles),
                )
            )

        return list(db.execute(query.order_by(ApprovalNotification.created_at.desc())).scalars().all())


# ==============================================================================
# Central Helper: Role Mapping from Level
# ==============================================================================

def role_for_approval_level(level: str) -> str:
    """Map an approval level to its authoritative RBAC role name."""
    if level == ApprovalLevel.SALES_MANAGER.value:
        return RBACRoleNames.SALES_MANAGER
    elif level == ApprovalLevel.FINANCE.value:
        return RBACRoleNames.FINANCE
    elif level == ApprovalLevel.VP_SALES.value:
        return "VP Sales"
    elif level == ApprovalLevel.EXECUTIVE.value:
        return "Executive"
    return RBACRoleNames.ADMIN


# ==============================================================================
# Phase 165: Central Approval Decision Engine
# (Also coordinates Phases 156-161, 162, 163)
# ==============================================================================

class ApprovalDecisionEngine:
    """Central authoritative orchestration layer for the approval lifecycle (Phase 165)."""

    @classmethod
    def submit_for_approval(
        cls,
        db: Session,
        company_id: uuid.UUID,
        request_payload: ComprehensiveApprovalEvaluationRequest,
        actor: User,
        expiration_hours: int = 72,
    ) -> ApprovalRequest:
        """Submit a deal, execute B05 routing, initialize chain steps, and check auto-approval."""
        # 1. Run B05 Multi-dimensional Routing
        routing_res = BlendedRiskScoreService.evaluate_comprehensive(
            db=db,
            company_id=company_id,
            request=request_payload,
        )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=expiration_hours)

        req = ApprovalRequest(
            company_id=company_id,
            deal_reference=request_payload.deal_reference or f"DEAL-{uuid.uuid4().hex[:8].upper()}",
            deal_value=request_payload.deal_value,
            selling_price=request_payload.selling_price,
            unit_cost=request_payload.unit_cost,
            requested_discount_pct=request_payload.requested_discount_pct,
            customer_id=request_payload.customer_id,
            status=ApprovalRequestStatus.PENDING.value,
            required_level=routing_res.final_required_level.value,
            required_chain_type=routing_res.final_approval_chain.chain_type.value,
            current_step_number=1,
            total_steps=len(routing_res.final_approval_chain.steps),
            blended_risk_score=routing_res.blended_result.blended_risk_score,
            blended_risk_classification=routing_res.blended_result.blended_risk_classification,
            routing_metadata=routing_res.model_dump(mode="json"),
            submitted_by_id=actor.id,
            expires_at=expires_at,
        )
        db.add(req)
        db.flush()

        # Record CREATED audit log
        ApprovalAuditService.record(
            db=db,
            approval_request=req,
            action=ApprovalAction.CREATED,
            approval_level=req.required_level,
            previous_status="NONE",
            new_status=ApprovalRequestStatus.PENDING.value,
            actor_id=actor.id,
            reason="Submitted for approval evaluation",
        )

        # 2. Check Auto-Approval Condition (Phase 156)
        if routing_res.final_required_level == ApprovalLevel.NO_APPROVAL_REQUIRED:
            req.status = ApprovalRequestStatus.APPROVED.value
            req.decision_reason = "Automated approval granted: All risk, discount, and margin metrics are within pre-approved thresholds."
            req.final_actioned_at = now

            ApprovalAuditService.record(
                db=db,
                approval_request=req,
                action=ApprovalAction.AUTO_APPROVED,
                approval_level=ApprovalLevel.NO_APPROVAL_REQUIRED.value,
                previous_status=ApprovalRequestStatus.PENDING.value,
                new_status=ApprovalRequestStatus.APPROVED.value,
                reason=req.decision_reason,
            )

            ApprovalNotificationService.notify(
                db=db,
                approval_request=req,
                event_type=NotificationEventType.APPROVAL_COMPLETED,
                recipient_role=RBACRoleNames.SALES_REPRESENTATIVE,
                title="Deal Auto-Approved",
                message=f"Deal {req.deal_reference} has been automatically approved.",
                recipient_user_id=actor.id,
            )

            db.commit()
            db.refresh(req)
            return req

        # 3. Build Sequential Chain Steps (Phase 159)
        chain_def = routing_res.final_approval_chain
        for idx, step_def in enumerate(chain_def.steps, start=1):
            is_first = (idx == 1)
            due_at = now + timedelta(hours=step_def.sla_hours) if is_first else None

            step = ApprovalStep(
                approval_request_id=req.id,
                company_id=company_id,
                step_number=step_def.step_number,
                step_name=step_def.step_name,
                required_level=step_def.level.value,
                assigned_role=role_for_approval_level(step_def.level.value),
                status=StepStatus.ACTIVE.value if is_first else StepStatus.PENDING.value,
                is_required=step_def.required,
                sla_hours=step_def.sla_hours,
                due_at=due_at,
            )
            db.add(step)

        req.status = ApprovalRequestStatus.IN_PROGRESS.value
        db.flush()

        # Emit notification for the first active step
        first_step = chain_def.steps[0]
        assigned_role = role_for_approval_level(first_step.level.value)
        event_type = (
            NotificationEventType.MANAGER_APPROVAL_REQUIRED
            if first_step.level == ApprovalLevel.SALES_MANAGER
            else NotificationEventType.FINANCE_APPROVAL_REQUIRED
            if first_step.level == ApprovalLevel.FINANCE
            else NotificationEventType.STEP_ACTIVATED
        )

        ApprovalNotificationService.notify(
            db=db,
            approval_request=req,
            event_type=event_type,
            recipient_role=assigned_role,
            title=f"{first_step.step_name} Required",
            message=f"Deal {req.deal_reference} requires your review and approval.",
        )

        db.commit()
        db.refresh(req)
        return req

    @classmethod
    def execute_auto_approval(
        cls,
        db: Session,
        company_id: uuid.UUID,
        approval_request_id: uuid.UUID,
        actor: User,
    ) -> DecisionResult:
        """Execute explicit auto-approval verification (Phase 156).
        Must REJECT if any level other than NO_APPROVAL_REQUIRED is required.
        """
        req = cls._get_request_for_tenant(db, company_id, approval_request_id)

        # Disallow auto-approval if higher authority is required
        if req.required_level != ApprovalLevel.NO_APPROVAL_REQUIRED.value:
            raise ApplicationError(
                message=f"Cannot auto-approve: deal requires '{req.required_level}' authority review.",
                code="AUTO_APPROVAL_DISALLOWED",
                status_code=400,
            )

        if req.status == ApprovalRequestStatus.APPROVED.value:
            # Idempotent response
            return DecisionResult(
                approval_request_id=req.id,
                status=req.status,
                decision="APPROVED",
                current_level=req.required_level,
                required_chain=req.required_chain_type,
                risk_score=float(req.blended_risk_score),
                blended_risk_score=float(req.blended_risk_score),
                message="Deal was already auto-approved.",
            )

        prev = req.status
        now = datetime.now(timezone.utc)
        req.status = ApprovalRequestStatus.APPROVED.value
        req.final_actioned_at = now
        req.final_actioned_by_id = actor.id
        req.decision_reason = "Verified automated approval executed."

        audit = ApprovalAuditService.record(
            db=db,
            approval_request=req,
            action=ApprovalAction.AUTO_APPROVED,
            approval_level=req.required_level,
            previous_status=prev,
            new_status=req.status,
            actor_id=actor.id,
            reason=req.decision_reason,
        )

        notif = ApprovalNotificationService.notify(
            db=db,
            approval_request=req,
            event_type=NotificationEventType.APPROVAL_COMPLETED,
            recipient_role=RBACRoleNames.SALES_REPRESENTATIVE,
            title="Auto-Approval Completed",
            message=f"Deal {req.deal_reference} has been auto-approved.",
        )

        db.commit()
        db.refresh(req)

        return DecisionResult(
            approval_request_id=req.id,
            status=req.status,
            decision="APPROVED",
            current_level=req.required_level,
            required_chain=req.required_chain_type,
            risk_score=float(req.blended_risk_score),
            blended_risk_score=float(req.blended_risk_score),
            audit_event_id=audit.id,
            notification_event_id=notif.id if notif else None,
            message="Auto-approval executed successfully.",
        )

    @classmethod
    def execute_approval_decision(
        cls,
        db: Session,
        company_id: uuid.UUID,
        approval_request_id: uuid.UUID,
        actor: User,
        decision: str,  # "APPROVED", "REJECTED", "RETURNED_FOR_REVISION"
        reason: Optional[str] = None,
        target_step_number: Optional[int] = None,
    ) -> DecisionResult:
        """Authoritative execution of step decision (Phases 157, 158, 159, 165)."""
        req = cls._get_request_for_tenant(db, company_id, approval_request_id)

        # 1. Terminal state check
        if req.status in (
            ApprovalRequestStatus.APPROVED.value,
            ApprovalRequestStatus.REJECTED.value,
            ApprovalRequestStatus.TIMED_OUT.value,
        ):
            # Idempotency check: if repeating same terminal action, return clean result
            if req.status == decision:
                return DecisionResult(
                    approval_request_id=req.id,
                    status=req.status,
                    decision=decision,
                    current_level=req.required_level,
                    required_chain=req.required_chain_type,
                    risk_score=float(req.blended_risk_score),
                    blended_risk_score=float(req.blended_risk_score),
                    message=f"Request is already in terminal state '{req.status}'.",
                )
            raise ApplicationError(
                message=f"Cannot act on request in terminal status '{req.status}'.",
                code="APPROVAL_TERMINAL_STATE",
                status_code=400,
            )

        # 2. Find currently active step
        active_step = db.execute(
            select(ApprovalStep).where(
                ApprovalStep.approval_request_id == req.id,
                ApprovalStep.status == StepStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()

        if not active_step:
            raise ApplicationError(
                message="No active approval step found for this request.",
                code="NO_ACTIVE_STEP",
                status_code=400,
            )

        # Enforce step sequence: cannot approve future or wrong step
        if target_step_number is not None and target_step_number != active_step.step_number:
            raise ApplicationError(
                message=f"Cannot act on step {target_step_number}; active step is {active_step.step_number}.",
                code="INVALID_STEP_SEQUENCE",
                status_code=400,
            )

        # 3. RBAC & Authority Level Enforcement (Phases 157 & 158)
        cls._validate_actor_authority(actor, active_step.required_level)

        now = datetime.now(timezone.utc)
        prev_req_status = req.status
        action_enum = (
            ApprovalAction.APPROVED if decision == "APPROVED"
            else ApprovalAction.REJECTED if decision == "REJECTED"
            else ApprovalAction.RETURNED_FOR_REVISION
        )

        # 4. Handle REJECTION
        if decision == "REJECTED":
            active_step.status = StepStatus.REJECTED.value
            active_step.decision = "REJECTED"
            active_step.decision_reason = reason or "Deal proposal rejected."
            active_step.actioned_by_id = actor.id
            active_step.actioned_at = now

            req.status = ApprovalRequestStatus.REJECTED.value
            req.decision_reason = active_step.decision_reason
            req.final_actioned_by_id = actor.id
            req.final_actioned_at = now

            audit = ApprovalAuditService.record(
                db=db,
                approval_request=req,
                action=ApprovalAction.REJECTED,
                approval_level=active_step.required_level,
                previous_status=prev_req_status,
                new_status=req.status,
                actor_id=actor.id,
                step_number=active_step.step_number,
                reason=active_step.decision_reason,
            )

            notif = ApprovalNotificationService.notify(
                db=db,
                approval_request=req,
                event_type=NotificationEventType.APPROVAL_REJECTED,
                recipient_role=RBACRoleNames.SALES_REPRESENTATIVE,
                title="Deal Proposal Rejected",
                message=f"Deal {req.deal_reference} was rejected at step {active_step.step_number} ({active_step.step_name}).",
                recipient_user_id=req.submitted_by_id,
            )

            db.commit()
            db.refresh(req)

            return DecisionResult(
                approval_request_id=req.id,
                status=req.status,
                decision="REJECTED",
                current_level=active_step.required_level,
                required_chain=req.required_chain_type,
                risk_score=float(req.blended_risk_score),
                blended_risk_score=float(req.blended_risk_score),
                audit_event_id=audit.id,
                notification_event_id=notif.id if notif else None,
                message="Deal proposal has been rejected.",
            )

        # 5. Handle RETURN FOR REVISION
        if decision == "RETURNED_FOR_REVISION":
            active_step.status = StepStatus.RETURNED_FOR_REVISION.value
            active_step.decision = "RETURNED_FOR_REVISION"
            active_step.decision_reason = reason or "Proposal returned for terms revision."
            active_step.actioned_by_id = actor.id
            active_step.actioned_at = now

            req.status = ApprovalRequestStatus.RETURNED_FOR_REVISION.value
            req.decision_reason = active_step.decision_reason
            req.final_actioned_by_id = actor.id
            req.final_actioned_at = now

            audit = ApprovalAuditService.record(
                db=db,
                approval_request=req,
                action=ApprovalAction.RETURNED_FOR_REVISION,
                approval_level=active_step.required_level,
                previous_status=prev_req_status,
                new_status=req.status,
                actor_id=actor.id,
                step_number=active_step.step_number,
                reason=active_step.decision_reason,
            )

            notif = ApprovalNotificationService.notify(
                db=db,
                approval_request=req,
                event_type=NotificationEventType.RETURNED_FOR_REVISION,
                recipient_role=RBACRoleNames.SALES_REPRESENTATIVE,
                title="Proposal Returned for Revision",
                message=f"Deal {req.deal_reference} requires revision: {active_step.decision_reason}",
                recipient_user_id=req.submitted_by_id,
            )

            db.commit()
            db.refresh(req)

            return DecisionResult(
                approval_request_id=req.id,
                status=req.status,
                decision="RETURNED_FOR_REVISION",
                current_level=active_step.required_level,
                required_chain=req.required_chain_type,
                risk_score=float(req.blended_risk_score),
                blended_risk_score=float(req.blended_risk_score),
                audit_event_id=audit.id,
                notification_event_id=notif.id if notif else None,
                message="Deal proposal returned for revision.",
            )

        # 6. Handle APPROVAL (Advance Chain - Phase 159)
        active_step.status = StepStatus.APPROVED.value
        active_step.decision = "APPROVED"
        active_step.decision_reason = reason or "Step approved."
        active_step.actioned_by_id = actor.id
        active_step.actioned_at = now

        # Find next sequential step
        next_step = db.execute(
            select(ApprovalStep).where(
                ApprovalStep.approval_request_id == req.id,
                ApprovalStep.step_number == active_step.step_number + 1,
            )
        ).scalar_one_or_none()

        audit = ApprovalAuditService.record(
            db=db,
            approval_request=req,
            action=ApprovalAction.APPROVED,
            approval_level=active_step.required_level,
            previous_status=prev_req_status,
            new_status=ApprovalRequestStatus.IN_PROGRESS.value if next_step else ApprovalRequestStatus.APPROVED.value,
            actor_id=actor.id,
            step_number=active_step.step_number,
            reason=active_step.decision_reason,
        )

        if next_step:
            # Activate next step
            next_step.status = StepStatus.ACTIVE.value
            next_step.due_at = now + timedelta(hours=next_step.sla_hours)
            req.current_step_number = next_step.step_number
            req.status = ApprovalRequestStatus.IN_PROGRESS.value

            notif = ApprovalNotificationService.notify(
                db=db,
                approval_request=req,
                event_type=NotificationEventType.STEP_ACTIVATED,
                recipient_role=next_step.assigned_role,
                title=f"{next_step.step_name} Required",
                message=f"Deal {req.deal_reference} advanced to step {next_step.step_number} ({next_step.step_name}).",
            )

            msg = f"Step {active_step.step_number} approved. Step {next_step.step_number} ({next_step.step_name}) is now active."
            next_level_val = next_step.required_level
        else:
            # All steps completed! Full chain approved!
            req.status = ApprovalRequestStatus.APPROVED.value
            req.final_actioned_at = now
            req.final_actioned_by_id = actor.id
            req.decision_reason = "All approval chain steps successfully completed."

            notif = ApprovalNotificationService.notify(
                db=db,
                approval_request=req,
                event_type=NotificationEventType.APPROVAL_COMPLETED,
                recipient_role=RBACRoleNames.SALES_REPRESENTATIVE,
                title="Deal Fully Approved",
                message=f"Deal {req.deal_reference} has completed all approval steps successfully.",
                recipient_user_id=req.submitted_by_id,
            )

            msg = "All approval chain steps successfully completed. Deal is fully APPROVED."
            next_level_val = None

        db.commit()
        db.refresh(req)

        return DecisionResult(
            approval_request_id=req.id,
            status=req.status,
            decision="APPROVED",
            current_level=active_step.required_level,
            next_level=next_level_val,
            required_chain=req.required_chain_type,
            risk_score=float(req.blended_risk_score),
            blended_risk_score=float(req.blended_risk_score),
            audit_event_id=audit.id,
            notification_event_id=notif.id if notif else None,
            message=msg,
        )

    @classmethod
    def escalate_request(
        cls,
        db: Session,
        company_id: uuid.UUID,
        approval_request_id: uuid.UUID,
        actor: Optional[User] = None,
        reason: Optional[str] = None,
    ) -> DecisionResult:
        """Escalate an overdue or stalled approval step to the next authority level (Phase 160)."""
        req = cls._get_request_for_tenant(db, company_id, approval_request_id)

        if req.status not in (
            ApprovalRequestStatus.IN_PROGRESS.value,
            ApprovalRequestStatus.PENDING.value,
            ApprovalRequestStatus.ESCALATED.value,
        ):
            raise ApplicationError(
                message=f"Cannot escalate request in status '{req.status}'.",
                code="CANNOT_ESCALATE_STATUS",
                status_code=400,
            )

        active_step = db.execute(
            select(ApprovalStep).where(
                ApprovalStep.approval_request_id == req.id,
                ApprovalStep.status == StepStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()

        if not active_step:
            raise ApplicationError(
                message="No active step available for escalation.",
                code="NO_ACTIVE_STEP",
                status_code=400,
            )

        curr_level = ApprovalLevel(active_step.required_level)
        curr_rank = ApprovalLevelHierarchyService.get_rank(curr_level)

        # Check for terminal executive level
        if curr_level == ApprovalLevel.EXECUTIVE:
            raise ApplicationError(
                message="Cannot escalate beyond EXECUTIVE level; highest governance tier already active.",
                code="MAXIMUM_ESCALATION_REACHED",
                status_code=400,
            )

        # Escalate to next level in hierarchy
        next_level = (
            ApprovalLevel.FINANCE if curr_level == ApprovalLevel.SALES_MANAGER
            else ApprovalLevel.VP_SALES if curr_level == ApprovalLevel.FINANCE
            else ApprovalLevel.EXECUTIVE
        )

        now = datetime.now(timezone.utc)
        prev_level_str = active_step.required_level
        active_step.escalated_to_level = next_level.value
        active_step.required_level = next_level.value
        active_step.assigned_role = role_for_approval_level(next_level.value)
        # Base step name without prior escalation suffixes
        base_name = active_step.step_name.split(" (Escalated")[0]
        active_step.step_name = f"{base_name[:60]} (Escalated: {next_level.value})"
        active_step.status = StepStatus.ACTIVE.value
        active_step.due_at = now + timedelta(hours=active_step.sla_hours)

        req.status = ApprovalRequestStatus.ESCALATED.value
        req.required_level = next_level.value

        audit = ApprovalAuditService.record(
            db=db,
            approval_request=req,
            action=ApprovalAction.ESCALATED,
            approval_level=next_level.value,
            previous_status=prev_level_str,
            new_status=req.status,
            actor_id=actor.id if actor else None,
            step_number=active_step.step_number,
            reason=reason or f"SLA escalation from {curr_level.value} to {next_level.value}.",
        )

        notif = ApprovalNotificationService.notify(
            db=db,
            approval_request=req,
            event_type=NotificationEventType.APPROVAL_ESCALATED,
            recipient_role=active_step.assigned_role,
            title="Approval Request Escalated",
            message=f"Deal {req.deal_reference} has been escalated to {next_level.value}.",
        )

        db.commit()
        db.refresh(req)

        return DecisionResult(
            approval_request_id=req.id,
            status=req.status,
            decision="ESCALATED",
            current_level=next_level.value,
            required_chain=req.required_chain_type,
            risk_score=float(req.blended_risk_score),
            blended_risk_score=float(req.blended_risk_score),
            audit_event_id=audit.id,
            notification_event_id=notif.id if notif else None,
            message=f"Approval request successfully escalated to {next_level.value}.",
        )

    @classmethod
    def check_and_apply_timeouts(
        cls,
        db: Session,
        company_id: uuid.UUID,
    ) -> List[uuid.UUID]:
        """Scan active approval requests and steps for expired deadlines, marking as TIMED_OUT (Phase 161)."""
        now = datetime.now(timezone.utc)
        timed_out_ids: List[uuid.UUID] = []

        # 1. Requests exceeding overall expires_at
        expired_reqs = db.execute(
            select(ApprovalRequest).where(
                ApprovalRequest.company_id == company_id,
                ApprovalRequest.status.in_([
                    ApprovalRequestStatus.PENDING.value,
                    ApprovalRequestStatus.IN_PROGRESS.value,
                    ApprovalRequestStatus.ESCALATED.value,
                ]),
                ApprovalRequest.expires_at <= now,
            )
        ).scalars().all()

        for req in expired_reqs:
            prev = req.status
            req.status = ApprovalRequestStatus.TIMED_OUT.value
            req.decision_reason = "Approval window expired past maximum allowed expiration horizon."

            # Mark any active step as skipped/timed out
            for step in req.steps:
                if step.status == StepStatus.ACTIVE.value:
                    step.status = StepStatus.SKIPPED.value

            ApprovalAuditService.record(
                db=db,
                approval_request=req,
                action=ApprovalAction.TIMED_OUT,
                approval_level=req.required_level,
                previous_status=prev,
                new_status=req.status,
                reason=req.decision_reason,
            )

            ApprovalNotificationService.notify(
                db=db,
                approval_request=req,
                event_type=NotificationEventType.APPROVAL_TIMED_OUT,
                recipient_role=RBACRoleNames.SALES_REPRESENTATIVE,
                title="Approval Request Timed Out",
                message=f"Deal {req.deal_reference} has expired and marked TIMED_OUT.",
                recipient_user_id=req.submitted_by_id,
            )
            timed_out_ids.append(req.id)

        db.commit()
        return timed_out_ids

    # --------------------------------------------------------------------------
    # Private Helpers & RBAC Verification
    # --------------------------------------------------------------------------

    @classmethod
    def _get_request_for_tenant(
        cls,
        db: Session,
        company_id: uuid.UUID,
        approval_request_id: uuid.UUID,
    ) -> ApprovalRequest:
        """Fetch request ensuring strict company_id isolation."""
        req = db.execute(
            select(ApprovalRequest)
            .options(joinedload(ApprovalRequest.steps))
            .where(
                ApprovalRequest.id == approval_request_id,
                ApprovalRequest.company_id == company_id,
            )
        ).unique().scalar_one_or_none()

        if not req:
            raise ApplicationError(
                message=f"Approval request '{approval_request_id}' not found.",
                code="APPROVAL_REQUEST_NOT_FOUND",
                status_code=404,
            )
        return req

    @classmethod
    def _validate_actor_authority(cls, actor: User, required_level_str: str) -> None:
        """Enforce that the acting user holds sufficient RBAC permissions/roles for the level."""
        req_level = ApprovalLevel(required_level_str)
        user_role_names = [r.name for r in actor.roles if r.is_active]

        def has_role_pattern(pattern: str) -> bool:
            return any(pattern.lower() in r.lower() for r in user_role_names)

        # Admin can approve anything
        if has_role_pattern("admin"):
            return

        if req_level == ApprovalLevel.SALES_MANAGER:
            if not has_role_pattern("manager") and not has_role_pattern("sales manager"):
                raise ApplicationError(
                    message="Access denied: Sales Manager role required.",
                    code="UNAUTHORIZED_MANAGER_APPROVAL",
                    status_code=403,
                )

        elif req_level == ApprovalLevel.FINANCE:
            if not has_role_pattern("finance"):
                raise ApplicationError(
                    message="Access denied: Finance role required for fiscal approval.",
                    code="UNAUTHORIZED_FINANCE_APPROVAL",
                    status_code=403,
                )

        elif req_level in (ApprovalLevel.VP_SALES, ApprovalLevel.EXECUTIVE):
            if not has_role_pattern("vp") and not has_role_pattern("executive") and not has_role_pattern("admin"):
                raise ApplicationError(
                    message=f"Access denied: Senior leadership role required for {req_level.value} sign-off.",
                    code="UNAUTHORIZED_EXECUTIVE_APPROVAL",
                    status_code=403,
                )


# ==============================================================================
# Phase 164: Approval Dashboard Service
# ==============================================================================

class ApprovalDashboardService:
    """Service providing aggregated KPIs, counts, and active queues (Phase 164)."""

    @classmethod
    def get_dashboard_metrics(cls, db: Session, company_id: uuid.UUID) -> ApprovalDashboardMetrics:
        """Produce real-time multi-tenant dashboard aggregations."""
        reqs = list(
            db.execute(
                select(ApprovalRequest)
                .options(joinedload(ApprovalRequest.steps))
                .where(ApprovalRequest.company_id == company_id)
                .order_by(ApprovalRequest.created_at.desc())
            ).unique().scalars().all()
        )

        total = len(reqs)
        pending = sum(1 for r in reqs if r.status == ApprovalRequestStatus.PENDING.value)
        in_prog = sum(1 for r in reqs if r.status == ApprovalRequestStatus.IN_PROGRESS.value)
        approved = sum(1 for r in reqs if r.status == ApprovalRequestStatus.APPROVED.value)
        rejected = sum(1 for r in reqs if r.status == ApprovalRequestStatus.REJECTED.value)
        returned = sum(1 for r in reqs if r.status == ApprovalRequestStatus.RETURNED_FOR_REVISION.value)
        escalated = sum(1 for r in reqs if r.status == ApprovalRequestStatus.ESCALATED.value)
        timed_out = sum(1 for r in reqs if r.status == ApprovalRequestStatus.TIMED_OUT.value)

        # Average approval time (in hours) for approved requests
        durations: List[float] = []
        for r in reqs:
            if r.status == ApprovalRequestStatus.APPROVED.value and r.final_actioned_at and r.created_at:
                dur = (r.final_actioned_at - r.created_at).total_seconds() / 3600.0
                durations.append(dur)
        avg_time = round(sum(durations) / len(durations), 2) if durations else 0.0

        # Group by status
        status_map: Dict[str, int] = {}
        for r in reqs:
            status_map[r.status] = status_map.get(r.status, 0) + 1
        counts_by_status = [ApprovalStatusCount(status=k, count=v) for k, v in status_map.items()]

        # Group by level
        level_map: Dict[str, int] = {}
        for r in reqs:
            level_map[r.required_level] = level_map.get(r.required_level, 0) + 1
        counts_by_level = [ApprovalLevelCount(level=k, count=v) for k, v in level_map.items()]

        recent = [ApprovalRequestResponse.model_validate(r) for r in reqs[:10]]

        return ApprovalDashboardMetrics(
            company_id=company_id,
            total_requests=total,
            pending_count=pending,
            in_progress_count=in_prog,
            approved_count=approved,
            rejected_count=rejected,
            returned_count=returned,
            escalated_count=escalated,
            timed_out_count=timed_out,
            avg_approval_time_hours=avg_time,
            counts_by_status=counts_by_status,
            counts_by_level=counts_by_level,
            recent_requests=recent,
            generated_at=datetime.now(timezone.utc),
        )
