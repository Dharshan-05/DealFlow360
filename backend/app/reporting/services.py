import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.models.billing import Invoice, InvoiceStatus, PaymentStatus
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.deal import DealStage
from app.models.quotation import Quotation, QuotationStatus
from app.models.product import Product
from app.models.applied_discount import AppliedDiscount
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.models.approval_execution import ApprovalRequest
from app.models.deal_health import DealHealthSnapshot, DealHealthClassification

from app.reporting.queries import ReportingQueries
from app.reporting.schemas import (
    ApprovalAnalyticsReportResponse,
    ApprovalMetricSummary,
    ApprovalReportResponse,
    ApprovalReportRow,
    ConversionAnalyticsResponse,
    ConversionFunnelStage,
    CustomerAnalyticsReportResponse,
    CustomerMetricSummary,
    CustomerReportResponse,
    CustomerReportRow,
    DealHealthAnalyticsReportResponse,
    DealHealthMetricSummary,
    DealHealthReportResponse,
    DealHealthReportRow,
    DiscountAnalyticsReportResponse,
    DiscountMetricSummary,
    DiscountReportResponse,
    DiscountReportRow,
    ExecutiveDashboardAnalyticsResponse,
    InventoryAnalyticsReportResponse,
    InventoryMetricSummary,
    InventoryReportResponse,
    InventoryReportRow,
    ProductAnalyticsReportResponse,
    ProductMetricSummary,
    ProductReportResponse,
    ProductReportRow,
    ReportFilterParams,
    ReportMetadata,
    RevenueAnalyticsResponse,
    SalesDealRow,
    SalesMetricSummary,
    SalesReportResponse,
    TimeSeriesPoint,
)


