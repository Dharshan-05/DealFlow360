import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select, and_, or_, desc
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.deal import DealProduct, DealStage
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.models.inventory_alert import InventoryAlert
from app.models.applied_discount import AppliedDiscount
from app.models.approval_execution import ApprovalRequest, ApprovalAuditLog
from app.models.deal_health import DealHealthSnapshot, DealHealthClassification
from app.models.billing import Invoice, InvoiceStatus, PaymentStatus
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.quotation import Quotation
from app.reporting.schemas import ReportFilterParams


class ReportingQueries:
    """
    SQLAlchemy Analytical & Reporting Query Layer (Phases 353–367).
    Pure database-side aggregations with strict multi-tenant isolation.
    """

    # --------------------------------------------------------------------------
    # Phase 353: Sales Reports Query
    # --------------------------------------------------------------------------
    @staticmethod
    def get_sales_report_data(
        db: Session,
        company_id: uuid.UUID,
        filters: ReportFilterParams,
    ) -> Tuple[Dict[str, Any], List[CustomerDealHistory]]:
        conditions = [CustomerDealHistory.company_id == company_id]

        if filters.date_from:
            conditions.append(CustomerDealHistory.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(CustomerDealHistory.created_at <= filters.date_to)
        if filters.customer_id:
            conditions.append(CustomerDealHistory.customer_id == filters.customer_id)
        if filters.salesperson_id:
            conditions.append(CustomerDealHistory.owner_id == filters.salesperson_id)
        if filters.status:
            conditions.append(CustomerDealHistory.stage == filters.status.upper())

        deals = list(
            db.scalars(
                select(CustomerDealHistory)
                .where(and_(*conditions))
                .order_by(CustomerDealHistory.created_at.desc())
            )
        )

        total_deals = len(deals)
        won_deals = sum(1 for d in deals if d.stage == DealStage.CLOSED_WON.value)
        lost_deals = sum(1 for d in deals if d.stage == DealStage.CLOSED_LOST.value)
        open_deals = total_deals - won_deals - lost_deals
        win_rate = round((won_deals / total_deals * 100.0) if total_deals > 0 else 0.0, 2)

        total_pipeline = sum((d.deal_value for d in deals), Decimal("0.00"))
        won_revenue = sum(
            (d.deal_value for d in deals if d.stage == DealStage.CLOSED_WON.value),
            Decimal("0.00"),
        )
        avg_deal_value = (
            round(total_pipeline / Decimal(str(total_deals)), 2)
            if total_deals > 0
            else Decimal("0.00")
        )

        summary = {
            "total_deals": total_deals,
            "won_deals": won_deals,
            "lost_deals": lost_deals,
            "open_deals": open_deals,
            "win_rate": win_rate,
            "total_pipeline_value": total_pipeline,
            "total_won_revenue": won_revenue,
            "average_deal_value": avg_deal_value,
        }

        return summary, deals

    # --------------------------------------------------------------------------
    # Phase 354: Customer Reports Query
    # --------------------------------------------------------------------------
    @staticmethod
    def get_customer_report_data(
        db: Session,
        company_id: uuid.UUID,
        filters: ReportFilterParams,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        conditions = [Customer.company_id == company_id]
        if filters.status:
            is_act = filters.status.upper() in {"ACTIVE", "TRUE", "1"}
            conditions.append(Customer.is_active == is_act)

        customers = list(db.scalars(select(Customer).where(and_(*conditions))))
        total_customers = len(customers)
        active_customers = sum(1 for c in customers if c.is_active)
        inactive_customers = total_customers - active_customers
        tiered_customers = sum(1 for c in customers if c.tier_id is not None)

        rows = []
        total_rev = Decimal("0.00")
        for c in customers:
            # Query customer deals
            c_deals = list(
                db.scalars(
                    select(CustomerDealHistory).where(
                        CustomerDealHistory.company_id == company_id,
                        CustomerDealHistory.customer_id == c.id,
                    )
                )
            )
            deal_count = len(c_deals)
            rev = sum(
                (d.deal_value for d in c_deals if d.stage == DealStage.CLOSED_WON.value),
                Decimal("0.00"),
            )
            total_rev += rev
            avg_size = round(rev / Decimal(str(deal_count)), 2) if deal_count > 0 else Decimal("0.00")

            rows.append({
                "customer_id": c.id,
                "customer_name": c.name,
                "customer_code": c.customer_code,
                "tier_name": c.tier.name if c.tier else None,
                "deal_count": deal_count,
                "total_revenue": rev,
                "average_deal_size": avg_size,
                "status": "ACTIVE" if c.is_active else "INACTIVE",
                "created_at": c.created_at,
            })

        # Sort top revenue first
        rows.sort(key=lambda x: x["total_revenue"], reverse=True)

        avg_rev = (
            round(total_rev / Decimal(str(total_customers)), 2)
            if total_customers > 0
            else Decimal("0.00")
        )

        summary = {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "inactive_customers": inactive_customers,
            "tiered_customers": tiered_customers,
            "total_lifetime_revenue": total_rev,
            "average_revenue_per_customer": avg_rev,
        }

        return summary, rows

    # --------------------------------------------------------------------------
    # Phase 355: Product Reports Query
    # --------------------------------------------------------------------------
    @staticmethod
    def get_product_report_data(
        db: Session,
        company_id: uuid.UUID,
        filters: ReportFilterParams,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        conditions = [DealProduct.company_id == company_id]
        if filters.product_id:
            conditions.append(DealProduct.product_id == filters.product_id)

        # Aggregate DealProduct
        deal_prods = list(
            db.scalars(
                select(DealProduct)
                .where(and_(*conditions))
            )
        )

        prod_agg: Dict[uuid.UUID, Dict[str, Any]] = {}
        for dp in deal_prods:
            pid = dp.product_id
            if pid not in prod_agg:
                prod_agg[pid] = {
                    "product_id": pid,
                    "units_sold": Decimal("0.00"),
                    "revenue": Decimal("0.00"),
                    "deal_appearances": 0,
                }
            prod_agg[pid]["units_sold"] += dp.quantity
            prod_agg[pid]["revenue"] += dp.subtotal
            prod_agg[pid]["deal_appearances"] += 1

        rows = []
        total_units = Decimal("0.00")
        total_rev = Decimal("0.00")

        for pid, agg in prod_agg.items():
            product = db.get(Product, pid)
            sku = product.sku if product else "UNKNOWN"
            name = product.name if product else "Unknown Product"
            cat_name = product.category.name if product and product.category else None

            total_units += agg["units_sold"]
            total_rev += agg["revenue"]

            rows.append({
                "product_id": pid,
                "sku": sku,
                "name": name,
                "category_name": cat_name,
                "units_sold": agg["units_sold"],
                "revenue": agg["revenue"],
                "deal_appearances": agg["deal_appearances"],
            })

        rows.sort(key=lambda x: x["revenue"], reverse=True)
        avg_price = (
            round(total_rev / total_units, 2)
            if total_units > Decimal("0.00")
            else Decimal("0.00")
        )

        summary = {
            "total_products_sold": len(rows),
            "total_units_sold": total_units,
            "total_product_revenue": total_rev,
            "average_selling_price": avg_price,
        }

        return summary, rows

    # --------------------------------------------------------------------------
    # Phase 356: Inventory Reports Query
    # --------------------------------------------------------------------------
    @staticmethod
    def get_inventory_report_data(
        db: Session,
        company_id: uuid.UUID,
        filters: ReportFilterParams,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        w_query = select(Warehouse).where(Warehouse.company_id == company_id)
        if filters.warehouse_id:
            w_query = w_query.where(Warehouse.id == filters.warehouse_id)
        warehouses = list(db.scalars(w_query))

        w_ids = [w.id for w in warehouses]
        stocks = list(
            db.scalars(
                select(WarehouseStock).where(WarehouseStock.warehouse_id.in_(w_ids))
            )
        ) if w_ids else []

        w_map = {w.id: w.name for w in warehouses}

        rows = []
        total_phys = 0
        total_res = 0
        total_atp = 0
        low_stock_count = 0

        for s in stocks:
            prod = db.get(Product, s.product_id)
            is_low = s.available_to_promise <= 10

            total_phys += s.quantity
            total_res += s.reserved_quantity
            total_atp += s.available_to_promise
            if is_low:
                low_stock_count += 1

            rows.append({
                "warehouse_id": s.warehouse_id,
                "warehouse_name": w_map.get(s.warehouse_id, "Unknown"),
                "product_id": s.product_id,
                "product_sku": prod.sku if prod else "UNKNOWN",
                "product_name": prod.name if prod else "Unknown Product",
                "physical_quantity": s.quantity,
                "reserved_quantity": s.reserved_quantity,
                "available_to_promise": s.available_to_promise,
                "is_low_stock": is_low,
            })

        summary = {
            "total_warehouses": len(warehouses),
            "total_stock_items": len(stocks),
            "total_physical_quantity": total_phys,
            "total_reserved_quantity": total_res,
            "total_atp_quantity": total_atp,
            "low_stock_sku_count": low_stock_count,
        }

        return summary, rows

    # --------------------------------------------------------------------------
    # Phase 357: Discount Reports Query
    # --------------------------------------------------------------------------
    @staticmethod
    def get_discount_report_data(
        db: Session,
        company_id: uuid.UUID,
        filters: ReportFilterParams,
    ) -> Tuple[Dict[str, Any], List[AppliedDiscount]]:
        conditions = [AppliedDiscount.company_id == company_id]
        if filters.date_from:
            conditions.append(AppliedDiscount.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(AppliedDiscount.created_at <= filters.date_to)

        discounts = list(
            db.scalars(
                select(AppliedDiscount)
                .where(and_(*conditions))
                .order_by(AppliedDiscount.created_at.desc())
            )
        )

        total_discounts = len(discounts)
        total_amount = sum((d.discount_amount for d in discounts), Decimal("0.00"))
        avg_pct = (
            round(sum(d.discount_percentage for d in discounts) / Decimal(str(total_discounts)), 2)
            if total_discounts > 0
            else Decimal("0.00")
        )
        overrides = sum(1 for d in discounts if d.requires_approval)

        summary = {
            "total_discounts_granted": total_discounts,
            "total_discount_amount": total_amount,
            "average_discount_percentage": avg_pct,
            "policy_overrides_count": overrides,
        }

        return summary, discounts

    # --------------------------------------------------------------------------
    # Phase 358: Approval Reports Query
    # --------------------------------------------------------------------------
    @staticmethod
    def get_approval_report_data(
        db: Session,
        company_id: uuid.UUID,
        filters: ReportFilterParams,
    ) -> Tuple[Dict[str, Any], List[ApprovalRequest]]:
        conditions = [ApprovalRequest.company_id == company_id]
        if filters.status:
            conditions.append(ApprovalRequest.status == filters.status.upper())
        if filters.date_from:
            conditions.append(ApprovalRequest.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(ApprovalRequest.created_at <= filters.date_to)

        requests = list(
            db.scalars(
                select(ApprovalRequest)
                .where(and_(*conditions))
                .order_by(ApprovalRequest.created_at.desc())
            )
        )

        total_reqs = len(requests)
        pending = sum(1 for r in requests if r.status in {"PENDING", "IN_PROGRESS"})
        approved = sum(1 for r in requests if r.status == "APPROVED")
        rejected = sum(1 for r in requests if r.status == "REJECTED")
        app_rate = round((approved / total_reqs * 100.0) if total_reqs > 0 else 0.0, 2)

        # Average turnaround hours
        turnaround_hours = []
        for r in requests:
            if r.final_actioned_at and r.created_at:
                diff = (r.final_actioned_at - r.created_at).total_seconds() / 3600.0
                turnaround_hours.append(diff)
        avg_turnaround = round(sum(turnaround_hours) / len(turnaround_hours), 1) if turnaround_hours else 0.0

        summary = {
            "total_requests": total_reqs,
            "pending_requests": pending,
            "approved_requests": approved,
            "rejected_requests": rejected,
            "approval_rate": app_rate,
            "average_turnaround_hours": avg_turnaround,
        }

        return summary, requests

    # --------------------------------------------------------------------------
    # Phase 359: Deal Health Reports Query
    # --------------------------------------------------------------------------
    @staticmethod
    def get_deal_health_report_data(
        db: Session,
        company_id: uuid.UUID,
        filters: ReportFilterParams,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        # Fetch latest snapshot per deal
        subq = (
            select(
                DealHealthSnapshot.deal_id,
                func.max(DealHealthSnapshot.created_at).label("max_date"),
            )
            .where(DealHealthSnapshot.company_id == company_id)
            .group_by(DealHealthSnapshot.deal_id)
            .subquery()
        )

        stmt = (
            select(DealHealthSnapshot)
            .join(
                subq,
                and_(
                    DealHealthSnapshot.deal_id == subq.c.deal_id,
                    DealHealthSnapshot.created_at == subq.c.max_date,
                ),
            )
            .order_by(DealHealthSnapshot.health_score.asc())
        )

        snapshots = list(db.scalars(stmt))

        total_monitored = len(snapshots)
        healthy = sum(1 for s in snapshots if s.classification == DealHealthClassification.HEALTHY.value)
        at_risk = sum(1 for s in snapshots if s.classification == DealHealthClassification.AT_RISK.value)
        critical = sum(1 for s in snapshots if s.classification == DealHealthClassification.CRITICAL.value)

        avg_score = (
            round(sum(float(s.health_score) for s in snapshots) / total_monitored, 2)
            if total_monitored > 0
            else 0.0
        )

        rows = []
        at_risk_val = Decimal("0.00")
        for s in snapshots:
            deal = db.get(CustomerDealHistory, s.deal_id)
            val = deal.deal_value if deal else Decimal("0.00")
            if s.classification in {DealHealthClassification.AT_RISK.value, DealHealthClassification.CRITICAL.value}:
                at_risk_val += val

            rows.append({
                "deal_id": s.deal_id,
                "deal_code": deal.deal_code if deal else "UNKNOWN",
                "deal_name": deal.title if deal else "Unknown Deal",
                "deal_value": val,
                "health_score": s.health_score,
                "classification": s.classification,
                "stall_risk_level": str(s.stall_probability),
                "delay_risk_level": str(s.delay_probability),
                "snapshot_date": s.created_at,
            })

        summary = {
            "total_monitored_deals": total_monitored,
            "healthy_deals_count": healthy,
            "at_risk_deals_count": at_risk,
            "critical_deals_count": critical,
            "average_health_score": avg_score,
            "total_at_risk_value": at_risk_val,
        }

        return summary, rows
