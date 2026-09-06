from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import uuid
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# Filter Parameters
# ==============================================================================

class ReportFilterParams(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    customer_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    warehouse_id: Optional[uuid.UUID] = None
    salesperson_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    group_by: Optional[str] = Field("day", description="Aggregation granularity: day, week, month")


class ReportMetadata(BaseModel):
    report_type: str
    generated_at: datetime
    record_count: int
    company_id: uuid.UUID
    filters: Dict[str, Any] = Field(default_factory=dict)


# ==============================================================================
# Phase 353: Sales Reports Schemas
# ==============================================================================

class SalesMetricSummary(BaseModel):
    total_deals: int
    won_deals: int
    lost_deals: int
    open_deals: int
    win_rate: float
    total_pipeline_value: Decimal
    total_won_revenue: Decimal
    average_deal_value: Decimal


class SalesDealRow(BaseModel):
    deal_id: uuid.UUID
    deal_code: str
    deal_name: str
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    stage: str
    deal_value: Decimal
    gross_profit: Decimal
    margin_percentage: Decimal
    probability: int
    expected_revenue: Decimal
    created_at: datetime


class SalesReportResponse(BaseModel):
    metadata: ReportMetadata
    summary: SalesMetricSummary
    items: List[SalesDealRow]


# ==============================================================================
# Phase 354: Customer Reports Schemas
# ==============================================================================

class CustomerMetricSummary(BaseModel):
    total_customers: int
    active_customers: int
    inactive_customers: int
    tiered_customers: int
    total_lifetime_revenue: Decimal
    average_revenue_per_customer: Decimal


class CustomerReportRow(BaseModel):
    customer_id: uuid.UUID
    customer_name: str
    customer_code: str
    tier_name: Optional[str] = None
    deal_count: int
    total_revenue: Decimal
    average_deal_size: Decimal
    status: str
    created_at: datetime


class CustomerReportResponse(BaseModel):
    metadata: ReportMetadata
    summary: CustomerMetricSummary
    items: List[CustomerReportRow]


# ==============================================================================
# Phase 355: Product Reports Schemas
# ==============================================================================

class ProductMetricSummary(BaseModel):
    total_products_sold: int
    total_units_sold: Decimal
    total_product_revenue: Decimal
    average_selling_price: Decimal


class ProductReportRow(BaseModel):
    product_id: uuid.UUID
    sku: str
    name: str
    category_name: Optional[str] = None
    units_sold: Decimal
    revenue: Decimal
    deal_appearances: int


class ProductReportResponse(BaseModel):
    metadata: ReportMetadata
    summary: ProductMetricSummary
    items: List[ProductReportRow]


# ==============================================================================
# Phase 356: Inventory Reports Schemas
# ==============================================================================

class InventoryMetricSummary(BaseModel):
    total_warehouses: int
    total_stock_items: int
    total_physical_quantity: int
    total_reserved_quantity: int
    total_atp_quantity: int
    low_stock_sku_count: int


class InventoryReportRow(BaseModel):
    warehouse_id: uuid.UUID
    warehouse_name: str
    product_id: uuid.UUID
    product_sku: str
    product_name: str
    physical_quantity: int
    reserved_quantity: int
    available_to_promise: int
    is_low_stock: bool


class InventoryReportResponse(BaseModel):
    metadata: ReportMetadata
    summary: InventoryMetricSummary
    items: List[InventoryReportRow]


# ==============================================================================
# Phase 357: Discount Reports Schemas
# ==============================================================================

class DiscountMetricSummary(BaseModel):
    total_discounts_granted: int
    total_discount_amount: Decimal
    average_discount_percentage: Decimal
    policy_overrides_count: int


class DiscountReportRow(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    discount_percentage: Decimal
    discount_amount: Decimal
    authority_role: str
    requires_approval: bool
    created_at: datetime


class DiscountReportResponse(BaseModel):
    metadata: ReportMetadata
    summary: DiscountMetricSummary
    items: List[DiscountReportRow]


# ==============================================================================
# Phase 358: Approval Reports Schemas
# ==============================================================================

class ApprovalMetricSummary(BaseModel):
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    approval_rate: float
    average_turnaround_hours: float


class ApprovalReportRow(BaseModel):
    request_id: uuid.UUID
    deal_reference: str
    status: str
    current_step: int
    total_steps: int
    requested_by_id: uuid.UUID
    created_at: datetime
    completed_at: Optional[datetime] = None


class ApprovalReportResponse(BaseModel):
    metadata: ReportMetadata
    summary: ApprovalMetricSummary
    items: List[ApprovalReportRow]


# ==============================================================================
# Phase 359: Deal Health Reports Schemas
# ==============================================================================

class DealHealthMetricSummary(BaseModel):
    total_monitored_deals: int
    healthy_deals_count: int
    at_risk_deals_count: int
    critical_deals_count: int
    average_health_score: float
    total_at_risk_value: Decimal


class DealHealthReportRow(BaseModel):
    deal_id: uuid.UUID
    deal_code: str
    deal_name: str
    deal_value: Decimal
    health_score: Decimal
    classification: str
    stall_risk_level: Optional[str] = None
    delay_risk_level: Optional[str] = None
    snapshot_date: datetime


class DealHealthReportResponse(BaseModel):
    metadata: ReportMetadata
    summary: DealHealthMetricSummary
    items: List[DealHealthReportRow]


# ==============================================================================
# Phases 360–367: Domain Analytics Schemas
# ==============================================================================

class TimeSeriesPoint(BaseModel):
    period: str
    value: Decimal
    count: int = 0


class RevenueAnalyticsResponse(BaseModel):
    metadata: ReportMetadata
    total_revenue: Decimal
    invoiced_revenue: Decimal
    collected_revenue: Decimal
    time_series: List[TimeSeriesPoint]


class ConversionFunnelStage(BaseModel):
    stage_name: str
    count: int
    value: Decimal
    conversion_rate_from_previous: float
    drop_rate: float


class ConversionAnalyticsResponse(BaseModel):
    metadata: ReportMetadata
    quote_to_deal_rate: float
    deal_to_won_rate: float
    deal_to_paid_rate: float
    funnel: List[ConversionFunnelStage]


class CustomerAnalyticsReportResponse(BaseModel):
    metadata: ReportMetadata
    new_customers_trend: List[TimeSeriesPoint]
    revenue_by_tier: Dict[str, Decimal]
    repeat_customer_rate: float


class ProductAnalyticsReportResponse(BaseModel):
    metadata: ReportMetadata
    top_revenue_products: List[Dict[str, Any]]
    product_category_breakdown: Dict[str, Decimal]


class DiscountAnalyticsReportResponse(BaseModel):
    metadata: ReportMetadata
    discount_trend: List[TimeSeriesPoint]
    discounts_by_role: Dict[str, Decimal]


class InventoryAnalyticsReportResponse(BaseModel):
    metadata: ReportMetadata
    warehouse_capacity_distribution: Dict[str, int]
    stock_to_reservation_ratio: float


class ApprovalAnalyticsReportResponse(BaseModel):
    metadata: ReportMetadata
    approval_velocity_by_role: Dict[str, float]
    rejection_distribution: Dict[str, int]


class DealHealthAnalyticsReportResponse(BaseModel):
    metadata: ReportMetadata
    health_score_distribution: Dict[str, int]
    risk_value_exposure: Dict[str, Decimal]


# ==============================================================================
# Phase 368: Consolidated Executive Dashboard Analytics
# ==============================================================================

class ExecutiveDashboardAnalyticsResponse(BaseModel):
    metadata: ReportMetadata
    sales_summary: SalesMetricSummary
    customer_summary: CustomerMetricSummary
    revenue_summary: RevenueAnalyticsResponse
    inventory_summary: InventoryMetricSummary
    approval_summary: ApprovalMetricSummary
    deal_health_summary: DealHealthMetricSummary
    recent_activity_count: int


# ==============================================================================
# Phase 369: Scheduled Reports & Export Schemas
# ==============================================================================

class ScheduledReportCreate(BaseModel):
    name: str
    report_type: str
    filters: Optional[Dict[str, Any]] = None
    frequency: str = "WEEKLY"
    format: str = "CSV"
    recipients: Optional[List[str]] = None
    is_active: bool = True


class ScheduledReportResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    report_type: str
    filters: Optional[Dict[str, Any]] = None
    frequency: str
    format: str
    recipients: Optional[List[str]] = None
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportExecutionResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    scheduled_report_id: Optional[uuid.UUID] = None
    report_type: str
    status: str
    row_count: int
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)
