import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.reporting import ScheduledReport, ReportExecution, ExecutionStatus
from app.reporting.schemas import ScheduledReportCreate, ScheduledReportResponse, ReportExecutionResponse
from app.reporting.services import ReportingService
from app.reporting.schemas import ReportFilterParams


class SchedulingService:
    """
    Scheduled Report Management & Triggering Engine (Phase 369).
    Persists recurring report automation parameters and records historical runs per tenant.
    """

    @staticmethod
    def create_schedule(
        db: Session,
        company_id: uuid.UUID,
        created_by_id: uuid.UUID,
        data: ScheduledReportCreate,
    ) -> ScheduledReport:
        schedule = ScheduledReport(
            company_id=company_id,
            name=data.name,
            report_type=data.report_type.lower(),
            filters=data.filters,
            frequency=data.frequency.upper(),
            format=data.format.upper(),
            recipients=data.recipients,
            is_active=data.is_active,
            created_by_id=created_by_id,
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def list_schedules(
        db: Session,
        company_id: uuid.UUID,
    ) -> List[ScheduledReport]:
        return list(
            db.scalars(
                select(ScheduledReport)
                .where(ScheduledReport.company_id == company_id)
                .order_by(ScheduledReport.created_at.desc())
            )
        )

    @staticmethod
    def trigger_execution(
        db: Session,
        company_id: uuid.UUID,
        schedule_id: uuid.UUID,
    ) -> ReportExecution:
        schedule = db.get(ScheduledReport, schedule_id)
        if not schedule or schedule.company_id != company_id:
            raise ValueError("Scheduled report not found or access denied")

        # Run report generation logic
        filter_dict = schedule.filters or {}
        filters = ReportFilterParams(**filter_dict)

        row_count = 0
        rep_type = schedule.report_type.lower()
        if rep_type == "sales":
            rep = ReportingService.get_sales_report(db, company_id, filters)
            row_count = len(rep.items)
        elif rep_type == "customers":
            rep = ReportingService.get_customer_report(db, company_id, filters)
            row_count = len(rep.items)
        elif rep_type == "products":
            rep = ReportingService.get_product_report(db, company_id, filters)
            row_count = len(rep.items)
        elif rep_type == "inventory":
            rep = ReportingService.get_inventory_report(db, company_id, filters)
            row_count = len(rep.items)
        elif rep_type == "discounts":
            rep = ReportingService.get_discount_report(db, company_id, filters)
            row_count = len(rep.items)
        elif rep_type == "approvals":
            rep = ReportingService.get_approval_report(db, company_id, filters)
            row_count = len(rep.items)
        elif rep_type == "deal_health":
            rep = ReportingService.get_deal_health_report(db, company_id, filters)
            row_count = len(rep.items)
        else:
            row_count = 1

        now = datetime.now(timezone.utc)
        schedule.last_run_at = now

        execution = ReportExecution(
            company_id=company_id,
            scheduled_report_id=schedule.id,
            report_type=schedule.report_type,
            status=ExecutionStatus.COMPLETED.value,
            row_count=row_count,
            executed_at=now,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def list_executions(
        db: Session,
        company_id: uuid.UUID,
        schedule_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> List[ReportExecution]:
        stmt = select(ReportExecution).where(ReportExecution.company_id == company_id)
        if schedule_id:
            stmt = stmt.where(ReportExecution.scheduled_report_id == schedule_id)
        stmt = stmt.order_by(desc(ReportExecution.executed_at)).limit(limit)
        return list(db.scalars(stmt))
