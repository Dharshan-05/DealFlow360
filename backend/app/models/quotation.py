"""Quotation Models (DealFlow360 B09 & B10: Phases 186–205).

Represents a governed commercial quotation scoped to a tenant company, customer,
and authoring user, tracking line items, multi-tier discounts, taxes, real-time margins,
status lifecycle, versioning revisions, approval integration, dispatch logs, and deal conversion.
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.approval_execution import ApprovalRequest
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.customer_deal_history import CustomerDealHistory
    from app.models.quotation_line_item import QuotationLineItem
    from app.models.user import User


class QuotationStatus(str, enum.Enum):
    """Lifecycle statuses for quotations (Phases 186 & 196)."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SENT = "SENT"
    VIEWED = "VIEWED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"
    CANCELLED = "CANCELLED"


class Quotation(Base):
    """Quotation Header Entity (Phase 186–195).

    Tracks customer association, unique quote numbering, discounts, taxes,
    and financial margins with strict Decimal numeric precision.
    """

    __tablename__ = "quotations"

    __table_args__ = (
        UniqueConstraint("company_id", "quotation_number", name="uq_quotations_company_quotation_number"),
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
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        comment="Author/Sales representative who created the quotation",
    )
    quotation_number: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
        default=QuotationStatus.DRAFT.value,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Active version number of the quotation (Phase 197)",
    )

    # Financial totals (Strict Decimal / Numeric precision)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Sum of gross line subtotals before discounts",
    )
    line_discount_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Aggregated sum of all line item discounts",
    )
    overall_discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Quotation-level overall discount percentage (Phase 194)",
    )
    overall_discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Quotation-level overall discount monetary amount (Phase 194)",
    )
    total_discount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Combined total discounts (line discounts + overall discount)",
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Net taxable base after all discounts applied (Phase 192)",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Aggregated tax amount (Phase 192)",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Final grand total amount payable (taxable + tax)",
    )

    # Margin metrics (Phase 195)
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Aggregated product cost across all line items",
    )
    gross_profit: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Total net revenue excluding tax minus total cost",
    )
    margin_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Gross profit margin percentage",
    )
    is_negative_margin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Flag indicating quotation has negative gross profit",
    )

    # Lifecycle & Extension fields (Phases 198–205)
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiration timestamp (Phase 198)",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    terms_conditions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Approval Engine Linkage (Phase 199)
    approval_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Acceptance / Rejection Metadata (Phases 203 & 204)
    accepted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    acceptance_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    rejected_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Conversion to Deal (Phase 205)
    converted_deal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_deal_history.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    converted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Send Tracking (Phase 202)
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    viewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
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
    company: Mapped["Company"] = relationship(
        "Company",
        lazy="selectin",
    )
    customer: Mapped["Customer"] = relationship(
        "Customer",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    accepted_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[accepted_by_id],
        lazy="selectin",
    )
    rejected_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[rejected_by_id],
        lazy="selectin",
    )
    approval_request: Mapped[Optional["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        foreign_keys=[approval_request_id],
        lazy="selectin",
    )
    converted_deal: Mapped[Optional["CustomerDealHistory"]] = relationship(
        "CustomerDealHistory",
        foreign_keys=[converted_deal_id],
        lazy="selectin",
    )
    line_items: Mapped[List["QuotationLineItem"]] = relationship(
        "QuotationLineItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="QuotationLineItem.line_number",
    )
    versions: Mapped[List["QuotationVersion"]] = relationship(
        "QuotationVersion",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="QuotationVersion.version_number.desc()",
    )
    send_logs: Mapped[List["QuotationSendLog"]] = relationship(
        "QuotationSendLog",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="QuotationSendLog.sent_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Quotation {self.quotation_number} (v{self.version_number}) status={self.status} total={self.total_amount}>"


class QuotationVersion(Base):
    """Historical immutable revision of a commercial quotation (Phase 197).

    Snapshots the entire state of line items, totals, discounts, and margins
    with Decimal string values to prevent floating-point drifts.
    """

    __tablename__ = "quotation_versions"

    __table_args__ = (
        UniqueConstraint("quotation_id", "version_number", name="uq_quotation_versions_quote_ver"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    change_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    snapshot_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship(
        "Quotation",
        back_populates="versions",
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<QuotationVersion {self.quotation_id} v{self.version_number}>"


class QuotationSendLog(Base):
    """Quotation send and view lifecycle tracking log (Phases 201 & 202).

    Records every email dispatch attempt, tracking token, recipient,
    delivery state, and client view/open timestamps.
    """

    __tablename__ = "quotation_send_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    recipient_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    delivery_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SENT",
    )
    email_subject: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    tracking_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    viewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    quotation: Mapped["Quotation"] = relationship(
        "Quotation",
        back_populates="send_logs",
    )
    sender: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<QuotationSendLog {self.quotation_id} to={self.recipient_email} status={self.delivery_status}>"
