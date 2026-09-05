"""Approval Execution Engine Models (DealFlow360 B06: Phases 156–165).

Defines persistent entities for:
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

Strictly isolated by company_id.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.user import User


class ApprovalRequest(Base):
    """Core approval request entity orchestrating approval lifecycle (Phases 156–165)."""

    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    deal_reference: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    deal_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    requested_discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        index=True,
        nullable=False,
    )
    required_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    required_chain_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    current_step_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    total_steps: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    blended_risk_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    blended_risk_classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    routing_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    submitted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    final_actioned_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    final_actioned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    customer: Mapped[Optional["Customer"]] = relationship("Customer")
    submitted_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[submitted_by_id])
    final_actioned_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[final_actioned_by_id])
    steps: Mapped[List["ApprovalStep"]] = relationship(
        "ApprovalStep",
        back_populates="approval_request",
        cascade="all, delete-orphan",
        order_by="ApprovalStep.step_number",
    )
    audit_logs: Mapped[List["ApprovalAuditLog"]] = relationship(
        "ApprovalAuditLog",
        back_populates="approval_request",
        cascade="all, delete-orphan",
        order_by="ApprovalAuditLog.created_at",
    )

    __table_args__ = (
        Index("ix_approval_requests_company_status", "company_id", "status"),
        Index("ix_approval_requests_company_deal", "company_id", "deal_reference"),
    )


class ApprovalStep(Base):
    """Sequential step within an approval chain (Phase 159)."""

    __tablename__ = "approval_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    approval_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    step_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    required_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    assigned_role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    sla_hours: Mapped[int] = mapped_column(
        Integer,
        default=24,
        nullable=False,
    )
    due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    actioned_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actioned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    escalated_to_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    approval_request: Mapped["ApprovalRequest"] = relationship("ApprovalRequest", back_populates="steps")
    actioned_by: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_approval_steps_request_step", "approval_request_id", "step_number", unique=True),
        Index("ix_approval_steps_company_status", "company_id", "status"),
    )


class ApprovalAuditLog(Base):
    """Immutable audit trail for all approval actions (Phase 162)."""

    __tablename__ = "approval_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    approval_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    deal_reference: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    step_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    approval_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    new_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    context_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    approval_request: Mapped["ApprovalRequest"] = relationship("ApprovalRequest", back_populates="audit_logs")
    actor: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_approval_audit_logs_company_req", "company_id", "approval_request_id"),
        Index("ix_approval_audit_logs_deal", "company_id", "deal_reference"),
    )


class ApprovalNotification(Base):
    """Internal domain notification record for approval workflow events (Phase 163)."""

    __tablename__ = "approval_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    approval_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    deal_reference: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    recipient_role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    recipient_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    approval_request: Mapped["ApprovalRequest"] = relationship("ApprovalRequest")
    recipient_user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("ix_approval_notif_company_read", "company_id", "is_read"),
        Index("ix_approval_notif_company_role", "company_id", "recipient_role"),
    )
