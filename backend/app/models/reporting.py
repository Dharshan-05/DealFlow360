import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReportFrequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"


class ExportFormat(str, Enum):
    CSV = "CSV"
    JSON = "JSON"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScheduledReport(Base):
    """
    Scheduled Report Model (Phase 369).
    Persists recurring automated report execution rules per tenant.
    """
    __tablename__ = "scheduled_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    frequency: Mapped[str] = mapped_column(String(50), default=ReportFrequency.WEEKLY.value, nullable=False)
    format: Mapped[str] = mapped_column(String(20), default=ExportFormat.CSV.value, nullable=False)
    recipients: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company: Mapped["Company"] = relationship("Company")
    created_by: Mapped[Optional["User"]] = relationship("User")
    executions: Mapped[List["ReportExecution"]] = relationship(
        "ReportExecution", back_populates="scheduled_report", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ScheduledReport {self.id} [{self.report_type}] {self.name}>"


class ReportExecution(Base):
    """
    Report Execution Log (Phase 369).
    Records historical report generations, row counts, and status per tenant.
    """
    __tablename__ = "report_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    scheduled_report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheduled_reports.id", ondelete="CASCADE"), index=True, nullable=True
    )
    report_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ExecutionStatus.COMPLETED.value, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    company: Mapped["Company"] = relationship("Company")
    scheduled_report: Mapped[Optional["ScheduledReport"]] = relationship("ScheduledReport", back_populates="executions")

    def __repr__(self) -> str:
        return f"<ReportExecution {self.id} [{self.report_type}] status={self.status}>"
