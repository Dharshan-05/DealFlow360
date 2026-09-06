import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, get_db
from app.models.user import User
from app.reporting import (
    ReportFilterParams,
    ReportingService,
    ReportExporter,
    SchedulingService,
    SalesReportResponse,
    CustomerReportResponse,
    ProductReportResponse,
    InventoryReportResponse,
    DiscountReportResponse,
    ApprovalReportResponse,
    DealHealthReportResponse,
    RevenueAnalyticsResponse,
    ConversionAnalyticsResponse,
    CustomerAnalyticsReportResponse,
    ProductAnalyticsReportResponse,
    DiscountAnalyticsReportResponse,
    InventoryAnalyticsReportResponse,
    ApprovalAnalyticsReportResponse,
    DealHealthAnalyticsReportResponse,
    ExecutiveDashboardAnalyticsResponse,
)
from app.reporting.schemas import (
    ScheduledReportCreate,
    ScheduledReportResponse,
    ReportExecutionResponse,
)

router = APIRouter()


# ==============================================================================
# Domain Reports (Phases 353–359)
# ==============================================================================

@router.get("/sales", response_model=SalesReportResponse)
def get_sales_report(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_sales_report(db, current_user.company_id, filters)


@router.get("/sales/export")
def export_sales_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    rep = ReportingService.get_sales_report(db, current_user.company_id, filters)
    cols = ["deal_code", "deal_name", "customer_name", "stage", "deal_value", "gross_profit", "margin_percentage", "probability", "expected_revenue"]
    rows = [item.model_dump() for item in rep.items]
    if format == "json":
        return ReportExporter.export_to_json("sales_report", rep.model_dump())
    return ReportExporter.export_to_csv("sales_report", cols, rows)


@router.get("/customers", response_model=CustomerReportResponse)
def get_customer_report(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_customer_report(db, current_user.company_id, filters)


@router.get("/customers/export")
def export_customer_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    rep = ReportingService.get_customer_report(db, current_user.company_id, filters)
    cols = ["customer_code", "customer_name", "tier_name", "deal_count", "total_revenue", "average_deal_size", "status"]
    rows = [item.model_dump() for item in rep.items]
    if format == "json":
        return ReportExporter.export_to_json("customer_report", rep.model_dump())
    return ReportExporter.export_to_csv("customer_report", cols, rows)


@router.get("/products", response_model=ProductReportResponse)
def get_product_report(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_product_report(db, current_user.company_id, filters)


@router.get("/products/export")
def export_product_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    rep = ReportingService.get_product_report(db, current_user.company_id, filters)
    cols = ["sku", "name", "category_name", "units_sold", "revenue", "deal_appearances"]
    rows = [item.model_dump() for item in rep.items]
    if format == "json":
        return ReportExporter.export_to_json("product_report", rep.model_dump())
    return ReportExporter.export_to_csv("product_report", cols, rows)


@router.get("/inventory", response_model=InventoryReportResponse)
def get_inventory_report(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_inventory_report(db, current_user.company_id, filters)


@router.get("/inventory/export")
def export_inventory_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    rep = ReportingService.get_inventory_report(db, current_user.company_id, filters)
    cols = ["warehouse_name", "product_sku", "product_name", "physical_quantity", "reserved_quantity", "available_to_promise", "is_low_stock"]
    rows = [item.model_dump() for item in rep.items]
    if format == "json":
        return ReportExporter.export_to_json("inventory_report", rep.model_dump())
    return ReportExporter.export_to_csv("inventory_report", cols, rows)


@router.get("/discounts", response_model=DiscountReportResponse)
def get_discount_report(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_discount_report(db, current_user.company_id, filters)


@router.get("/discounts/export")
def export_discount_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    rep = ReportingService.get_discount_report(db, current_user.company_id, filters)
    cols = ["entity_type", "entity_id", "discount_percentage", "discount_amount", "authority_role", "requires_approval"]
    rows = [item.model_dump() for item in rep.items]
    if format == "json":
        return ReportExporter.export_to_json("discount_report", rep.model_dump())
    return ReportExporter.export_to_csv("discount_report", cols, rows)


@router.get("/approvals", response_model=ApprovalReportResponse)
def get_approval_report(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_approval_report(db, current_user.company_id, filters)


@router.get("/approvals/export")
def export_approval_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    rep = ReportingService.get_approval_report(db, current_user.company_id, filters)
    cols = ["deal_reference", "status", "current_step", "total_steps", "created_at", "completed_at"]
    rows = [item.model_dump() for item in rep.items]
    if format == "json":
        return ReportExporter.export_to_json("approval_report", rep.model_dump())
    return ReportExporter.export_to_csv("approval_report", cols, rows)


@router.get("/deal-health", response_model=DealHealthReportResponse)
def get_deal_health_report(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_deal_health_report(db, current_user.company_id, filters)


@router.get("/deal-health/export")
def export_deal_health_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    rep = ReportingService.get_deal_health_report(db, current_user.company_id, filters)
    cols = ["deal_code", "deal_name", "deal_value", "health_score", "classification", "stall_risk_level", "delay_risk_level", "snapshot_date"]
    rows = [item.model_dump() for item in rep.items]
    if format == "json":
        return ReportExporter.export_to_json("deal_health_report", rep.model_dump())
    return ReportExporter.export_to_csv("deal_health_report", cols, rows)


# ==============================================================================
# Domain Analytics (Phases 360–367)
# ==============================================================================

@router.get("/analytics/revenue", response_model=RevenueAnalyticsResponse)
def get_revenue_analytics(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_revenue_analytics(db, current_user.company_id, filters)


@router.get("/analytics/conversion", response_model=ConversionAnalyticsResponse)
def get_conversion_analytics(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_conversion_analytics(db, current_user.company_id, filters)


@router.get("/analytics/customer", response_model=CustomerAnalyticsReportResponse)
def get_customer_analytics(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_customer_analytics(db, current_user.company_id, filters)


@router.get("/analytics/product", response_model=ProductAnalyticsReportResponse)
def get_product_analytics(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_product_analytics(db, current_user.company_id, filters)


@router.get("/analytics/discount", response_model=DiscountAnalyticsReportResponse)
def get_discount_analytics(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_discount_analytics(db, current_user.company_id, filters)


@router.get("/analytics/inventory", response_model=InventoryAnalyticsReportResponse)
def get_inventory_analytics(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_inventory_analytics(db, current_user.company_id, filters)


@router.get("/analytics/approval", response_model=ApprovalAnalyticsReportResponse)
def get_approval_analytics(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_approval_analytics(db, current_user.company_id, filters)


@router.get("/analytics/deal-health", response_model=DealHealthAnalyticsReportResponse)
def get_deal_health_analytics(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_deal_health_analytics(db, current_user.company_id, filters)


# ==============================================================================
# Consolidated Executive Dashboard (Phase 368)
# ==============================================================================

@router.get("/analytics/dashboard", response_model=ExecutiveDashboardAnalyticsResponse)
def get_executive_dashboard(
    filters: ReportFilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return ReportingService.get_executive_dashboard(db, current_user.company_id, filters)


# ==============================================================================
# Scheduled Reports & Executions (Phase 369)
# ==============================================================================

@router.post("/schedules", response_model=ScheduledReportResponse)
def create_scheduled_report(
    data: ScheduledReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return SchedulingService.create_schedule(
        db=db,
        company_id=current_user.company_id,
        created_by_id=current_user.id,
        data=data,
    )


@router.get("/schedules", response_model=List[ScheduledReportResponse])
def list_scheduled_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return SchedulingService.list_schedules(db, current_user.company_id)


@router.post("/schedules/{schedule_id}/run", response_model=ReportExecutionResponse)
def trigger_scheduled_report(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    try:
        return SchedulingService.trigger_execution(db, current_user.company_id, schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/executions", response_model=List[ReportExecutionResponse])
def list_report_executions(
    schedule_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    return SchedulingService.list_executions(db, current_user.company_id, schedule_id, limit)