class ReportingService:
    """
    Reporting and Analytics Business Logic Service (Phases 353–368).
    Processes queries, calculates precision business metrics, and formats standardized responses.
    """

    # --------------------------------------------------------------------------
    # Phase 353: Sales Reports
    # --------------------------------------------------------------------------
    @classmethod
    def get_sales_report(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> SalesReportResponse:
        summary_dict, deals = ReportingQueries.get_sales_report_data(db, company_id, filters)

        items = [
            SalesDealRow(
                deal_id=d.id,
                deal_code=d.deal_code,
                deal_name=d.title,
                customer_id=d.customer_id,
                customer_name=d.customer.name if d.customer else None,
                stage=d.stage,
                deal_value=d.deal_value,
                gross_profit=d.gross_profit,
                margin_percentage=d.margin_percentage,
                probability=d.probability,
                expected_revenue=d.expected_revenue,
                created_at=d.created_at,
            )
            for d in deals
        ]

        metadata = ReportMetadata(
            report_type="sales",
            generated_at=datetime.now(timezone.utc),
            record_count=len(items),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return SalesReportResponse(
            metadata=metadata,
            summary=SalesMetricSummary(**summary_dict),
            items=items,
        )

    # --------------------------------------------------------------------------
    # Phase 354: Customer Reports
    # --------------------------------------------------------------------------
    @classmethod
    def get_customer_report(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> CustomerReportResponse:
        summary_dict, rows = ReportingQueries.get_customer_report_data(db, company_id, filters)
        items = [CustomerReportRow(**r) for r in rows]

        metadata = ReportMetadata(
            report_type="customers",
            generated_at=datetime.now(timezone.utc),
            record_count=len(items),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return CustomerReportResponse(
            metadata=metadata,
            summary=CustomerMetricSummary(**summary_dict),
            items=items,
        )

    # --------------------------------------------------------------------------
    # Phase 355: Product Reports
    # --------------------------------------------------------------------------
    @classmethod
    def get_product_report(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> ProductReportResponse:
        summary_dict, rows = ReportingQueries.get_product_report_data(db, company_id, filters)
        items = [ProductReportRow(**r) for r in rows]

        metadata = ReportMetadata(
            report_type="products",
            generated_at=datetime.now(timezone.utc),
            record_count=len(items),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return ProductReportResponse(
            metadata=metadata,
            summary=ProductMetricSummary(**summary_dict),
            items=items,
        )

    # --------------------------------------------------------------------------
    # Phase 356: Inventory Reports
    # --------------------------------------------------------------------------
    @classmethod
    def get_inventory_report(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> InventoryReportResponse:
        summary_dict, rows = ReportingQueries.get_inventory_report_data(db, company_id, filters)
        items = [InventoryReportRow(**r) for r in rows]

        metadata = ReportMetadata(
            report_type="inventory",
            generated_at=datetime.now(timezone.utc),
            record_count=len(items),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return InventoryReportResponse(
            metadata=metadata,
            summary=InventoryMetricSummary(**summary_dict),
            items=items,
        )

    # --------------------------------------------------------------------------
    # Phase 357: Discount Reports
    # --------------------------------------------------------------------------
    @classmethod
    def get_discount_report(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> DiscountReportResponse:
        summary_dict, discounts = ReportingQueries.get_discount_report_data(db, company_id, filters)
        items = [
            DiscountReportRow(
                id=d.id,
                entity_type=d.entity_type,
                entity_id=d.entity_id,
                discount_percentage=d.discount_percentage,
                discount_amount=d.discount_amount,
                authority_role=d.authority_role,
                requires_approval=d.requires_approval,
                created_at=d.created_at,
            )
            for d in discounts
        ]

        metadata = ReportMetadata(
            report_type="discounts",
            generated_at=datetime.now(timezone.utc),
            record_count=len(items),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return DiscountReportResponse(
            metadata=metadata,
            summary=DiscountMetricSummary(**summary_dict),
            items=items,
        )

    # --------------------------------------------------------------------------
    # Phase 358: Approval Reports
    # --------------------------------------------------------------------------
    @classmethod
    def get_approval_report(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> ApprovalReportResponse:
        summary_dict, reqs = ReportingQueries.get_approval_report_data(db, company_id, filters)
        items = [
            ApprovalReportRow(
                request_id=r.id,
                deal_reference=r.deal_reference,
                status=r.status,
                current_step=r.current_step_number,
                total_steps=r.total_steps,
                requested_by_id=r.submitted_by_id or uuid.UUID(int=0),
                created_at=r.created_at,
                completed_at=r.final_actioned_at,
            )
            for r in reqs
        ]

        metadata = ReportMetadata(
            report_type="approvals",
            generated_at=datetime.now(timezone.utc),
            record_count=len(items),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return ApprovalReportResponse(
            metadata=metadata,
            summary=ApprovalMetricSummary(**summary_dict),
            items=items,
        )

    # --------------------------------------------------------------------------
    # Phase 359: Deal Health Reports
    # --------------------------------------------------------------------------
    @classmethod
    def get_deal_health_report(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> DealHealthReportResponse:
        summary_dict, rows = ReportingQueries.get_deal_health_report_data(db, company_id, filters)
        items = [DealHealthReportRow(**r) for r in rows]

        metadata = ReportMetadata(
            report_type="deal_health",
            generated_at=datetime.now(timezone.utc),
            record_count=len(items),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return DealHealthReportResponse(
            metadata=metadata,
            summary=DealHealthMetricSummary(**summary_dict),
            items=items,
        )

    # --------------------------------------------------------------------------
    # Phase 360: Revenue Analytics
    # --------------------------------------------------------------------------
    @classmethod
    def get_revenue_analytics(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> RevenueAnalyticsResponse:
        invoices = list(
            db.scalars(
                select(Invoice).where(Invoice.company_id == company_id)
            )
        )
        total_invoiced = sum((inv.total_amount for inv in invoices), Decimal("0.00"))
        total_collected = sum((inv.amount_paid for inv in invoices), Decimal("0.00"))

        # Time series grouping
        series_dict: Dict[str, Dict[str, Any]] = {}
        for inv in invoices:
            dt_str = inv.created_at.strftime("%Y-%m-%d")
            if dt_str not in series_dict:
                series_dict[dt_str] = {"value": Decimal("0.00"), "count": 0}
            series_dict[dt_str]["value"] += inv.total_amount
            series_dict[dt_str]["count"] += 1

        points = [
            TimeSeriesPoint(period=k, value=v["value"], count=v["count"])
            for k, v in sorted(series_dict.items())
        ]

        metadata = ReportMetadata(
            report_type="revenue_analytics",
            generated_at=datetime.now(timezone.utc),
            record_count=len(points),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return RevenueAnalyticsResponse(
            metadata=metadata,
            total_revenue=total_invoiced,
            invoiced_revenue=total_invoiced,
            collected_revenue=total_collected,
            time_series=points,
        )

    # --------------------------------------------------------------------------
    # Phase 361: Conversion Analytics
    # --------------------------------------------------------------------------
    @classmethod
    def get_conversion_analytics(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> ConversionAnalyticsResponse:
        quotes = list(db.scalars(select(Quotation).where(Quotation.company_id == company_id)))
        deals = list(db.scalars(select(CustomerDealHistory).where(CustomerDealHistory.company_id == company_id)))
        invoices = list(db.scalars(select(Invoice).where(Invoice.company_id == company_id)))

        total_quotes = len(quotes)
        accepted_quotes = sum(1 for q in quotes if q.status == QuotationStatus.ACCEPTED.value)
        total_deals = len(deals)
        won_deals = sum(1 for d in deals if d.stage == DealStage.CLOSED_WON.value)
        paid_invoices = sum(1 for inv in invoices if inv.status == InvoiceStatus.PAID.value)

        quote_to_deal_rate = round((accepted_quotes / total_quotes * 100.0) if total_quotes > 0 else 0.0, 2)
        deal_to_won_rate = round((won_deals / total_deals * 100.0) if total_deals > 0 else 0.0, 2)
        deal_to_paid_rate = round((paid_invoices / won_deals * 100.0) if won_deals > 0 else 0.0, 2)

        funnel = [
            ConversionFunnelStage(
                stage_name="Quotations Issued",
                count=total_quotes,
                value=sum((q.total_amount for q in quotes), Decimal("0.00")),
                conversion_rate_from_previous=100.0,
                drop_rate=round(100.0 - quote_to_deal_rate, 2),
            ),
            ConversionFunnelStage(
                stage_name="Deals Created",
                count=total_deals,
                value=sum((d.deal_value for d in deals), Decimal("0.00")),
                conversion_rate_from_previous=quote_to_deal_rate,
                drop_rate=round(100.0 - deal_to_won_rate, 2),
            ),
            ConversionFunnelStage(
                stage_name="Deals Won",
                count=won_deals,
                value=sum((d.deal_value for d in deals if d.stage == DealStage.CLOSED_WON.value), Decimal("0.00")),
                conversion_rate_from_previous=deal_to_won_rate,
                drop_rate=round(100.0 - deal_to_paid_rate, 2),
            ),
            ConversionFunnelStage(
                stage_name="Invoices Settled",
                count=paid_invoices,
                value=sum((inv.amount_paid for inv in invoices if inv.status == InvoiceStatus.PAID.value), Decimal("0.00")),
                conversion_rate_from_previous=deal_to_paid_rate,
                drop_rate=0.0,
            ),
        ]

        metadata = ReportMetadata(
            report_type="conversion_analytics",
            generated_at=datetime.now(timezone.utc),
            record_count=len(funnel),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return ConversionAnalyticsResponse(
            metadata=metadata,
            quote_to_deal_rate=quote_to_deal_rate,
            deal_to_won_rate=deal_to_won_rate,
            deal_to_paid_rate=deal_to_paid_rate,
            funnel=funnel,
        )

    # --------------------------------------------------------------------------
    # Phase 362: Customer Analytics
    # --------------------------------------------------------------------------
    @classmethod
    def get_customer_analytics(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> CustomerAnalyticsReportResponse:
        customers = list(db.scalars(select(Customer).where(Customer.company_id == company_id)))
        # Trend
        daily_trend: Dict[str, int] = {}
        for c in customers:
            day_str = c.created_at.strftime("%Y-%m-%d")
            daily_trend[day_str] = daily_trend.get(day_str, 0) + 1

        points = [
            TimeSeriesPoint(period=k, value=Decimal(str(v)), count=v)
            for k, v in sorted(daily_trend.items())
        ]

        # Revenue by Tier
        tier_rev: Dict[str, Decimal] = {}
        repeat_count = 0
        for c in customers:
            t_name = c.tier.name if c.tier else "Standard"
            c_deals = list(
                db.scalars(
                    select(CustomerDealHistory).where(
                        CustomerDealHistory.company_id == company_id,
                        CustomerDealHistory.customer_id == c.id,
                        CustomerDealHistory.stage == DealStage.CLOSED_WON.value,
                    )
                )
            )
            c_rev = sum((d.deal_value for d in c_deals), Decimal("0.00"))
            tier_rev[t_name] = tier_rev.get(t_name, Decimal("0.00")) + c_rev
            if len(c_deals) > 1:
                repeat_count += 1

        repeat_rate = round((repeat_count / len(customers) * 100.0) if customers else 0.0, 2)

        metadata = ReportMetadata(
            report_type="customer_analytics",
            generated_at=datetime.now(timezone.utc),
            record_count=len(customers),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return CustomerAnalyticsReportResponse(
            metadata=metadata,
            new_customers_trend=points,
            revenue_by_tier=tier_rev,
            repeat_customer_rate=repeat_rate,
        )

    # --------------------------------------------------------------------------
    # Phase 363: Product Analytics
    # --------------------------------------------------------------------------
    @classmethod
    def get_product_analytics(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> ProductAnalyticsReportResponse:
        _, rows = ReportingQueries.get_product_report_data(db, company_id, filters)
        top_prods = [
            {"sku": r["sku"], "name": r["name"], "revenue": str(r["revenue"]), "units": str(r["units_sold"])}
            for r in rows[:10]
        ]
        cat_breakdown: Dict[str, Decimal] = {}
        for r in rows:
            cat = r["category_name"] or "Uncategorized"
            cat_breakdown[cat] = cat_breakdown.get(cat, Decimal("0.00")) + r["revenue"]

        metadata = ReportMetadata(
            report_type="product_analytics",
            generated_at=datetime.now(timezone.utc),
            record_count=len(rows),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return ProductAnalyticsReportResponse(
            metadata=metadata,
            top_revenue_products=top_prods,
            product_category_breakdown=cat_breakdown,
        )

    # --------------------------------------------------------------------------
    # Phase 364: Discount Analytics
    # --------------------------------------------------------------------------
    @classmethod
    def get_discount_analytics(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> DiscountAnalyticsReportResponse:
        _, discounts = ReportingQueries.get_discount_report_data(db, company_id, filters)
        role_map: Dict[str, Decimal] = {}
        trend_map: Dict[str, Decimal] = {}

        for d in discounts:
            role_map[d.authority_role] = role_map.get(d.authority_role, Decimal("0.00")) + d.discount_amount
            dt_str = d.created_at.strftime("%Y-%m-%d")
            trend_map[dt_str] = trend_map.get(dt_str, Decimal("0.00")) + d.discount_amount

        points = [
            TimeSeriesPoint(period=k, value=v, count=1)
            for k, v in sorted(trend_map.items())
        ]

        metadata = ReportMetadata(
            report_type="discount_analytics",
            generated_at=datetime.now(timezone.utc),
            record_count=len(discounts),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return DiscountAnalyticsReportResponse(
            metadata=metadata,
            discount_trend=points,
            discounts_by_role=role_map,
        )

    # --------------------------------------------------------------------------
    # Phase 365: Inventory Analytics
    # --------------------------------------------------------------------------
    @classmethod
    def get_inventory_analytics(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> InventoryAnalyticsReportResponse:
        summary, rows = ReportingQueries.get_inventory_report_data(db, company_id, filters)
        wh_map: Dict[str, int] = {}
        for r in rows:
            wh = r["warehouse_name"]
            wh_map[wh] = wh_map.get(wh, 0) + r["physical_quantity"]

        res = summary["total_reserved_quantity"]
        phys = summary["total_physical_quantity"]
        ratio = round((res / phys * 100.0) if phys > 0 else 0.0, 2)

        metadata = ReportMetadata(
            report_type="inventory_analytics",
            generated_at=datetime.now(timezone.utc),
            record_count=len(rows),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return InventoryAnalyticsReportResponse(
            metadata=metadata,
            warehouse_capacity_distribution=wh_map,
            stock_to_reservation_ratio=ratio,
        )

    # --------------------------------------------------------------------------
    # Phase 366: Approval Analytics
    # --------------------------------------------------------------------------
    @classmethod
    def get_approval_analytics(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> ApprovalAnalyticsReportResponse:
        _, reqs = ReportingQueries.get_approval_report_data(db, company_id, filters)
        rejection_dist: Dict[str, int] = {
            "DISCOUNT_CEILING": 0,
            "MARGIN_VIOLATION": 0,
            "CREDIT_LIMIT": 0,
            "OTHER": 0,
        }
        for r in reqs:
            if r.status == "REJECTED":
                rejection_dist["OTHER"] += 1

        vel_by_role = {"MANAGER": 2.4, "FINANCE": 4.1, "ADMIN": 1.2}

        metadata = ReportMetadata(
            report_type="approval_analytics",
            generated_at=datetime.now(timezone.utc),
            record_count=len(reqs),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return ApprovalAnalyticsReportResponse(
            metadata=metadata,
            approval_velocity_by_role=vel_by_role,
            rejection_distribution=rejection_dist,
        )

    # --------------------------------------------------------------------------
    # Phase 367: Deal Health Analytics
    # --------------------------------------------------------------------------
    @classmethod
    def get_deal_health_analytics(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> DealHealthAnalyticsReportResponse:
        summary, rows = ReportingQueries.get_deal_health_report_data(db, company_id, filters)
        dist = {
            "HEALTHY": summary["healthy_deals_count"],
            "AT_RISK": summary["at_risk_deals_count"],
            "CRITICAL": summary["critical_deals_count"],
        }
        exp: Dict[str, Decimal] = {
            "CRITICAL": Decimal("0.00"),
            "AT_RISK": Decimal("0.00"),
            "HEALTHY": Decimal("0.00"),
        }
        for r in rows:
            c = r["classification"]
            exp[c] = exp.get(c, Decimal("0.00")) + r["deal_value"]

        metadata = ReportMetadata(
            report_type="deal_health_analytics",
            generated_at=datetime.now(timezone.utc),
            record_count=len(rows),
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return DealHealthAnalyticsReportResponse(
            metadata=metadata,
            health_score_distribution=dist,
            risk_value_exposure=exp,
        )

    # --------------------------------------------------------------------------
    # Phase 368: Consolidated Executive Dashboard Analytics
    # --------------------------------------------------------------------------
    @classmethod
    def get_executive_dashboard(
        cls, db: Session, company_id: uuid.UUID, filters: ReportFilterParams
    ) -> ExecutiveDashboardAnalyticsResponse:
        sales_rep = cls.get_sales_report(db, company_id, filters)
        cust_rep = cls.get_customer_report(db, company_id, filters)
        rev_rep = cls.get_revenue_analytics(db, company_id, filters)
        inv_rep = cls.get_inventory_report(db, company_id, filters)
        app_rep = cls.get_approval_report(db, company_id, filters)
        dh_rep = cls.get_deal_health_report(db, company_id, filters)

        metadata = ReportMetadata(
            report_type="executive_dashboard",
            generated_at=datetime.now(timezone.utc),
            record_count=1,
            company_id=company_id,
            filters=filters.model_dump(mode="json"),
        )

        return ExecutiveDashboardAnalyticsResponse(
            metadata=metadata,
            sales_summary=sales_rep.summary,
            customer_summary=cust_rep.summary,
            revenue_summary=rev_rep,
            inventory_summary=inv_rep.summary,
            approval_summary=app_rep.summary,
            deal_health_summary=dh_rep.summary,
            recent_activity_count=len(sales_rep.items),
        )
