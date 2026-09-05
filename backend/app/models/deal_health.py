import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer_deal_history import CustomerDealHistory
    from app.models.user import User


class DealHealthClassification(str, enum.Enum):
    """Canonical deal health classifications (Phase 223)."""
    HEALTHY = "HEALTHY"      # 80-100
    WATCH = "WATCH"          # 60-79
    AT_RISK = "AT_RISK"      # 40-59
    CRITICAL = "CRITICAL"    # 0-39


class DealHealthAlertType(str, enum.Enum):
    """Supported deal health alert triggers (Phase 226)."""
    CRITICAL_HEALTH = "CRITICAL_HEALTH"
    HIGH_STALL_RISK = "HIGH_STALL_RISK"
    HIGH_DELAY_RISK = "HIGH_DELAY_RISK"
    DISCOUNT_ANOMALY = "DISCOUNT_ANOMALY"
    APPROVAL_BOTTLENECK = "APPROVAL_BOTTLENECK"
    DELIVERY_SLIPPAGE = "DELIVERY_SLIPPAGE"
    SEVERE_INACTIVITY = "SEVERE_INACTIVITY"
    BEHAVIORAL_ANOMALY = "BEHAVIORAL_ANOMALY"


class DealHealthAlertSeverity(str, enum.Enum):
    """Alert severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DealHealthAlertStatus(str, enum.Enum):
    """Alert resolution status."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class DealHealthNudgeStatus(str, enum.Enum):
    """Nudge lifecycle states (Phase 228)."""
    PENDING = "PENDING"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DISMISSED = "DISMISSED"


class DealHealthEscalationStatus(str, enum.Enum):
    """Escalation status (Phase 229)."""
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    ESCALATED_HIGHER = "ESCALATED_HIGHER"


class DealHealthSnapshot(Base):
    """Persisted point-in-time deal health evaluation snapshot (Phases 211–224)."""

    __tablename__ = "deal_health_snapshots"

    __table_args__ = (
        Index("ix_deal_health_snapshots_company_deal", "company_id", "deal_id"),
        Index("ix_deal_health_snapshots_created_at", "created_at"),
        CheckConstraint("health_score >= 0 AND health_score <= 100", name="chk_deal_health_score_range"),
    )

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
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_deal_history.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    health_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    conversion_probability: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    stall_probability: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    delay_probability: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    anomaly_detected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    anomaly_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    primary_risk_factors: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    positive_factors: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    contributing_signals: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    feature_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    deal: Mapped["CustomerDealHistory"] = relationship("CustomerDealHistory")


class DealHealthAlert(Base):
    """Alert record generated for critical deal health conditions (Phase 226)."""

    __tablename__ = "deal_health_alerts"

    __table_args__ = (
        Index("ix_deal_health_alerts_company_status", "company_id", "status"),
        Index("ix_deal_health_alerts_deal_type_status", "deal_id", "alert_type", "status"),
        Index("ix_deal_health_alerts_created_at", "created_at"),
    )

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
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_deal_history.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        default="HIGH",
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    health_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    anomaly_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    recommended_action: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        nullable=False,
        index=True,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    deal: Mapped["CustomerDealHistory"] = relationship("CustomerDealHistory")
    actor: Mapped[Optional["User"]] = relationship("User", lazy="selectin")


class DealHealthRecommendation(Base):
    """Actionable recommendations derived from deal risk signals (Phase 227)."""

    __tablename__ = "deal_health_recommendations"

    __table_args__ = (
        Index("ix_deal_health_recs_company_deal", "company_id", "deal_id"),
        Index("ix_deal_health_recs_status", "status"),
    )

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
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_deal_history.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    recommendation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default="MEDIUM",
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    triggering_signal: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    suggested_action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    deal: Mapped["CustomerDealHistory"] = relationship("CustomerDealHistory")


class DealHealthNudge(Base):
    """Automated internal nudge event for deal attention (Phase 228)."""

    __tablename__ = "deal_health_nudges"

    __table_args__ = (
        Index("ix_deal_health_nudges_company_deal", "company_id", "deal_id"),
        Index("ix_deal_health_nudges_status", "status"),
    )

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
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_deal_history.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    nudge_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    deal: Mapped["CustomerDealHistory"] = relationship("CustomerDealHistory")
    recipient: Mapped[Optional["User"]] = relationship("User", foreign_keys=[recipient_id], lazy="selectin")
    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_id], lazy="selectin")


class DealHealthEscalation(Base):
    """Deal escalation event tied to existing approval authority hierarchy (Phase 229)."""

    __tablename__ = "deal_health_escalations"

    __table_args__ = (
        Index("ix_deal_health_escalations_company_deal", "company_id", "deal_id"),
        Index("ix_deal_health_escalations_status", "status"),
    )

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
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_deal_history.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    current_health: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    escalation_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_signal: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    previous_authority_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    next_authority_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
    )
    sla_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    deal: Mapped["CustomerDealHistory"] = relationship("CustomerDealHistory")
    previous_authority: Mapped[Optional["User"]] = relationship("User", foreign_keys=[previous_authority_id], lazy="selectin")
    next_authority: Mapped[Optional["User"]] = relationship("User", foreign_keys=[next_authority_id], lazy="selectin")


class DealHealthModelMetadata(Base):
    """Model versioning and feature metadata persistence (Phase 218)."""

    __tablename__ = "deal_health_model_metadata"

    __table_args__ = (
        Index("ix_deal_health_model_metadata_company_version", "company_id", "model_version"),
    )

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
    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    model_type: Mapped[str] = mapped_column(
        String(50),
        default="DEAL_HEALTH_ENSEMBLE",
        nullable=False,
    )
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    feature_names: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
    )
    metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
