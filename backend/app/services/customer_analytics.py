"""Customer Analytics Service (Phases 066–070).

Provides deterministic calculations for:
- Phase 066: Customer Analytics (portfolio aggregates, transaction totals, distributions)
- Phase 067 & 068: Search & filtering helpers
- Phase 069: Customer Segmentation (deterministic rule-based portfolio segmentation)
- Phase 070: Customer Dashboard (consolidated KPIs, charts, and activity summaries)
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.customer_purchase_history import CustomerPurchaseHistory
from app.models.customer_tier import CustomerTier
from app.models.user import User
from app.schemas.customer_analytics import (
    ChartDataPointResponse,
    CustomerAnalyticsSummary,
    CustomerDashboardResponse,
    CustomerSegmentProfile,
    CustomerSegmentationSummary,
    CustomerSegmentType,
    DashboardKpiSummary,
    SegmentDistributionItem,
    TierDistributionItem,
)
from app.services.authorization import AuthorizationService
from app.services.customer_financial_intelligence import CustomerFinancialIntelligenceService


class CustomerAnalyticsService:
    """Dedicated analytical and aggregation service for Customer Management."""

    @classmethod
    def _get_scoped_customer_query(cls, current_user: User):
        """Base query scoped strictly to authenticated user's organization."""
        query = select(Customer).options(joinedload(Customer.tier))
        from app.services.rbac import RBACRoleNames, RBACService
        if not RBACService.has_role(current_user, RBACRoleNames.ADMIN):
            if current_user.company_id is None:
                return query.where(Customer.id == None)  # Safe empty query
            query = query.where(Customer.company_id == current_user.company_id)
        return query

    @classmethod
    def get_analytics(
        cls,
        db: Session,
        current_user: User,
    ) -> CustomerAnalyticsSummary:
        """Phase 066: Customer Analytics portfolio summary."""
        customers = db.scalars(cls._get_scoped_customer_query(current_user)).unique().all()
        customer_ids = [c.id for c in customers]

        total_customers = len(customers)
        active_customers = sum(1 for c in customers if c.is_active)
        inactive_customers = total_customers - active_customers
        tiered_customers = sum(1 for c in customers if c.tier_id is not None)
        standard_customers = total_customers - tiered_customers

        # Safe zero-state if no customers exist
        if total_customers == 0:
            return CustomerAnalyticsSummary(
                total_customers=0,
                active_customers=0,
                inactive_customers=0,
                tiered_customers=0,
                standard_customers=0,
                total_purchases_count=0,
                total_purchases_amount=Decimal("0.00"),
                total_deals_count=0,
                total_deals_value=Decimal("0.00"),
                total_payments_count=0,
                total_payments_amount=Decimal("0.00"),
                total_discounts_count=0,
                total_discounts_amount=Decimal("0.00"),
                average_customer_ltv=Decimal("0.00"),
                average_order_value=Decimal("0.00"),
                average_discount_percentage=Decimal("0.00"),
                tier_distribution=[],
                calculated_at=datetime.now(timezone.utc),
            )

        # Aggregate purchases
        purchases = db.scalars(
            select(CustomerPurchaseHistory)
            .where(CustomerPurchaseHistory.customer_id.in_(customer_ids))
        ).all()
        total_purchases_count = len(purchases)
        total_purchases_amount = sum(
            (p.total_amount for p in purchases if p.status == "COMPLETED"),
            Decimal("0.00"),
        )
        aov = (
            (total_purchases_amount / Decimal(total_purchases_count)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if total_purchases_count > 0
            else Decimal("0.00")
        )

        # Aggregate deals
        deals = db.scalars(
            select(CustomerDealHistory)
            .where(CustomerDealHistory.customer_id.in_(customer_ids))
        ).all()
        total_deals_count = len(deals)
        total_deals_value = sum((d.deal_value for d in deals), Decimal("0.00"))

        # Aggregate payments
        payments = db.scalars(
            select(CustomerPaymentHistory)
            .where(CustomerPaymentHistory.customer_id.in_(customer_ids))
        ).all()
        total_payments_count = len(payments)
        total_payments_amount = sum(
            (p.amount for p in payments if p.status == "COMPLETED"),
            Decimal("0.00"),
        )

        # Aggregate discounts
        discounts = db.scalars(
            select(CustomerDiscountHistory)
            .where(CustomerDiscountHistory.customer_id.in_(customer_ids))
        ).all()
        total_discounts_count = len(discounts)
        total_discounts_amount = sum((d.discount_amount for d in discounts), Decimal("0.00"))
        avg_disc_pct = (
            (
                sum((d.discount_percentage for d in discounts), Decimal("0.00"))
                / Decimal(total_discounts_count)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if total_discounts_count > 0
            else Decimal("0.00")
        )

        # Average Customer LTV = Total realized purchases / Total customers
        avg_ltv = (total_purchases_amount / Decimal(total_customers)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Tier breakdown
        tiers = db.scalars(select(CustomerTier).where(CustomerTier.is_active == True)).all()
        tier_counts: Dict[Optional[uuid.UUID], int] = {}
        for c in customers:
            tier_counts[c.tier_id] = tier_counts.get(c.tier_id, 0) + 1

        tier_distribution: List[TierDistributionItem] = []
        for t in tiers:
            count = tier_counts.get(t.id, 0)
            pct = (
                (Decimal(count) / Decimal(total_customers) * Decimal("100.0")).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
                if total_customers > 0
                else Decimal("0.0")
            )
            tier_distribution.append(
                TierDistributionItem(
                    tier_id=t.id,
                    tier_name=t.name,
                    tier_code=t.code,
                    customer_count=count,
                    percentage_of_total=pct,
                )
            )

        # Include standard / untiered category
        standard_count = tier_counts.get(None, 0)
        standard_pct = (
            (Decimal(standard_count) / Decimal(total_customers) * Decimal("100.0")).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            )
            if total_customers > 0
            else Decimal("0.0")
        )
        tier_distribution.append(
            TierDistributionItem(
                tier_id=None,
                tier_name="Standard (No Tier)",
                tier_code="STANDARD",
                customer_count=standard_count,
                percentage_of_total=standard_pct,
            )
        )

        return CustomerAnalyticsSummary(
            total_customers=total_customers,
            active_customers=active_customers,
            inactive_customers=inactive_customers,
            tiered_customers=tiered_customers,
            standard_customers=standard_customers,
            total_purchases_count=total_purchases_count,
            total_purchases_amount=total_purchases_amount,
            total_deals_count=total_deals_count,
            total_deals_value=total_deals_value,
            total_payments_count=total_payments_count,
            total_payments_amount=total_payments_amount,
            total_discounts_count=total_discounts_count,
            total_discounts_amount=total_discounts_amount,
            average_customer_ltv=avg_ltv,
            average_order_value=aov,
            average_discount_percentage=avg_disc_pct,
            tier_distribution=tier_distribution,
            calculated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def get_segmentation(
        cls,
        db: Session,
        current_user: User,
    ) -> CustomerSegmentationSummary:
        """Phase 069: Customer Segmentation based on deterministic financial intelligence."""
        customers = db.scalars(cls._get_scoped_customer_query(current_user)).unique().all()
        total_evaluated = len(customers)

        customer_profiles: List[CustomerSegmentProfile] = []
        counts: Dict[CustomerSegmentType, int] = {s: 0 for s in CustomerSegmentType}

        for c in customers:
            ltv_res = CustomerFinancialIntelligenceService.calculate_ltv(db, c)
            sens_res = CustomerFinancialIntelligenceService.calculate_discount_sensitivity(db, c)
            risk_res = CustomerFinancialIntelligenceService.calculate_risk_profile(db, c)

            # Deterministic Classification Rules
            if not c.is_active or risk_res.risk_level == "HIGH" or risk_res.score >= 60:
                segment = CustomerSegmentType.AT_RISK
                label = "At-Risk Account"
                badge_variant = "destructive"
                rationale = "Elevated credit risk score, payment default history, or inactive account status."
            elif ltv_res.total_purchases_count >= 2 and ltv_res.ltv_amount >= Decimal("20000.00"):
                segment = CustomerSegmentType.CHAMPIONS
                label = "High-Value Champion"
                badge_variant = "success"
                rationale = "Strong transaction history with high cumulative Lifetime Value and dependable settlement."
            elif sens_res.level == "HIGH" or sens_res.score >= 60:
                segment = CustomerSegmentType.DISCOUNT_DEPENDENT
                label = "Discount Sensitive"
                badge_variant = "warning"
                rationale = "High discount sensitivity where deal conversions correlate directly with margin concessions."
            elif ltv_res.total_purchases_count >= 1 or c.tier_id is not None:
                segment = CustomerSegmentType.GROWTH_POTENTIAL
                label = "Growth Potential"
                badge_variant = "primary"
                rationale = "Active commercial engagement with established purchasing patterns and headroom for expansion."
            else:
                segment = CustomerSegmentType.UNCLASSIFIED
                label = "New / Unclassified"
                badge_variant = "outline"
                rationale = "Insufficient transaction records to evaluate lifetime velocity or behavioral sensitivity."

            counts[segment] += 1
            customer_profiles.append(
                CustomerSegmentProfile(
                    customer_id=c.id,
                    customer_code=c.customer_code,
                    customer_name=c.name,
                    segment=segment,
                    segment_label=label,
                    badge_variant=badge_variant,
                    rationale=rationale,
                    ltv_amount=ltv_res.ltv_amount,
                    risk_level=risk_res.risk_level,
                    discount_sensitivity_level=sens_res.level,
                    assigned_at=datetime.now(timezone.utc),
                )
            )

        # Distribution metadata
        descriptions = {
            CustomerSegmentType.CHAMPIONS: "High-value partners with significant cumulative spend and low risk.",
            CustomerSegmentType.GROWTH_POTENTIAL: "Developing accounts with steady purchase cadence and moderate margins.",
            CustomerSegmentType.DISCOUNT_DEPENDENT: "Accounts requiring discount concessions to convert orders.",
            CustomerSegmentType.AT_RISK: "Accounts with payment default signals, high risk, or deactivated status.",
            CustomerSegmentType.UNCLASSIFIED: "Recently added accounts with minimal recorded transaction history.",
        }
        labels = {
            CustomerSegmentType.CHAMPIONS: "Champions",
            CustomerSegmentType.GROWTH_POTENTIAL: "Growth Potential",
            CustomerSegmentType.DISCOUNT_DEPENDENT: "Discount Sensitive",
            CustomerSegmentType.AT_RISK: "At Risk",
            CustomerSegmentType.UNCLASSIFIED: "Unclassified",
        }

        distribution: List[SegmentDistributionItem] = []
        for seg in CustomerSegmentType:
            c_count = counts[seg]
            pct = (
                (Decimal(c_count) / Decimal(total_evaluated) * Decimal("100.0")).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
                if total_evaluated > 0
                else Decimal("0.0")
            )
            distribution.append(
                SegmentDistributionItem(
                    segment=seg,
                    label=labels[seg],
                    count=c_count,
                    percentage=pct,
                    description=descriptions[seg],
                )
            )

        return CustomerSegmentationSummary(
            total_evaluated=total_evaluated,
            distribution=distribution,
            customers=customer_profiles,
            calculated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def get_dashboard(
        cls,
        db: Session,
        current_user: User,
    ) -> CustomerDashboardResponse:
        """Phase 070: Consolidated Customer Dashboard view."""
        analytics = cls.get_analytics(db, current_user)
        segmentation = cls.get_segmentation(db, current_user)

        # High risk count from segmentation
        high_risk_count = sum(1 for c in segmentation.customers if c.risk_level == "HIGH")

        kpis = DashboardKpiSummary(
            total_customers=analytics.total_customers,
            active_customers=analytics.active_customers,
            portfolio_ltv=analytics.total_purchases_amount,
            high_risk_customers_count=high_risk_count,
            active_deals_count=analytics.total_deals_count,
            settled_revenue=analytics.total_payments_amount,
        )

        # Tier Chart Data (for DonutChart)
        tier_chart_data: List[ChartDataPointResponse] = [
            ChartDataPointResponse(
                label=t.tier_name,
                value=float(t.customer_count),
                color="#f59e0b" if "GOLD" in t.tier_code else "#64748b" if "SILVER" in t.tier_code else "#3b82f6",
            )
            for t in analytics.tier_distribution
            if t.customer_count > 0
        ]

        # Risk Distribution Data (for DonutChart)
        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for c in segmentation.customers:
            if c.risk_level in risk_counts:
                risk_counts[c.risk_level] += 1

        risk_colors = {"LOW": "#10b981", "MEDIUM": "#f59e0b", "HIGH": "#ef4444"}
        risk_chart_data: List[ChartDataPointResponse] = [
            ChartDataPointResponse(label=f"{lvl} Risk", value=float(cnt), color=risk_colors[lvl])
            for lvl, cnt in risk_counts.items()
            if cnt > 0
        ]

        # Segment Chart Data (for BarChart)
        segment_chart_data: List[ChartDataPointResponse] = [
            ChartDataPointResponse(
                label=s.label,
                value=float(s.count),
                color="#10b981" if s.segment == CustomerSegmentType.CHAMPIONS else "#ef4444" if s.segment == CustomerSegmentType.AT_RISK else "#3b82f6",
            )
            for s in segmentation.distribution
            if s.count > 0
        ]

        recent_activity = {
            "purchases": analytics.total_purchases_count,
            "deals": analytics.total_deals_count,
            "payments": analytics.total_payments_count,
            "discounts": analytics.total_discounts_count,
        }

        return CustomerDashboardResponse(
            kpis=kpis,
            tier_chart_data=tier_chart_data,
            risk_chart_data=risk_chart_data,
            segment_chart_data=segment_chart_data,
            recent_activity_summary=recent_activity,
            analytics=analytics,
            calculated_at=datetime.now(timezone.utc),
        )
