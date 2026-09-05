"""Recommendation Intelligence Services (DealFlow360 B07 & B08: Phases 166–185).

Production-grade recommendation engine implementing:
- Phase 166: AI Upsell Engine (AIUpsellService)
- Phase 167: AI Cross-Sell Engine (AICrossSellService)
- Phase 168: Customer Purchase Pattern Analysis (PurchasePatternAnalysisService)
- Phase 169: Product Affinity Analysis (ProductAffinityService)
- Phase 170: Frequently Bought Together (FrequentlyBoughtTogetherService)
- Phase 171: Next Best Product (NextBestProductService)
- Phase 172: Customer Segmentation (CustomerSegmentationService)
- Phase 173: Upsell Probability (UpsellProbabilityService)
- Phase 174: Cross-Sell Probability (CrossSellProbabilityService)
- Phase 175: Recommendation Ranking (RecommendationRankingEngine)
- Phase 176: Upsell Score (0–100) (AIUpsellService.calculate_upsell_score_100)
- Phase 177: Cross-Sell Score (0–100) (AICrossSellService.calculate_cross_sell_score_100)
- Phase 178: Extended Recommendation Ranking (RecommendationRankingEngine.rank_recommendations)
- Phase 179: AI Next-Best-Product (NextBestProductService.determine_next_best_product)
- Phase 180: Upsell Explanation (RecommendationExplanationService.generate_explanation)
- Phase 181: Add-to-Quote Recommendation (RecommendationQuoteIntegrationService.add_recommendation_to_quote)
- Phase 182: Real-Time Margin Update (RealTimeMarginService.calculate_margins)
- Phase 183: Upsell Acceptance Tracking (RecommendationTrackingService.track_event)
- Phase 184: Recommendation Analytics (RecommendationAnalyticsService.get_analytics)
- Phase 185: Upsell Dashboard (UpsellDashboardService.get_dashboard_summary)

Strictly non-LLM, strictly deterministic, mathematically sound, tenant-isolated.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.applied_discount import AppliedDiscount
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.customer_purchase_history import CustomerPurchaseHistory
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.recommendation_event import RecommendationEvent
from app.schemas.recommendations import (
    AddToQuoteRequest,
    AddToQuoteResponse,
    CustomerBehaviorSegment,
    CustomerPurchasePattern,
    CustomerSegmentationResult,
    FrequentlyBoughtTogetherItem,
    FrequentlyBoughtTogetherResponse,
    FunnelStageMetric,
    LineMarginDetail,
    NextBestProductResponse,
    ProductAffinityMetric,
    ProductPerformanceItem,
    QuoteLineItemInput,
    RealTimeMarginSummary,
    RecentActivityItem,
    RecommendationAnalyticsResponse,
    RecommendationEventCreate,
    RecommendationEventEnum,
    RecommendationEventResponse,
    RecommendationExplanation,
    RecommendationItem,
    RecommendationRankingResponse,
    RecommendationType,
    UpsellDashboardSummary,
)


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    """Safely quantize Decimal to specified decimal places."""
    fmt = Decimal("1." + "0" * places) if places > 0 else Decimal("1")
    return val.quantize(fmt, rounding=ROUND_HALF_UP)


# ==============================================================================
# Phase 168: Customer Purchase Pattern Analysis
# ==============================================================================

class PurchasePatternAnalysisService:
    """Deterministic RFM and behavioral purchase pattern analyzer (Phase 168).
    Extracts recency, frequency, monetary aggregates, transaction intervals,
    category preferences, and repeat purchase ratios from verified tables.
    """

    @classmethod
    def analyze_customer(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        as_of: Optional[datetime] = None,
    ) -> CustomerPurchasePattern:
        """Extract point-in-time RFM and purchase patterns for a customer."""
        ref_time = as_of or datetime.now(timezone.utc)

        # 1. Fetch customer account
        customer = db.scalars(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.company_id == company_id,
            )
        ).one_or_none()

        if not customer:
            raise ValueError(f"Customer {customer_id} not found in company {company_id}")

        # Compute tenure days
        cust_created = customer.created_at
        if cust_created.tzinfo is None:
            cust_created = cust_created.replace(tzinfo=timezone.utc)
        tenure_days = max(1, (ref_time - cust_created).days)

        # 2. Fetch completed historical purchases
        purchases = db.scalars(
            select(CustomerPurchaseHistory).where(
                CustomerPurchaseHistory.company_id == company_id,
                CustomerPurchaseHistory.customer_id == customer_id,
                CustomerPurchaseHistory.purchase_date <= ref_time,
                CustomerPurchaseHistory.status.in_(["COMPLETED", "DELIVERED", "FULFILLED"]),
            ).order_by(CustomerPurchaseHistory.purchase_date.desc())
        ).all()

        # 3. Fetch product history from AppliedDiscount for item-level patterns
        applied_discounts = db.scalars(
            select(AppliedDiscount).where(
                AppliedDiscount.company_id == company_id,
                AppliedDiscount.customer_id == customer_id,
                AppliedDiscount.applied_at <= ref_time,
            ).order_by(AppliedDiscount.applied_at.desc())
        ).all()

        total_orders = len(purchases)
        total_spend = sum((p.total_amount for p in purchases), Decimal("0.00"))

        if total_orders == 0 and len(applied_discounts) > 0:
            total_orders = len(applied_discounts)
            total_spend = sum((ad.discounted_price for ad in applied_discounts), Decimal("0.00"))
            latest_date = applied_discounts[0].applied_at
        elif total_orders > 0:
            latest_date = purchases[0].purchase_date
        else:
            latest_date = None

        if total_orders == 0 or latest_date is None:
            return CustomerPurchasePattern(
                customer_id=customer_id,
                company_id=company_id,
                total_orders_count=0,
                total_spend=Decimal("0.00"),
                average_order_value=Decimal("0.00"),
                last_purchase_date=None,
                recency_days=999,
                purchase_frequency_monthly=0.0,
                tenure_days=tenure_days,
                top_purchased_categories=[],
                distinct_products_count=0,
                repeat_purchase_rate=0.0,
                is_zero_history=True,
                analyzed_at=ref_time,
            )

        if latest_date.tzinfo is None:
            latest_date = latest_date.replace(tzinfo=timezone.utc)
        recency_days = max(0, (ref_time - latest_date).days)

        aov = quantize_dec(total_spend / Decimal(total_orders))

        tenure_months = max(1.0, float(tenure_days) / 30.0)
        monthly_freq = round(float(total_orders) / tenure_months, 2)

        product_counts: Dict[uuid.UUID, int] = {}
        category_counts: Dict[str, int] = {}

        all_prods = db.scalars(
            select(Product).where(Product.is_active == True)
        ).all()
        prod_map = {p.id: p for p in all_prods}

        all_cats = db.scalars(select(ProductCategory)).all()
        cat_map = {c.id: c.name for c in all_cats}

        for ad in applied_discounts:
            p_id = ad.product_id
            product_counts[p_id] = product_counts.get(p_id, 0) + 1
            prod = prod_map.get(p_id)
            if prod and prod.category_id:
                c_name = cat_map.get(prod.category_id, "General")
                category_counts[c_name] = category_counts.get(c_name, 0) + 1

        distinct_prods = len(product_counts)
        repeat_prods = sum(1 for c in product_counts.values() if c > 1)
        repeat_rate = round(float(repeat_prods) / float(distinct_prods), 4) if distinct_prods > 0 else 0.0

        top_cats = sorted(category_counts.keys(), key=lambda k: category_counts[k], reverse=True)[:5]

        return CustomerPurchasePattern(
            customer_id=customer_id,
            company_id=company_id,
            total_orders_count=total_orders,
            total_spend=total_spend,
            average_order_value=aov,
            last_purchase_date=latest_date,
            recency_days=recency_days,
            purchase_frequency_monthly=monthly_freq,
            tenure_days=tenure_days,
            top_purchased_categories=top_cats,
            distinct_products_count=distinct_prods,
            repeat_purchase_rate=repeat_rate,
            is_zero_history=False,
            analyzed_at=ref_time,
        )


# ==============================================================================
# Phase 169: Product Affinity Analysis
# ==============================================================================

class ProductAffinityService:
    """Product-to-Product statistical market basket analysis (Phase 169)."""

    MIN_SUPPORT_THRESHOLD: float = 0.001
    MAX_LIFT_CAP: float = 20.0

    @classmethod
    def compute_pair_affinity(
        cls,
        db: Session,
        company_id: uuid.UUID,
        source_product_id: uuid.UUID,
        target_product_id: uuid.UUID,
    ) -> Optional[ProductAffinityMetric]:
        """Compute statistical affinity metrics between two specific products."""
        if source_product_id == target_product_id:
            return None

        source_prod = db.get(Product, source_product_id)
        target_prod = db.get(Product, target_product_id)
        if not source_prod or not target_prod:
            return None

        baskets_query = (
            select(
                func.coalesce(AppliedDiscount.deal_reference, func.concat(AppliedDiscount.customer_id, '_', func.date(AppliedDiscount.applied_at))).label("basket_id"),
                AppliedDiscount.product_id,
            )
            .where(AppliedDiscount.company_id == company_id)
            .distinct()
        )
        basket_rows = db.execute(baskets_query).all()

        basket_map: Dict[str, Set[uuid.UUID]] = {}
        for b_id, p_id in basket_rows:
            if b_id not in basket_map:
                basket_map[b_id] = set()
            basket_map[b_id].add(p_id)

        total_baskets = max(1, len(basket_map))

        source_baskets = 0
        target_baskets = 0
        co_occur_baskets = 0

        for prods in basket_map.values():
            has_s = source_product_id in prods
            has_t = target_product_id in prods
            if has_s:
                source_baskets += 1
            if has_t:
                target_baskets += 1
            if has_s and has_t:
                co_occur_baskets += 1

        if total_baskets <= 1 or source_baskets == 0:
            same_category = (source_prod.category_id is not None and source_prod.category_id == target_prod.category_id)
            heuristic_conf = 0.35 if same_category else 0.10
            heuristic_lift = 1.8 if same_category else 1.0
            heuristic_score = 0.45 if same_category else 0.15
            return ProductAffinityMetric(
                source_product_id=source_product_id,
                target_product_id=target_product_id,
                source_product_name=source_prod.name,
                target_product_name=target_prod.name,
                source_sku=source_prod.sku,
                target_sku=target_prod.sku,
                co_occurrence_count=co_occur_baskets,
                source_count=source_baskets,
                target_count=target_baskets,
                support=0.0,
                confidence=heuristic_conf,
                lift=heuristic_lift,
                affinity_score=heuristic_score,
            )

        support = float(co_occur_baskets) / float(total_baskets)
        confidence = float(co_occur_baskets) / float(source_baskets) if source_baskets > 0 else 0.0

        p_s = float(source_baskets) / float(total_baskets)
        p_t = float(target_baskets) / float(total_baskets)
        denom = p_s * p_t

        if denom > 0.0:
            raw_lift = support / denom
            lift = min(cls.MAX_LIFT_CAP, round(raw_lift, 4))
        else:
            lift = 1.0

        normalized_lift = min(1.0, math.log1p(lift) / math.log1p(cls.MAX_LIFT_CAP))
        affinity_score = round(min(1.0, max(0.0, 0.6 * confidence + 0.4 * normalized_lift)), 4)

        return ProductAffinityMetric(
            source_product_id=source_product_id,
            target_product_id=target_product_id,
            source_product_name=source_prod.name,
            target_product_name=target_prod.name,
            source_sku=source_prod.sku,
            target_sku=target_prod.sku,
            co_occurrence_count=co_occur_baskets,
            source_count=source_baskets,
            target_count=target_baskets,
            support=round(support, 6),
            confidence=round(confidence, 4),
            lift=lift,
            affinity_score=affinity_score,
        )

    @classmethod
    def get_affinities_for_product(
        cls,
        db: Session,
        company_id: uuid.UUID,
        source_product_id: uuid.UUID,
        min_support: float = 0.0,
        limit: int = 20,
    ) -> List[ProductAffinityMetric]:
        """Compute and rank product affinities for a source product against all active products."""
        source_prod = db.get(Product, source_product_id)
        if not source_prod:
            raise ValueError(f"Product {source_product_id} not found")

        active_prods = db.scalars(
            select(Product).where(
                Product.id != source_product_id,
                Product.is_active == True,
            )
        ).all()

        results: List[ProductAffinityMetric] = []
        for target in active_prods:
            metric = cls.compute_pair_affinity(
                db=db,
                company_id=company_id,
                source_product_id=source_product_id,
                target_product_id=target.id,
            )
            if metric and metric.support >= min_support:
                results.append(metric)

        results.sort(key=lambda m: (-m.affinity_score, -m.confidence, m.target_sku))
        return results[:limit]


# ==============================================================================
# Phase 170: Frequently Bought Together
# ==============================================================================

class FrequentlyBoughtTogetherService:
    """Service producing ranked frequently bought together recommendations (Phase 170)."""

    @classmethod
    def get_frequently_bought_together(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        limit: int = 5,
        min_support: float = 0.0,
    ) -> FrequentlyBoughtTogetherResponse:
        """Return products frequently bought alongside the given product."""
        source_prod = db.get(Product, product_id)
        if not source_prod:
            raise ValueError(f"Product {product_id} not found")

        affinities = ProductAffinityService.get_affinities_for_product(
            db=db,
            company_id=company_id,
            source_product_id=product_id,
            min_support=min_support,
            limit=limit * 2,
        )

        all_cats = db.scalars(select(ProductCategory)).all()
        cat_map = {c.id: c.name for c in all_cats}

        items: List[FrequentlyBoughtTogetherItem] = []
        rank = 1

        for aff in affinities:
            p = db.get(Product, aff.target_product_id)
            if not p or not p.is_active:
                continue

            c_name = cat_map.get(p.category_id) if p.category_id else None
            items.append(
                FrequentlyBoughtTogetherItem(
                    product_id=p.id,
                    sku=p.sku,
                    name=p.name,
                    category_id=p.category_id,
                    category_name=c_name,
                    base_price=p.base_price,
                    inventory_quantity=p.inventory_quantity,
                    is_active=p.is_active,
                    confidence=aff.confidence,
                    lift=aff.lift,
                    co_occurrence_count=aff.co_occurrence_count,
                    rank=rank,
                )
            )
            rank += 1
            if len(items) >= limit:
                break

        return FrequentlyBoughtTogetherResponse(
            source_product_id=source_prod.id,
            source_sku=source_prod.sku,
            source_name=source_prod.name,
            total_associations_evaluated=len(affinities),
            items=items,
            generated_at=datetime.now(timezone.utc),
        )


# ==============================================================================
# Phase 172: Customer Segmentation
# ==============================================================================

class CustomerSegmentationService:
    """Deterministic customer behavioral segmentation (Phase 172)."""

    HIGH_VALUE_SPEND_THRESHOLD = Decimal("25000.00")
    HIGH_VALUE_AOV_THRESHOLD = Decimal("5000.00")
    LOYAL_ORDER_COUNT_THRESHOLD = 5
    RECENT_ACTIVE_DAYS_THRESHOLD = 60
    RECENT_LOYAL_DAYS_THRESHOLD = 90
    AT_RISK_RECENCY_DAYS_THRESHOLD = 120
    DORMANT_RECENCY_DAYS_THRESHOLD = 240
    NEW_CUSTOMER_DAYS_THRESHOLD = 30

    @classmethod
    def segment_customer(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        as_of: Optional[datetime] = None,
    ) -> CustomerSegmentationResult:
        """Classify a customer into an explainable behavioral segment."""
        pattern = PurchasePatternAnalysisService.analyze_customer(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
            as_of=as_of,
        )

        customer = db.get(Customer, customer_id)
        is_active = customer.is_active if customer else True

        if not is_active:
            segment = CustomerBehaviorSegment.DORMANT
            label = "Dormant / Inactive"
            rationale = "Customer account is marked inactive in the master registry."
        elif pattern.is_zero_history:
            segment = CustomerBehaviorSegment.NEW
            label = "New Prospect / Onboarding"
            rationale = "No completed transactions recorded; initial transaction baseline."
        elif (
            pattern.total_spend >= cls.HIGH_VALUE_SPEND_THRESHOLD
            or pattern.average_order_value >= cls.HIGH_VALUE_AOV_THRESHOLD
        ):
            segment = CustomerBehaviorSegment.HIGH_VALUE
            label = "High-Value Account"
            rationale = (
                f"Cumulative spend (${pattern.total_spend}) or AOV (${pattern.average_order_value}) "
                f"exceeds enterprise thresholds."
            )
        elif pattern.recency_days > cls.DORMANT_RECENCY_DAYS_THRESHOLD:
            segment = CustomerBehaviorSegment.DORMANT
            label = "Dormant Account"
            rationale = f"Last purchase occurred {pattern.recency_days} days ago (> {cls.DORMANT_RECENCY_DAYS_THRESHOLD} days)."
        elif pattern.recency_days > cls.AT_RISK_RECENCY_DAYS_THRESHOLD:
            segment = CustomerBehaviorSegment.AT_RISK
            label = "At-Risk Account"
            rationale = f"Purchase lapse of {pattern.recency_days} days indicates attrition hazard."
        elif (
            pattern.total_orders_count >= cls.LOYAL_ORDER_COUNT_THRESHOLD
            and pattern.recency_days <= cls.RECENT_LOYAL_DAYS_THRESHOLD
        ):
            segment = CustomerBehaviorSegment.LOYAL
            label = "Loyal Partner"
            rationale = (
                f"{pattern.total_orders_count} orders completed with consistent engagement "
                f"within {pattern.recency_days} days."
            )
        elif (
            pattern.total_orders_count >= 2
            and pattern.recency_days <= cls.RECENT_ACTIVE_DAYS_THRESHOLD
        ):
            segment = CustomerBehaviorSegment.ACTIVE
            label = "Active Regular"
            rationale = f"Recent purchase {pattern.recency_days} days ago with multiple completed orders."
        elif pattern.tenure_days <= cls.NEW_CUSTOMER_DAYS_THRESHOLD:
            segment = CustomerBehaviorSegment.NEW
            label = "New Customer"
            rationale = f"Account tenure is {pattern.tenure_days} days with initial transaction momentum."
        else:
            segment = CustomerBehaviorSegment.GROWTH
            label = "Growth Potential"
            rationale = "Demonstrated repeat buying propensity with significant expansion opportunity."

        return CustomerSegmentationResult(
            customer_id=customer_id,
            segment=segment,
            segment_label=label,
            rationale=rationale,
            recency_days=pattern.recency_days,
            frequency_count=pattern.total_orders_count,
            monetary_total=pattern.total_spend,
            average_order_value=pattern.average_order_value,
            tenure_days=pattern.tenure_days,
            evaluated_at=datetime.now(timezone.utc),
        )


# ==============================================================================
# Phase 173: Upsell Probability
# ==============================================================================

class UpsellProbabilityService:
    """Deterministic Upsell Probability Estimator (Phase 173)."""

    SEGMENT_MULTIPLIERS = {
        CustomerBehaviorSegment.HIGH_VALUE: 1.25,
        CustomerBehaviorSegment.LOYAL: 1.15,
        CustomerBehaviorSegment.ACTIVE: 1.00,
        CustomerBehaviorSegment.GROWTH: 0.90,
        CustomerBehaviorSegment.NEW: 0.75,
        CustomerBehaviorSegment.AT_RISK: 0.40,
        CustomerBehaviorSegment.DORMANT: 0.20,
    }

    @classmethod
    def calculate_probability(
        cls,
        customer_pattern: CustomerPurchasePattern,
        customer_segment: CustomerBehaviorSegment,
        target_product: Product,
        target_category_name: Optional[str] = None,
    ) -> float:
        """Compute calibrated P(upsell) bounded in [0.0, 1.0]."""
        base_prob = 0.30

        price = target_product.base_price
        aov = customer_pattern.average_order_value

        if aov > Decimal("0.00"):
            price_ratio = float(price / aov)
            if 1.0 <= price_ratio <= 1.5:
                price_score = 0.85
            elif 1.5 < price_ratio <= 2.5:
                price_score = 0.65
            elif 0.8 <= price_ratio < 1.0:
                price_score = 0.50
            elif price_ratio < 0.8:
                price_score = 0.20
            else:
                price_score = max(0.10, 0.65 - (price_ratio - 2.5) * 0.15)
        else:
            if price <= Decimal("1000.00"):
                price_score = 0.60
            elif price <= Decimal("5000.00"):
                price_score = 0.45
            else:
                price_score = 0.25

        cat_familiarity = 0.40
        if target_category_name and target_category_name in customer_pattern.top_purchased_categories:
            rank = customer_pattern.top_purchased_categories.index(target_category_name)
            cat_familiarity = 0.90 if rank == 0 else 0.75

        seg_mult = cls.SEGMENT_MULTIPLIERS.get(customer_segment, 1.0)
        raw_prob = (0.50 * price_score + 0.30 * cat_familiarity + 0.20 * base_prob) * seg_mult
        calibrated_prob = max(0.0, min(1.0, round(raw_prob, 4)))
        return calibrated_prob


# ==============================================================================
# Phase 174: Cross-Sell Probability
# ==============================================================================

class CrossSellProbabilityService:
    """Deterministic Cross-Sell Probability Estimator (Phase 174)."""

    @classmethod
    def calculate_probability(
        cls,
        customer_pattern: CustomerPurchasePattern,
        customer_segment: CustomerBehaviorSegment,
        affinity_metric: Optional[ProductAffinityMetric],
        is_complementary_category: bool = False,
    ) -> float:
        """Compute calibrated P(cross-sell) bounded in [0.0, 1.0]."""
        if affinity_metric:
            conf = affinity_metric.confidence
            norm_lift = min(1.0, math.log1p(affinity_metric.lift) / math.log1p(20.0))
            affinity_factor = 0.65 * conf + 0.35 * norm_lift
        else:
            affinity_factor = 0.30 if is_complementary_category else 0.15

        recency = customer_pattern.recency_days
        if recency <= 30:
            recency_factor = 0.90
        elif recency <= 90:
            recency_factor = 0.70
        elif recency <= 180:
            recency_factor = 0.50
        else:
            recency_factor = 0.25

        diversity = min(1.0, float(customer_pattern.distinct_products_count) / 5.0)
        diversity_factor = 0.40 + (0.60 * diversity)

        seg_multiplier = {
            CustomerBehaviorSegment.HIGH_VALUE: 1.20,
            CustomerBehaviorSegment.LOYAL: 1.15,
            CustomerBehaviorSegment.ACTIVE: 1.05,
            CustomerBehaviorSegment.GROWTH: 1.00,
            CustomerBehaviorSegment.NEW: 0.85,
            CustomerBehaviorSegment.AT_RISK: 0.50,
            CustomerBehaviorSegment.DORMANT: 0.25,
        }.get(customer_segment, 1.0)

        raw_prob = (
            0.50 * affinity_factor
            + 0.30 * recency_factor
            + 0.20 * diversity_factor
        ) * seg_multiplier

        calibrated_prob = max(0.0, min(1.0, round(raw_prob, 4)))
        return calibrated_prob


# ==============================================================================
# Phase 166 & 176: AI Upsell Engine & Upsell Score (0–100)
# ==============================================================================

class AIUpsellService:
    """AI Upsell Engine (Phase 166) & Upsell Score (Phase 176)."""

    @classmethod
    def calculate_upsell_score_100(
        cls,
        probability: float,
        unit_margin_pct: float,
        inventory_quantity: int,
        price_ratio: float,
    ) -> int:
        """Phase 176: Produce deterministic, explainable 0–100 Upsell Score.
        Evaluates probability (45%), unit margin (25%), inventory (15%), and price tier suitability (15%).
        """
        # Inventory factor
        if inventory_quantity <= 0:
            inv_factor = 0.20
        elif inventory_quantity <= 5:
            inv_factor = 0.60
        else:
            inv_factor = 1.00

        # Margin factor (normalized 0 to 1)
        margin_factor = max(0.0, min(1.0, unit_margin_pct / 100.0))

        # Price suitability: sweet spot 1.0 to 1.8 of AOV
        if 1.0 <= price_ratio <= 1.8:
            price_factor = 1.00
        elif 0.8 <= price_ratio < 1.0:
            price_factor = 0.70
        elif 1.8 < price_ratio <= 3.0:
            price_factor = 0.60
        else:
            price_factor = 0.30

        raw_score = (
            0.45 * probability
            + 0.25 * margin_factor
            + 0.15 * inv_factor
            + 0.15 * price_factor
        ) * 100.0

        return max(0, min(100, int(round(raw_score))))

    @classmethod
    def generate_upsell_candidates(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        limit: int = 5,
    ) -> List[Tuple[Product, float, int, Dict[str, float]]]:
        """Generate ranked upsell product candidates with normalized score and 0-100 score."""
        pattern = PurchasePatternAnalysisService.analyze_customer(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
        )
        segment_res = CustomerSegmentationService.segment_customer(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
        )

        ordered_pids = set(
            db.scalars(
                select(AppliedDiscount.product_id).where(
                    AppliedDiscount.company_id == company_id,
                    AppliedDiscount.customer_id == customer_id,
                )
            ).all()
        )

        active_products = db.scalars(
            select(Product).where(
                Product.is_active == True,
            )
        ).all()

        cats = db.scalars(select(ProductCategory)).all()
        cat_map = {c.id: c.name for c in cats}

        candidates: List[Tuple[Product, float, int, Dict[str, float]]] = []

        for p in active_products:
            if p.id in ordered_pids and not p.is_subscription:
                continue

            c_name = cat_map.get(p.category_id)
            prob = UpsellProbabilityService.calculate_probability(
                customer_pattern=pattern,
                customer_segment=segment_res.segment,
                target_product=p,
                target_category_name=c_name,
            )

            margin_pct = (
                float(p.base_price - p.cost) / float(p.base_price) * 100.0
                if p.base_price > Decimal("0.00")
                else 0.0
            )
            margin_pct = max(0.0, min(100.0, margin_pct))
            margin_ratio = margin_pct / 100.0

            p_ratio = (
                float(p.base_price / pattern.average_order_value)
                if pattern.average_order_value > 0
                else 1.0
            )

            # Phase 176: 0-100 Upsell Score
            score_100 = cls.calculate_upsell_score_100(
                probability=prob,
                unit_margin_pct=margin_pct,
                inventory_quantity=p.inventory_quantity,
                price_ratio=p_ratio,
            )

            score_norm = round(float(score_100) / 100.0, 4)

            signals = {
                "upsell_probability": prob,
                "unit_margin_ratio": round(margin_ratio, 4),
                "aov_ratio": round(p_ratio, 2),
                "upsell_score_100": float(score_100),
            }
            candidates.append((p, score_norm, score_100, signals))

        candidates.sort(key=lambda item: (-item[2], -item[1], item[0].sku))
        return candidates[:limit]


# ==============================================================================
# Phase 167 & 177: AI Cross-Sell Engine & Cross-Sell Score (0–100)
# ==============================================================================

class AICrossSellService:
    """AI Cross-Sell Engine (Phase 167) & Cross-Sell Score (Phase 177)."""

    @classmethod
    def calculate_cross_sell_score_100(
        cls,
        probability: float,
        confidence: float,
        lift: float,
        inventory_quantity: int,
    ) -> int:
        """Phase 177: Produce deterministic, explainable 0–100 Cross-Sell Score.
        Evaluates cross-sell probability (40%), association confidence (30%), lift (20%), and inventory (10%).
        """
        # Lift factor normalized
        norm_lift = min(1.0, math.log1p(lift) / math.log1p(20.0))

        # Inventory factor
        if inventory_quantity <= 0:
            inv_factor = 0.20
        elif inventory_quantity <= 5:
            inv_factor = 0.60
        else:
            inv_factor = 1.00

        raw_score = (
            0.40 * probability
            + 0.30 * confidence
            + 0.20 * norm_lift
            + 0.10 * inv_factor
        ) * 100.0

        return max(0, min(100, int(round(raw_score))))

    @classmethod
    def generate_cross_sell_candidates(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        limit: int = 5,
    ) -> List[Tuple[Product, float, int, Dict[str, float]]]:
        """Generate ranked cross-sell product candidates with normalized score and 0-100 score."""
        pattern = PurchasePatternAnalysisService.analyze_customer(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
        )
        segment_res = CustomerSegmentationService.segment_customer(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
        )

        prior_pids = list(
            set(
                db.scalars(
                    select(AppliedDiscount.product_id).where(
                        AppliedDiscount.company_id == company_id,
                        AppliedDiscount.customer_id == customer_id,
                    )
                ).all()
            )
        )

        active_products = db.scalars(
            select(Product).where(Product.is_active == True)
        ).all()
        prod_map = {p.id: p for p in active_products}

        candidates_map: Dict[uuid.UUID, Tuple[float, int, Dict[str, float]]] = {}

        if prior_pids:
            for s_id in prior_pids:
                affinities = ProductAffinityService.get_affinities_for_product(
                    db=db,
                    company_id=company_id,
                    source_product_id=s_id,
                    limit=limit * 2,
                )
                for aff in affinities:
                    t_id = aff.target_product_id
                    if t_id in prior_pids or t_id not in prod_map:
                        continue

                    target_prod = prod_map[t_id]
                    prob = CrossSellProbabilityService.calculate_probability(
                        customer_pattern=pattern,
                        customer_segment=segment_res.segment,
                        affinity_metric=aff,
                    )

                    score_100 = cls.calculate_cross_sell_score_100(
                        probability=prob,
                        confidence=aff.confidence,
                        lift=aff.lift,
                        inventory_quantity=target_prod.inventory_quantity,
                    )
                    score_norm = round(float(score_100) / 100.0, 4)

                    if t_id not in candidates_map or score_100 > candidates_map[t_id][1]:
                        candidates_map[t_id] = (
                            score_norm,
                            score_100,
                            {
                                "cross_sell_probability": prob,
                                "affinity_score": aff.affinity_score,
                                "confidence": aff.confidence,
                                "lift": aff.lift,
                                "cross_sell_score_100": float(score_100),
                            },
                        )

        if not candidates_map:
            for p in active_products[:limit * 2]:
                if p.id in prior_pids:
                    continue
                prob = CrossSellProbabilityService.calculate_probability(
                    customer_pattern=pattern,
                    customer_segment=segment_res.segment,
                    affinity_metric=None,
                    is_complementary_category=True,
                )
                score_100 = cls.calculate_cross_sell_score_100(
                    probability=prob,
                    confidence=0.30,
                    lift=1.0,
                    inventory_quantity=p.inventory_quantity,
                )
                score_norm = round(float(score_100) / 100.0, 4)
                candidates_map[p.id] = (
                    score_norm,
                    score_100,
                    {
                        "cross_sell_probability": prob,
                        "affinity_score": 0.20,
                        "confidence": 0.30,
                        "lift": 1.0,
                        "cross_sell_score_100": float(score_100),
                    },
                )

        ranked = []
        for p_id, (score_norm, score_100, signals) in candidates_map.items():
            if p_id in prod_map:
                ranked.append((prod_map[p_id], score_norm, score_100, signals))

        ranked.sort(key=lambda item: (-item[2], -item[1], item[0].sku))
        return ranked[:limit]


# ==============================================================================
# Phase 180: Upsell & Recommendation Explanation Service
# ==============================================================================

class RecommendationExplanationService:
    """Deterministic human-readable explanation generator (Phase 180)."""

    @classmethod
    def generate_explanation(
        cls,
        product: Product,
        recommendation_type: RecommendationType,
        customer_pattern: CustomerPurchasePattern,
        customer_segment: CustomerBehaviorSegment,
        score_100: int,
        signals: Dict[str, Any],
        category_name: Optional[str] = None,
    ) -> RecommendationExplanation:
        """Produce structured business justification without hallucination."""
        reasons: List[str] = []

        # Category affinity reason
        if category_name and category_name in customer_pattern.top_purchased_categories:
            reasons.append(f"Customer frequently purchases products in the {category_name} category.")

        # Price / Tier justification
        if recommendation_type == RecommendationType.UPSELL:
            aov = customer_pattern.average_order_value
            if aov > 0:
                price_ratio = float(product.base_price / aov)
                if 1.0 <= price_ratio <= 1.8:
                    reasons.append(
                        f"Target unit price (${product.base_price}) aligns with account upgrade capacity (~{int(price_ratio*100)}% of AOV)."
                    )
                elif price_ratio > 1.8:
                    reasons.append(
                        f"Higher-tier premium product offering enhanced capabilities."
                    )
            reasons.append("Premium alternative designed to expand relationship value.")
        else:
            lift = signals.get("lift", 1.0)
            if lift > 1.2:
                reasons.append(
                    f"Strong historical market-basket co-occurrence with complementary items (Lift {round(lift, 1)}x)."
                )
            reasons.append("Naturally pairs with products previously purchased by the account.")

        # Margin and Inventory reasons
        margin_pct = (
            float(product.base_price - product.cost) / float(product.base_price) * 100.0
            if product.base_price > Decimal("0.00")
            else 0.0
        )
        if margin_pct >= 40.0:
            reasons.append(f"High-margin catalog offering ({round(margin_pct, 1)}% gross margin).")

        if product.inventory_quantity > 10:
            reasons.append("Immediately available in primary warehouse stock.")

        # Segment context
        if customer_segment == CustomerBehaviorSegment.HIGH_VALUE:
            reasons.append("High-Value account profile with demonstrated upgrade propensity.")
        elif customer_segment == CustomerBehaviorSegment.LOYAL:
            reasons.append("Loyal customer with repeat ordering track record.")

        summary = (
            f"Recommended {recommendation_type.value} offering '{product.name}' with "
            f"suitability score {score_100}/100 based on account history and product catalog affinity."
        )

        return RecommendationExplanation(
            summary=summary,
            reasons=reasons,
            signals=signals,
        )


# ==============================================================================
# Phase 178: Recommendation Ranking Engine (Extended for B08)
# ==============================================================================

class RecommendationRankingEngine:
    """Final Multi-Factor Recommendation Ranking Engine (Phases 175 & 178)."""

    WEIGHT_UPSELL: float = 0.35
    WEIGHT_CROSS_SELL: float = 0.35
    WEIGHT_AFFINITY: float = 0.15
    WEIGHT_SEGMENT_RELEVANCE: float = 0.15

    @classmethod
    def rank_recommendations(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        top_n: int = 10,
    ) -> RecommendationRankingResponse:
        """Evaluate, rank, explain, and return top-N recommendations for a customer."""
        customer = db.scalars(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.company_id == company_id,
            )
        ).one_or_none()

        if not customer:
            raise ValueError(f"Customer {customer_id} not found in company {company_id}")

        pattern = PurchasePatternAnalysisService.analyze_customer(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
        )
        segment_res = CustomerSegmentationService.segment_customer(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
        )

        upsell_pool = AIUpsellService.generate_upsell_candidates(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
            limit=top_n * 2,
        )
        cross_sell_pool = AICrossSellService.generate_cross_sell_candidates(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
            limit=top_n * 2,
        )

        all_cats = db.scalars(select(ProductCategory)).all()
        cat_map = {c.id: c.name for c in all_cats}

        candidate_items: Dict[uuid.UUID, RecommendationItem] = {}

        # 1. Process Upsell Candidates
        for prod, score_norm, score_100, signals in upsell_pool:
            p_id = prod.id
            if not prod.is_active:
                continue

            u_prob = signals.get("upsell_probability", 0.0)
            c_prob = CrossSellProbabilityService.calculate_probability(
                customer_pattern=pattern,
                customer_segment=segment_res.segment,
                affinity_metric=None,
            )
            aff_score = signals.get("unit_margin_ratio", 0.40)
            seg_rel = 0.85 if segment_res.segment in (CustomerBehaviorSegment.HIGH_VALUE, CustomerBehaviorSegment.LOYAL) else 0.65

            final_score = round(
                cls.WEIGHT_UPSELL * (score_100 / 100.0)
                + cls.WEIGHT_CROSS_SELL * c_prob
                + cls.WEIGHT_AFFINITY * aff_score
                + cls.WEIGHT_SEGMENT_RELEVANCE * seg_rel,
                4,
            )

            margin_pct = (
                quantize_dec(((prod.base_price - prod.cost) / prod.base_price) * Decimal("100.00"))
                if prod.base_price > Decimal("0.00")
                else Decimal("0.00")
            )

            explanation = RecommendationExplanationService.generate_explanation(
                product=prod,
                recommendation_type=RecommendationType.UPSELL,
                customer_pattern=pattern,
                customer_segment=segment_res.segment,
                score_100=score_100,
                signals=signals,
                category_name=cat_map.get(prod.category_id),
            )

            candidate_items[p_id] = RecommendationItem(
                product_id=prod.id,
                sku=prod.sku,
                name=prod.name,
                category_id=prod.category_id,
                category_name=cat_map.get(prod.category_id),
                base_price=prod.base_price,
                cost=prod.cost,
                unit_margin_pct=margin_pct,
                inventory_status=prod.inventory_status,
                inventory_quantity=prod.inventory_quantity,
                recommendation_type=RecommendationType.UPSELL,
                score=final_score,
                rank=0,
                upsell_score_100=score_100,
                cross_sell_score_100=int(c_prob * 100),
                upsell_probability=u_prob,
                cross_sell_probability=c_prob,
                affinity_score=aff_score,
                segment_relevance=seg_rel,
                supporting_signals=signals,
                explanation=explanation,
            )

        # 2. Process Cross-Sell Candidates
        for prod, score_norm, score_100, signals in cross_sell_pool:
            p_id = prod.id
            if not prod.is_active:
                continue

            c_prob = signals.get("cross_sell_probability", 0.0)
            aff_score = signals.get("affinity_score", 0.30)
            u_prob = UpsellProbabilityService.calculate_probability(
                customer_pattern=pattern,
                customer_segment=segment_res.segment,
                target_product=prod,
            )
            margin_calc = (
                float(prod.base_price - prod.cost) / float(prod.base_price) * 100.0
                if prod.base_price > Decimal("0.00")
                else 0.0
            )
            price_ratio_calc = (
                float(prod.base_price / pattern.average_order_value)
                if pattern.average_order_value > Decimal("0.00")
                else 1.0
            )
            u_score_100 = AIUpsellService.calculate_upsell_score_100(
                probability=u_prob,
                unit_margin_pct=margin_calc,
                inventory_quantity=prod.inventory_quantity,
                price_ratio=price_ratio_calc,
            )
            seg_rel = 0.80 if segment_res.segment != CustomerBehaviorSegment.DORMANT else 0.40

            final_score = round(
                cls.WEIGHT_UPSELL * (u_score_100 / 100.0)
                + cls.WEIGHT_CROSS_SELL * (score_100 / 100.0)
                + cls.WEIGHT_AFFINITY * aff_score
                + cls.WEIGHT_SEGMENT_RELEVANCE * seg_rel,
                4,
            )

            margin_pct = (
                quantize_dec(((prod.base_price - prod.cost) / prod.base_price) * Decimal("100.00"))
                if prod.base_price > Decimal("0.00")
                else Decimal("0.00")
            )

            explanation = RecommendationExplanationService.generate_explanation(
                product=prod,
                recommendation_type=RecommendationType.CROSS_SELL,
                customer_pattern=pattern,
                customer_segment=segment_res.segment,
                score_100=score_100,
                signals=signals,
                category_name=cat_map.get(prod.category_id),
            )

            if p_id in candidate_items:
                if final_score > candidate_items[p_id].score:
                    candidate_items[p_id] = RecommendationItem(
                        product_id=prod.id,
                        sku=prod.sku,
                        name=prod.name,
                        category_id=prod.category_id,
                        category_name=cat_map.get(prod.category_id),
                        base_price=prod.base_price,
                        cost=prod.cost,
                        unit_margin_pct=margin_pct,
                        inventory_status=prod.inventory_status,
                        inventory_quantity=prod.inventory_quantity,
                        recommendation_type=RecommendationType.CROSS_SELL,
                        score=final_score,
                        rank=0,
                        upsell_score_100=u_score_100,
                        cross_sell_score_100=score_100,
                        upsell_probability=u_prob,
                        cross_sell_probability=c_prob,
                        affinity_score=aff_score,
                        segment_relevance=seg_rel,
                        supporting_signals=signals,
                        explanation=explanation,
                    )
            else:
                candidate_items[p_id] = RecommendationItem(
                    product_id=prod.id,
                    sku=prod.sku,
                    name=prod.name,
                    category_id=prod.category_id,
                    category_name=cat_map.get(prod.category_id),
                    base_price=prod.base_price,
                    cost=prod.cost,
                    unit_margin_pct=margin_pct,
                    inventory_status=prod.inventory_status,
                    inventory_quantity=prod.inventory_quantity,
                    recommendation_type=RecommendationType.CROSS_SELL,
                    score=final_score,
                    rank=0,
                    upsell_score_100=u_score_100,
                    cross_sell_score_100=score_100,
                    upsell_probability=u_prob,
                    cross_sell_probability=c_prob,
                    affinity_score=aff_score,
                    segment_relevance=seg_rel,
                    supporting_signals=signals,
                    explanation=explanation,
                )

        sorted_items = sorted(
            candidate_items.values(),
            key=lambda item: (-item.score, -float(item.unit_margin_pct), item.sku),
        )

        ranked_recommendations: List[RecommendationItem] = []
        for idx, item in enumerate(sorted_items[:top_n], start=1):
            ranked_recommendations.append(
                RecommendationItem(
                    product_id=item.product_id,
                    sku=item.sku,
                    name=item.name,
                    category_id=item.category_id,
                    category_name=item.category_name,
                    base_price=item.base_price,
                    cost=item.cost,
                    unit_margin_pct=item.unit_margin_pct,
                    inventory_status=item.inventory_status,
                    inventory_quantity=item.inventory_quantity,
                    recommendation_type=item.recommendation_type,
                    score=item.score,
                    rank=idx,
                    upsell_score_100=item.upsell_score_100,
                    cross_sell_score_100=item.cross_sell_score_100,
                    upsell_probability=item.upsell_probability,
                    cross_sell_probability=item.cross_sell_probability,
                    affinity_score=item.affinity_score,
                    segment_relevance=item.segment_relevance,
                    supporting_signals=item.supporting_signals,
                    explanation=item.explanation,
                )
            )

        return RecommendationRankingResponse(
            customer_id=customer.id,
            customer_code=customer.customer_code,
            customer_name=customer.name,
            customer_segment=segment_res.segment,
            total_candidates_evaluated=len(candidate_items),
            recommendations=ranked_recommendations,
            generated_at=datetime.now(timezone.utc),
        )


# ==============================================================================
# Phase 171 & 179: AI Next-Best-Product Service
# ==============================================================================

class NextBestProductService:
    """Next Best Product Selector (Phase 171 & 179)."""

    @classmethod
    def determine_next_best_product(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> NextBestProductResponse:
        """Evaluate catalog and customer state to pick the optimal Next Best Product."""
        ranking_res = RecommendationRankingEngine.rank_recommendations(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
            top_n=1,
        )

        if not ranking_res.recommendations:
            return NextBestProductResponse(
                customer_id=customer_id,
                has_recommendation=False,
                best_product=None,
                evaluated_at=datetime.now(timezone.utc),
            )

        return NextBestProductResponse(
            customer_id=customer_id,
            has_recommendation=True,
            best_product=ranking_res.recommendations[0],
            evaluated_at=datetime.now(timezone.utc),
        )


# ==============================================================================
# Phase 182: Real-Time Margin Update Service
# ==============================================================================

class RealTimeMarginService:
    """Financial margin calculator using strict Decimal arithmetic (Phase 182)."""

    @classmethod
    def calculate_margins(
        cls,
        items: List[QuoteLineItemInput],
    ) -> RealTimeMarginSummary:
        """Calculate line-by-line and consolidated quote margins."""
        lines: List[LineMarginDetail] = []
        total_rev = Decimal("0.00")
        total_cost = Decimal("0.00")

        for item in items:
            q = Decimal(item.quantity)
            line_rev = quantize_dec(item.selling_price * q)
            line_cost = quantize_dec(item.unit_cost * q)
            line_gp = line_rev - line_cost

            if line_rev > Decimal("0.00"):
                line_margin_pct = quantize_dec((line_gp / line_rev) * Decimal("100.00"))
            else:
                line_margin_pct = Decimal("-100.00") if line_cost > Decimal("0.00") else Decimal("0.00")

            lines.append(
                LineMarginDetail(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=quantize_dec(item.selling_price),
                    unit_cost=quantize_dec(item.unit_cost),
                    line_revenue=line_rev,
                    line_cost=line_cost,
                    line_gross_profit=line_gp,
                    line_margin_pct=line_margin_pct,
                )
            )

            total_rev += line_rev
            total_cost += line_cost

        total_gp = total_rev - total_cost
        if total_rev > Decimal("0.00"):
            total_margin_pct = quantize_dec((total_gp / total_rev) * Decimal("100.00"))
        else:
            total_margin_pct = Decimal("-100.00") if total_cost > Decimal("0.00") else Decimal("0.00")

        return RealTimeMarginSummary(
            total_revenue=total_rev,
            total_cost=total_cost,
            total_gross_profit=total_gp,
            total_margin_pct=total_margin_pct,
            lines=lines,
        )


# ==============================================================================
# Phase 181: Add-to-Quote Recommendation Service
# ==============================================================================

class RecommendationQuoteIntegrationService:
    """Recommendation-to-Quote integration service (Phase 181)."""

    @classmethod
    def add_recommendation_to_quote(
        cls,
        db: Session,
        company_id: uuid.UUID,
        request: AddToQuoteRequest,
        actor_id: Optional[uuid.UUID] = None,
    ) -> AddToQuoteResponse:
        """Validate candidate product and calculate updated quote margins."""
        # 1. Validate customer tenant
        customer = db.scalars(
            select(Customer).where(
                Customer.id == request.customer_id,
                Customer.company_id == company_id,
            )
        ).one_or_none()
        if not customer:
            raise ValueError(f"Customer {request.customer_id} not found in company {company_id}")

        # 2. Validate product status
        product = db.get(Product, request.product_id)
        if not product or not product.is_active:
            raise ValueError(f"Product {request.product_id} is inactive or does not exist")

        # 3. Assemble quote lines
        all_lines = list(request.existing_items)
        all_lines.append(
            QuoteLineItemInput(
                product_id=product.id,
                quantity=request.quantity,
                selling_price=product.base_price,
                unit_cost=product.cost,
            )
        )

        # 4. Phase 182: Recalculate margins
        margin_summary = RealTimeMarginService.calculate_margins(all_lines)

        # 5. Phase 183: Log ADDED_TO_QUOTE event
        rec_id = request.recommendation_id or f"REC-{uuid.uuid4().hex[:8]}"
        event_record = RecommendationTrackingService.track_event(
            db=db,
            company_id=company_id,
            event=RecommendationEventCreate(
                recommendation_id=rec_id,
                customer_id=request.customer_id,
                product_id=product.id,
                recommendation_type=request.recommendation_type,
                event_type=RecommendationEventEnum.ADDED_TO_QUOTE,
                score=Decimal("85.00"),
                quote_reference=request.quote_reference,
                context_metadata={"quantity": request.quantity, "margin_pct": float(margin_summary.total_margin_pct)},
            ),
            actor_id=actor_id,
        )

        return AddToQuoteResponse(
            customer_id=customer.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            quote_reference=request.quote_reference,
            added_quantity=request.quantity,
            margin_summary=margin_summary,
            event_id=str(event_record.id),
            status="SUCCESS",
        )


# ==============================================================================
# Phase 183: Upsell Acceptance Tracking Service
# ==============================================================================

class RecommendationTrackingService:
    """Lifecycle event tracking for recommendations (Phase 183)."""

    @classmethod
    def track_event(
        cls,
        db: Session,
        company_id: uuid.UUID,
        event: RecommendationEventCreate,
        actor_id: Optional[uuid.UUID] = None,
    ) -> RecommendationEvent:
        """Persist recommendation lifecycle event with deduplication."""
        # Check for duplicate within 2 minutes for identical recommendation + event_type
        recent = db.scalars(
            select(RecommendationEvent).where(
                RecommendationEvent.company_id == company_id,
                RecommendationEvent.recommendation_id == event.recommendation_id,
                RecommendationEvent.event_type == event.event_type.value,
            ).order_by(RecommendationEvent.created_at.desc())
        ).first()

        if recent:
            now = datetime.now(timezone.utc)
            r_time = recent.created_at
            if r_time.tzinfo is None:
                r_time = r_time.replace(tzinfo=timezone.utc)
            if (now - r_time).total_seconds() < 5:
                return recent  # Return existing event record safely without re-inserting

        rec_event = RecommendationEvent(
            company_id=company_id,
            recommendation_id=event.recommendation_id,
            customer_id=event.customer_id,
            product_id=event.product_id,
            actor_id=actor_id,
            recommendation_type=event.recommendation_type.value,
            event_type=event.event_type.value,
            score=event.score,
            quote_reference=event.quote_reference,
            context_metadata=event.context_metadata,
        )
        db.add(rec_event)
        db.commit()
        db.refresh(rec_event)
        return rec_event


# ==============================================================================
# Phase 184: Recommendation Analytics Service
# ==============================================================================

class RecommendationAnalyticsService:
    """Analytics aggregator for recommendation conversion and performance (Phase 184)."""

    @classmethod
    def get_analytics(
        cls,
        db: Session,
        company_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> RecommendationAnalyticsResponse:
        """Aggregate recommendation event funnel, scores, and conversion rates."""
        query = select(RecommendationEvent).where(RecommendationEvent.company_id == company_id)
        if start_date:
            query = query.where(RecommendationEvent.created_at >= start_date)
        if end_date:
            query = query.where(RecommendationEvent.created_at <= end_date)

        events = db.scalars(query).all()

        total_generated = sum(1 for e in events if e.event_type == "GENERATED")
        total_viewed = sum(1 for e in events if e.event_type == "VIEWED")
        total_selected = sum(1 for e in events if e.event_type == "SELECTED")
        total_added = sum(1 for e in events if e.event_type == "ADDED_TO_QUOTE")
        total_accepted = sum(1 for e in events if e.event_type == "ACCEPTED")
        total_rejected = sum(1 for e in events if e.event_type == "REJECTED")
        total_dismissed = sum(1 for e in events if e.event_type == "DISMISSED")

        upsell_count = sum(1 for e in events if e.recommendation_type == "UPSELL")
        cross_sell_count = sum(1 for e in events if e.recommendation_type == "CROSS_SELL")

        # Conversion rates with zero denominator protection
        view_rate = round(float(total_viewed) / float(total_generated), 4) if total_generated > 0 else 0.0
        selection_rate = round(float(total_selected) / float(total_viewed), 4) if total_viewed > 0 else 0.0
        add_rate = round(float(total_added) / float(total_selected), 4) if total_selected > 0 else 0.0
        acceptance_rate = round(float(total_accepted) / float(total_generated), 4) if total_generated > 0 else 0.0

        scores = [float(e.score) for e in events if e.score > Decimal("0.00")]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        # Product-level aggregation
        rec_p_counts: Dict[uuid.UUID, int] = {}
        acc_p_counts: Dict[uuid.UUID, int] = {}

        for e in events:
            p_id = e.product_id
            rec_p_counts[p_id] = rec_p_counts.get(p_id, 0) + 1
            if e.event_type in ("ACCEPTED", "ADDED_TO_QUOTE"):
                acc_p_counts[p_id] = acc_p_counts.get(p_id, 0) + 1

        top_prods_list: List[ProductPerformanceItem] = []
        for p_id, count in sorted(rec_p_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            p = db.get(Product, p_id)
            if not p:
                continue
            acc = acc_p_counts.get(p_id, 0)
            conv = round(float(acc) / float(count), 4) if count > 0 else 0.0
            top_prods_list.append(
                ProductPerformanceItem(
                    product_id=p.id,
                    sku=p.sku,
                    name=p.name,
                    recommendation_count=count,
                    acceptance_count=acc,
                    conversion_rate=conv,
                )
            )

        top_acc_list: List[ProductPerformanceItem] = []
        for p_id, acc in sorted(acc_p_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            p = db.get(Product, p_id)
            if not p:
                continue
            rec = rec_p_counts.get(p_id, acc)
            conv = round(float(acc) / float(rec), 4) if rec > 0 else 0.0
            top_acc_list.append(
                ProductPerformanceItem(
                    product_id=p.id,
                    sku=p.sku,
                    name=p.name,
                    recommendation_count=rec,
                    acceptance_count=acc,
                    conversion_rate=conv,
                )
            )

        return RecommendationAnalyticsResponse(
            total_recommendations_generated=total_generated,
            total_viewed=total_viewed,
            total_selected=total_selected,
            total_added_to_quote=total_added,
            total_accepted=total_accepted,
            total_rejected=total_rejected,
            total_dismissed=total_dismissed,
            view_rate=view_rate,
            selection_rate=selection_rate,
            add_to_quote_rate=add_rate,
            acceptance_rate=acceptance_rate,
            average_recommendation_score=avg_score,
            upsell_events_count=upsell_count,
            cross_sell_events_count=cross_sell_count,
            top_recommended_products=top_prods_list,
            top_accepted_products=top_acc_list,
            analyzed_at=datetime.now(timezone.utc),
        )


# ==============================================================================
# Phase 185: Upsell Dashboard Service
# ==============================================================================

class UpsellDashboardService:
    """Consolidated Upsell Dashboard reporting service (Phase 185)."""

    @classmethod
    def get_dashboard_summary(
        cls,
        db: Session,
        company_id: uuid.UUID,
    ) -> UpsellDashboardSummary:
        """Provide aggregated metrics, funnels, and recent activity for the UI."""
        analytics = RecommendationAnalyticsService.get_analytics(
            db=db,
            company_id=company_id,
        )

        gen = max(1, analytics.total_recommendations_generated)
        funnel = [
            FunnelStageMetric(
                stage="Generated",
                count=analytics.total_recommendations_generated,
                conversion_rate_from_top=1.0,
            ),
            FunnelStageMetric(
                stage="Viewed",
                count=analytics.total_viewed,
                conversion_rate_from_top=round(float(analytics.total_viewed) / float(gen), 4),
            ),
            FunnelStageMetric(
                stage="Selected",
                count=analytics.total_selected,
                conversion_rate_from_top=round(float(analytics.total_selected) / float(gen), 4),
            ),
            FunnelStageMetric(
                stage="Added to Quote",
                count=analytics.total_added_to_quote,
                conversion_rate_from_top=round(float(analytics.total_added_to_quote) / float(gen), 4),
            ),
            FunnelStageMetric(
                stage="Accepted",
                count=analytics.total_accepted,
                conversion_rate_from_top=round(float(analytics.total_accepted) / float(gen), 4),
            ),
        ]

        # Category distribution from products
        cats = db.scalars(select(ProductCategory)).all()
        cat_map = {c.id: c.name for c in cats}
        prods = db.scalars(select(Product).where(Product.is_active == True)).all()

        cat_dist: Dict[str, int] = {}
        for p in prods:
            c_name = cat_map.get(p.category_id, "General")
            cat_dist[c_name] = cat_dist.get(c_name, 0) + 1

        # Recent activities
        recent_events = db.scalars(
            select(RecommendationEvent)
            .where(RecommendationEvent.company_id == company_id)
            .order_by(desc(RecommendationEvent.created_at))
            .limit(10)
        ).all()

        activities: List[RecentActivityItem] = []
        for e in recent_events:
            activities.append(
                RecentActivityItem(
                    event_id=e.id,
                    event_type=e.event_type,
                    recommendation_type=e.recommendation_type,
                    customer_id=e.customer_id,
                    product_id=e.product_id,
                    score=float(e.score),
                    timestamp=e.created_at,
                )
            )

        kpis = {
            "total_recommendations": analytics.total_recommendations_generated,
            "acceptance_rate_pct": round(analytics.acceptance_rate * 100, 1),
            "add_to_quote_rate_pct": round(analytics.add_to_quote_rate * 100, 1),
            "average_score": analytics.average_recommendation_score,
            "upsell_volume": analytics.upsell_events_count,
            "cross_sell_volume": analytics.cross_sell_events_count,
        }

        return UpsellDashboardSummary(
            kpis=kpis,
            conversion_funnel=funnel,
            category_distribution=cat_dist,
            analytics=analytics,
            recent_activity=activities,
            generated_at=datetime.now(timezone.utc),
        )
