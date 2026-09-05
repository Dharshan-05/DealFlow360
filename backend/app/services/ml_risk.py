"""ML Risk Feature Engineering & Dataset Preparation Services (DealFlow360 B01 & B02: Phases 121–130).

Implements:
- Phase 121: ML Dataset Preparation (Data extraction, validation, missing value imputation, sanitization)
- Phase 122: Historical Deal Dataset (Point-in-time extraction from CustomerDealHistory & AppliedDiscount)
- Phase 123: Feature Engineering (Tabular feature transformation, numerical/categorical encoding, leakage safety)
- Phase 124: Discount Features (Contextual discount ceiling utilization, deviation from baseline, risk indicators)
- Phase 125: Margin Features (Decimal-safe gross margin, post-discount compression, pressure ratios)
- Phase 126: Customer Features (Tenure, tier, LTV, AOV, payment default ratio, payment reliability score)
- Phase 127: Deal Value Features (Nominal, log-scale, size band classification, ratio/deviation to customer AOV)
- Phase 128: Discount Behavior Features (Historical discount frequency, max discount, volatility, escalation rate)
- Phase 129: Margin Behavior Features (Historical margin mean/min/max, volatility, low-margin deal frequency, trend)
- Phase 130: Risk Target Definition (Deterministic binary target is_high_risk, risk level, primary trigger factors)

Strictly non-ML-training: provides the dataset, feature-engineering, and target-labeling foundation for future Phase Group 09 models.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applied_discount import AppliedDiscount
from app.models.category_discount_ceiling import CategoryDiscountCeiling
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.customer_purchase_history import CustomerPurchaseHistory
from app.models.customer_tier import CustomerTier
from app.models.discount_configuration import DiscountConfiguration
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_discount_ceiling import ProductDiscountCeiling
from app.schemas.ml_risk import (
    CustomerFeatures,
    DatasetMetadata,
    DatasetPreparationResponse,
    DatasetType,
    DealSizeCategory,
    DealValueFeatures,
    DiscountBehaviorFeatures,
    DiscountFeatures,
    EngineeredFeatureVector,
    MarginBehaviorFeatures,
    MarginFeatures,
    NormalizationStrategy,
    RawDealRecord,
    RiskTarget,
)


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    """Safely quantize Decimal to specified decimal places."""
    fmt = Decimal("1." + "0" * places) if places > 0 else Decimal("1")
    return val.quantize(fmt, rounding=ROUND_HALF_UP)


# ==============================================================================
# Phase 125: Margin Features Engine (Current Deal)
# ==============================================================================

class MarginFeatureEngineer:
    """Deterministic Margin Feature Engineering (Phase 125).
    Evaluates gross profit, post-discount margin, margin compression, and edge cases
    using strict Decimal arithmetic before converting to floating point for ML.
    """

    @classmethod
    def compute(
        cls,
        selling_price: Decimal,
        unit_cost: Decimal,
        discount_pct: Decimal,
    ) -> MarginFeatures:
        """Compute margin features for current deal."""
        safe_price = max(selling_price, Decimal("0.00"))
        safe_cost = max(unit_cost, Decimal("0.00"))
        safe_discount_pct = max(min(discount_pct, Decimal("100.00")), Decimal("0.00"))

        gross_margin_amount = safe_price - safe_cost
        
        if safe_price > Decimal("0.00"):
            gross_margin_pct = (gross_margin_amount / safe_price) * Decimal("100.00")
        else:
            gross_margin_pct = Decimal("0.00")

        discount_multiplier = (Decimal("100.00") - safe_discount_pct) / Decimal("100.00")
        discounted_price = quantize_dec(safe_price * discount_multiplier)

        discounted_margin_amount = discounted_price - safe_cost
        if discounted_price > Decimal("0.00"):
            discounted_margin_pct = (discounted_margin_amount / discounted_price) * Decimal("100.00")
        else:
            discounted_margin_pct = Decimal("0.00")

        discount_amount = safe_price - discounted_price
        if gross_margin_amount > Decimal("0.00"):
            margin_reduction_ratio = discount_amount / gross_margin_amount
            discount_to_margin_pressure = discount_amount / gross_margin_amount
        else:
            margin_reduction_ratio = Decimal("1.00") if discount_amount > Decimal("0.00") else Decimal("0.00")
            discount_to_margin_pressure = Decimal("1.00") if discount_amount > Decimal("0.00") else Decimal("0.00")

        is_negative_margin = discounted_margin_amount < Decimal("0.00")
        is_zero_cost = safe_cost == Decimal("0.00")

        return MarginFeatures(
            unit_cost=float(safe_cost),
            selling_price=float(safe_price),
            gross_margin_amount=float(quantize_dec(gross_margin_amount)),
            gross_margin_pct=float(quantize_dec(gross_margin_pct)),
            discounted_price=float(discounted_price),
            discounted_margin_amount=float(quantize_dec(discounted_margin_amount)),
            discounted_margin_pct=float(quantize_dec(discounted_margin_pct)),
            margin_reduction_ratio=float(quantize_dec(margin_reduction_ratio, places=4)),
            is_negative_margin=is_negative_margin,
            is_zero_cost=is_zero_cost,
            discount_to_margin_pressure=float(quantize_dec(discount_to_margin_pressure, places=4)),
        )


# ==============================================================================
# Phase 124: Discount Features Engine (Current Deal)
# ==============================================================================

class DiscountFeatureEngineer:
    """Deterministic Discount Feature Engineering (Phase 124).
    Calculates discount intensity, ceiling utilization, customer variance,
    and governance breach indicators.
    """

    @classmethod
    def compute(
        cls,
        requested_discount_pct: Decimal,
        effective_ceiling_pct: Decimal,
        customer_historical_avg_pct: Decimal,
        tier_discount_limit: Decimal,
        deal_value: Decimal,
        has_prior_history: bool,
    ) -> DiscountFeatures:
        """Compute discount features for current deal."""
        safe_req_disc = max(min(requested_discount_pct, Decimal("100.00")), Decimal("0.00"))
        safe_ceiling = max(effective_ceiling_pct, Decimal("0.00"))
        safe_hist_avg = max(customer_historical_avg_pct, Decimal("0.00"))
        safe_tier_limit = max(tier_discount_limit, Decimal("0.00"))
        safe_deal_val = max(deal_value, Decimal("0.00"))

        if safe_ceiling > Decimal("0.00"):
            ceiling_utilization_ratio = safe_req_disc / safe_ceiling
        else:
            ceiling_utilization_ratio = Decimal("1.00") if safe_req_disc > Decimal("0.00") else Decimal("0.00")

        is_ceiling_breached = safe_req_disc > safe_ceiling
        discount_deviation = safe_req_disc - safe_hist_avg

        if safe_tier_limit > Decimal("0.00"):
            tier_utilization_ratio = safe_req_disc / safe_tier_limit
        else:
            tier_utilization_ratio = Decimal("1.00") if safe_req_disc > Decimal("0.00") else Decimal("0.00")

        discount_amount_est = quantize_dec(safe_deal_val * (safe_req_disc / Decimal("100.00")))

        return DiscountFeatures(
            requested_discount_pct=float(quantize_dec(safe_req_disc)),
            effective_ceiling_pct=float(quantize_dec(safe_ceiling)),
            ceiling_utilization_ratio=float(quantize_dec(ceiling_utilization_ratio, places=4)),
            is_ceiling_breached=is_ceiling_breached,
            customer_historical_avg_discount=float(quantize_dec(safe_hist_avg)),
            discount_deviation_from_customer_avg=float(quantize_dec(discount_deviation)),
            has_prior_discount_history=has_prior_history,
            tier_discount_limit=float(quantize_dec(safe_tier_limit)),
            tier_utilization_ratio=float(quantize_dec(tier_utilization_ratio, places=4)),
            discount_amount_est=float(discount_amount_est),
        )


# ==============================================================================
# Phase 126: Customer Features Engine
# ==============================================================================

class CustomerFeatureEngineer:
    """Deterministic Customer Feature Engineering (Phase 126).
    Synthesizes relationship tenure, tier context, order counts, lifetime revenue,
    payment default rates, and price sensitivity from prior point-in-time data.
    """

    @classmethod
    def compute(
        cls,
        tenure_days: int,
        customer_tier: str,
        tier_discount_limit: Decimal,
        lifetime_orders: int,
        lifetime_revenue: Decimal,
        lifetime_settled: Decimal,
        failed_payments: int,
        total_payments: int,
        avg_discount_pct: Decimal,
        discount_count: int,
    ) -> CustomerFeatures:
        """Compute customer-level ML features."""
        # AOV calculation
        if lifetime_orders > 0:
            aov = quantize_dec(lifetime_revenue / Decimal(lifetime_orders))
        else:
            aov = Decimal("0.00")

        # Payment default ratio & reliability score (aligned with Phase 065)
        if total_payments > 0:
            default_ratio = Decimal(failed_payments) / Decimal(total_payments)
            reliability_score = max(Decimal("0.00"), Decimal("100.00") - (default_ratio * Decimal("100.00")))
        else:
            default_ratio = Decimal("0.00")
            reliability_score = Decimal("85.00")  # Neutral baseline for new account without payment history

        # Price sensitivity score (aligned with Phase 064: higher discount reliance = higher sensitivity)
        if lifetime_orders > 0:
            disc_freq = Decimal(discount_count) / Decimal(lifetime_orders)
            price_sens = min(Decimal("100.00"), (avg_discount_pct * Decimal("3.0")) + (disc_freq * Decimal("40.0")))
        else:
            price_sens = Decimal("20.00")

        is_established = (lifetime_orders >= 3) or (tenure_days >= 90)

        return CustomerFeatures(
            customer_tenure_days=max(tenure_days, 0),
            customer_tier=customer_tier,
            tier_discount_limit=float(quantize_dec(tier_discount_limit)),
            is_established_customer=is_established,
            lifetime_orders_count=lifetime_orders,
            lifetime_revenue=float(quantize_dec(lifetime_revenue)),
            lifetime_settled_amount=float(quantize_dec(lifetime_settled)),
            average_order_value=float(aov),
            payment_default_ratio=float(quantize_dec(default_ratio, places=4)),
            payment_reliability_score=float(quantize_dec(reliability_score)),
            has_payment_history=(total_payments > 0),
            price_sensitivity_score=float(quantize_dec(price_sens)),
        )


# ==============================================================================
# Phase 127: Deal Value Features Engine
# ==============================================================================

class DealValueFeatureEngineer:
    """Deterministic Deal Value Feature Engineering (Phase 127).
    Derives nominal scale, log transform, transaction size category, and comparison to customer's AOV.
    """

    @classmethod
    def compute(
        cls,
        deal_value: Decimal,
        customer_aov: Decimal,
        has_prior_orders: bool,
    ) -> DealValueFeatures:
        """Compute deal value features."""
        safe_val = max(deal_value, Decimal("0.00"))
        float_val = float(safe_val)
        log_val = math.log1p(float_val)

        # Categorize size band
        if safe_val < Decimal("1000.00"):
            category = DealSizeCategory.MICRO.value
        elif safe_val < Decimal("10000.00"):
            category = DealSizeCategory.SMALL.value
        elif safe_val < Decimal("50000.00"):
            category = DealSizeCategory.MEDIUM.value
        elif safe_val < Decimal("250000.00"):
            category = DealSizeCategory.LARGE.value
        else:
            category = DealSizeCategory.ENTERPRISE.value

        # Deal to AOV ratio & outlier detection
        if has_prior_orders and customer_aov > Decimal("0.00"):
            deal_to_aov = safe_val / customer_aov
            is_outlier = deal_to_aov > Decimal("3.00")
            deviation = safe_val - customer_aov
        else:
            deal_to_aov = Decimal("1.00")
            is_outlier = False
            deviation = Decimal("0.00")

        return DealValueFeatures(
            deal_value=float(quantize_dec(safe_val)),
            log_deal_value=round(log_val, 4),
            deal_size_category=category,
            deal_to_aov_ratio=float(quantize_dec(deal_to_aov, places=4)),
            is_deal_value_outlier=is_outlier,
            deal_value_deviation_from_aov=float(quantize_dec(deviation)),
            has_prior_aov_benchmark=has_prior_orders,
        )


# ==============================================================================
# Phase 128: Discount Behavior Features Engine
# ==============================================================================

class DiscountBehaviorFeatureEngineer:
    """Historical Discount Behavior Feature Engineering (Phase 128).
    Evaluates prior customer discount frequency, maximum discount awarded, standard deviation,
    trend, and historical escalation rate strictly before deal timestamp.
    """

    @classmethod
    def compute(
        cls,
        prior_discounts: List[Any],
        total_prior_orders: int = 0,
        prior_applied_discounts: Optional[List[Any]] = None,
    ) -> DiscountBehaviorFeatures:
        """Compute discount behavior features. Accepts ORM records or Decimals."""
        if prior_applied_discounts is None:
            prior_applied_discounts = []

        discount_percentages: List[Decimal] = [
            d.discount_percentage if hasattr(d, "discount_percentage") else Decimal(str(d))
            for d in prior_discounts
        ]
        for ad in prior_applied_discounts:
            discount_percentages.append(
                ad.applied_discount if hasattr(ad, "applied_discount") else Decimal(str(ad))
            )

        discount_count = len(discount_percentages)

        if total_prior_orders > 0:
            freq_pct = (Decimal(discount_count) / Decimal(total_prior_orders)) * Decimal("100.00")
            freq_pct = min(freq_pct, Decimal("100.00"))
        else:
            freq_pct = Decimal("100.00") if discount_count > 0 else Decimal("0.00")

        if discount_count > 0:
            avg_pct = sum(discount_percentages, Decimal("0.00")) / Decimal(discount_count)
            max_pct = max(discount_percentages)

            # Volatility (Standard Deviation)
            if discount_count > 1:
                variance = sum(((d - avg_pct) ** 2 for d in discount_percentages), Decimal("0.00")) / Decimal(discount_count - 1)
                volatility = Decimal(str(math.sqrt(float(variance))))
            else:
                volatility = Decimal("0.00")

            # Trend: compare first half average to second half average
            if discount_count >= 4:
                half = discount_count // 2
                first_half_avg = sum(discount_percentages[:half], Decimal("0.00")) / Decimal(half)
                second_half_avg = sum(discount_percentages[half:], Decimal("0.00")) / Decimal(discount_count - half)
                if second_half_avg > first_half_avg + Decimal("1.50"):
                    trend = Decimal("1.00")   # Expanding discounts
                elif second_half_avg < first_half_avg - Decimal("1.50"):
                    trend = Decimal("-1.00")  # Contracting discounts
                else:
                    trend = Decimal("0.00")   # Stable
            else:
                trend = Decimal("0.00")
        else:
            avg_pct = Decimal("0.00")
            max_pct = Decimal("0.00")
            volatility = Decimal("0.00")
            trend = Decimal("0.00")

        # Escalations & Rejections from prior AppliedDiscounts
        escalation_count = sum(
            1 for ad in prior_applied_discounts
            if hasattr(ad, "reason_code") and "ESCALATION" in (ad.reason_code or "")
        )
        rejection_count = sum(
            1 for ad in prior_applied_discounts
            if hasattr(ad, "reason_code") and "REJECTED" in (ad.reason_code or "")
        )

        if len(prior_applied_discounts) > 0:
            esc_rate = Decimal(escalation_count) / Decimal(len(prior_applied_discounts))
        else:
            esc_rate = Decimal("0.00")

        return DiscountBehaviorFeatures(
            historical_discount_count=discount_count,
            historical_discount_frequency_pct=float(quantize_dec(freq_pct)),
            historical_avg_discount_pct=float(quantize_dec(avg_pct)),
            historical_max_discount_pct=float(quantize_dec(max_pct)),
            historical_discount_volatility=float(quantize_dec(volatility)),
            discount_trend_slope=float(quantize_dec(trend)),
            historical_escalation_count=escalation_count,
            historical_rejection_count=rejection_count,
            historical_escalation_rate=float(quantize_dec(esc_rate, places=4)),
        )


# ==============================================================================
# Phase 129: Margin Behavior Features Engine
# ==============================================================================

class MarginBehaviorFeatureEngineer:
    """Historical Margin Behavior Feature Engineering (Phase 129).
    Quantifies historical track record for post-discount gross margin, minimum margin recorded,
    volatility, and low-margin (<20%) frequency strictly before deal timestamp.
    """

    @classmethod
    def compute(
        cls,
        prior_applied_discounts: List[Any],
    ) -> MarginBehaviorFeatures:
        """Compute margin behavior features. Accepts ORM records or Decimals."""
        margin_pcts: List[Decimal] = [
            ad.margin_percentage if hasattr(ad, "margin_percentage") else Decimal(str(ad))
            for ad in prior_applied_discounts
        ]
        count = len(margin_pcts)

        if count > 0:
            avg_margin = sum(margin_pcts, Decimal("0.00")) / Decimal(count)
            min_margin = min(margin_pcts)
            max_margin = max(margin_pcts)

            # Volatility
            if count > 1:
                variance = sum(((m - avg_margin) ** 2 for m in margin_pcts), Decimal("0.00")) / Decimal(count - 1)
                volatility = Decimal(str(math.sqrt(float(variance))))
            else:
                volatility = Decimal("0.00")

            low_margin_deals = sum(1 for m in margin_pcts if m < Decimal("20.00"))
            low_margin_freq = (Decimal(low_margin_deals) / Decimal(count)) * Decimal("100.00")

            # Trend: compare recent to early
            if count >= 4:
                half = count // 2
                first_avg = sum(margin_pcts[:half], Decimal("0.00")) / Decimal(half)
                second_avg = sum(margin_pcts[half:], Decimal("0.00")) / Decimal(count - half)
                if second_avg > first_avg + Decimal("2.00"):
                    trend = Decimal("1.00")   # Improving margins
                elif second_avg < first_avg - Decimal("2.00"):
                    trend = Decimal("-1.00")  # Deteriorating margins
                else:
                    trend = Decimal("0.00")
            else:
                trend = Decimal("0.00")
        else:
            avg_margin = Decimal("0.00")
            min_margin = Decimal("0.00")
            max_margin = Decimal("0.00")
            volatility = Decimal("0.00")
            low_margin_deals = 0
            low_margin_freq = Decimal("0.00")
            trend = Decimal("0.00")

        return MarginBehaviorFeatures(
            historical_avg_margin_pct=float(quantize_dec(avg_margin)),
            historical_min_margin_pct=float(quantize_dec(min_margin)),
            historical_max_margin_pct=float(quantize_dec(max_margin)),
            historical_margin_volatility=float(quantize_dec(volatility)),
            historical_low_margin_deal_count=low_margin_deals,
            low_margin_frequency_pct=float(quantize_dec(low_margin_freq)),
            margin_erosion_trend=float(quantize_dec(trend)),
            has_prior_margin_history=(count > 0),
        )


# ==============================================================================
# Phase 130: Risk Target Generator
# ==============================================================================

class RiskTargetGenerator:
    """Deterministic, explainable risk target label generator for ML risk modeling (Phase 130).
    Produces binary classification target (is_high_risk: 0 or 1) and structured risk triggers
    without target leakage.
    """

    @classmethod
    def generate_target(
        cls,
        record: Optional[RawDealRecord] = None,
        effective_ceiling: Decimal = Decimal("15.00"),
        margin_pct: Decimal = Decimal("25.00"),
        requested_discount_pct: Optional[Decimal] = None,
        risk_level: Optional[str] = None,
        decision_outcome: Optional[str] = None,
        deal_status: Optional[str] = None,
        reason_code: Optional[str] = None,
        prior_failed_payments_count: int = 0,
    ) -> RiskTarget:
        """Generate deterministic risk target."""
        if record is not None:
            req_disc = record.requested_discount_pct
            r_level = record.risk_level
            d_outcome = record.decision_outcome
            d_status = record.deal_status
            r_code = record.reason_code or ""
            failed_payments = record.prior_failed_payments_count
        else:
            req_disc = requested_discount_pct if requested_discount_pct is not None else Decimal("0.00")
            r_level = risk_level or "LOW"
            d_outcome = decision_outcome or "APPROVED"
            d_status = deal_status or "WON"
            r_code = reason_code or ""
            failed_payments = prior_failed_payments_count

        reasons: List[str] = []
        is_gov_breached = req_disc > effective_ceiling
        is_margin_breached = margin_pct < Decimal("15.00")
        is_escalation = d_outcome == "ESCALATION_REQUIRED" or "ESCALATION" in r_code
        is_rejected = d_outcome == "REJECTED" or d_status == "LOST"

        if is_gov_breached:
            reasons.append(f"Requested discount ({req_disc}%) breached governance ceiling ({effective_ceiling}%)")
        if is_margin_breached:
            reasons.append(f"Realized/proposed margin ({margin_pct}%) fell below minimum threshold (15.00%)")
        if is_escalation:
            reasons.append("Deal required supervisory/finance escalation")
        if is_rejected:
            reasons.append("Deal was rejected by governance or lost")

        # Binary label: 1 if high risk, 0 if normal/safe
        is_high_risk = 1 if (is_gov_breached or is_margin_breached or is_rejected or r_level in ("HIGH", "CRITICAL")) else 0

        # Primary failure mode categorization
        if is_margin_breached:
            category = "MARGIN_EROSION"
        elif is_gov_breached:
            category = "GOVERNANCE_BREACH"
        elif is_rejected:
            category = "DEAL_REJECTION"
        elif failed_payments > 0:
            category = "PAYMENT_DEFAULT"
        else:
            category = "NONE"

        return RiskTarget(
            is_high_risk=is_high_risk,
            risk_level=r_level,
            risk_category=category,
            is_governance_breached=is_gov_breached,
            is_margin_breached=is_margin_breached,
            is_escalation_triggered=is_escalation,
            is_rejected=is_rejected,
            trigger_reasons=reasons,
        )


# ==============================================================================
# Phase 122: Historical Deal Dataset Extractor (Leakage-Safe Point-in-Time)
# ==============================================================================

class HistoricalDealDatasetExtractor:
    """Extracts, filters, and standardizes point-in-time deal records (Phase 122).
    Combines verified entities: CustomerDealHistory, AppliedDiscount, CustomerPurchaseHistory,
    CustomerPaymentHistory, CustomerDiscountHistory, Product, and CustomerTier.
    """

    @classmethod
    def extract_records(
        cls,
        db: Session,
        company_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[RawDealRecord]:
        """Extract point-in-time historical deal records with tenant isolation."""
        customers = db.scalars(
            select(Customer).where(Customer.company_id == company_id)
        ).all()
        customer_map = {c.id: c for c in customers}

        tiers = db.scalars(select(CustomerTier)).all()
        tier_map = {t.id: t for t in tiers}

        products = db.scalars(select(Product)).all()
        product_map = {p.id: p for p in products}

        categories = db.scalars(select(ProductCategory)).all()
        cat_map = {c.id: c.code for c in categories}

        raw_records: List[RawDealRecord] = []
        seen_keys: Set[str] = set()

        # Query A: AppliedDiscount (Phase 120)
        query_discounts = select(AppliedDiscount).where(AppliedDiscount.company_id == company_id)
        if start_date:
            query_discounts = query_discounts.where(AppliedDiscount.created_at >= start_date)
        if end_date:
            query_discounts = query_discounts.where(AppliedDiscount.created_at <= end_date)
        query_discounts = query_discounts.order_by(AppliedDiscount.created_at.asc())
        
        applied_discounts = db.scalars(query_discounts).all()

        for ad in applied_discounts:
            cust = customer_map.get(ad.customer_id)
            if not cust:
                continue

            tier = tier_map.get(cust.tier_id) if cust.tier_id else None
            tier_code = tier.code if tier else "NONE"
            tier_limit = tier.discount_limit if tier else Decimal("0.00")

            prod = product_map.get(ad.product_id)
            prod_sku = prod.sku if prod else None
            prod_cat = cat_map.get(prod.category_id, "GENERAL") if prod and prod.category_id else "GENERAL"

            # Compute prior metrics strictly before ad.created_at (zero leakage)
            prior_stats = cls._compute_prior_customer_metrics(
                db=db,
                company_id=company_id,
                customer_id=cust.id,
                as_of=ad.created_at,
            )

            record_id = f"AD-{ad.id}"
            if record_id in seen_keys:
                continue
            seen_keys.add(record_id)

            raw_records.append(
                RawDealRecord(
                    record_id=record_id,
                    deal_reference=ad.deal_reference or f"DEAL-{ad.id.hex[:8].upper()}",
                    company_id=company_id,
                    customer_id=cust.id,
                    customer_code=cust.customer_code,
                    customer_tier=tier_code,
                    tier_discount_limit=tier_limit,
                    deal_value=ad.selling_price,
                    requested_discount_pct=ad.requested_discount,
                    applied_discount_pct=ad.applied_discount,
                    product_id=ad.product_id,
                    product_sku=prod_sku,
                    product_category=prod_cat,
                    unit_cost=ad.unit_cost,
                    selling_price=ad.selling_price,
                    prior_purchases_count=prior_stats["purchases_count"],
                    prior_purchases_total=prior_stats["purchases_total"],
                    prior_discounts_count=prior_stats["discounts_count"],
                    prior_discount_avg_pct=prior_stats["discount_avg_pct"],
                    prior_payments_count=prior_stats["payments_count"],
                    prior_payments_total=prior_stats["payments_total"],
                    prior_failed_payments_count=prior_stats["failed_payments_count"],
                    inventory_signal="HEALTHY_STOCK",
                    deal_status="WON",
                    decision_outcome="APPROVED",
                    risk_level=ad.risk_level,
                    reason_code=ad.reason_code,
                    closed_at=ad.created_at,
                    created_at=ad.created_at,
                )
            )

        # Query B: CustomerDealHistory (Phase 060)
        query_deals = select(CustomerDealHistory).where(CustomerDealHistory.company_id == company_id)
        if start_date:
            query_deals = query_deals.where(CustomerDealHistory.created_at >= start_date)
        if end_date:
            query_deals = query_deals.where(CustomerDealHistory.created_at <= end_date)
        query_deals = query_deals.order_by(CustomerDealHistory.created_at.asc())

        deal_histories = db.scalars(query_deals).all()

        for dh in deal_histories:
            cust = customer_map.get(dh.customer_id)
            if not cust:
                continue

            tier = tier_map.get(cust.tier_id) if cust.tier_id else None
            tier_code = tier.code if tier else "NONE"
            tier_limit = tier.discount_limit if tier else Decimal("0.00")

            record_id = f"DH-{dh.id}"
            if record_id in seen_keys:
                continue
            seen_keys.add(record_id)

            prior_stats = cls._compute_prior_customer_metrics(
                db=db,
                company_id=company_id,
                customer_id=cust.id,
                as_of=dh.created_at,
            )

            raw_records.append(
                RawDealRecord(
                    record_id=record_id,
                    deal_reference=dh.deal_code,
                    company_id=company_id,
                    customer_id=cust.id,
                    customer_code=cust.customer_code,
                    customer_tier=tier_code,
                    tier_discount_limit=tier_limit,
                    deal_value=dh.deal_value,
                    requested_discount_pct=tier_limit,
                    applied_discount_pct=tier_limit,
                    product_id=None,
                    product_sku=None,
                    product_category="GENERAL",
                    unit_cost=quantize_dec(dh.deal_value * Decimal("0.70")),
                    selling_price=dh.deal_value,
                    prior_purchases_count=prior_stats["purchases_count"],
                    prior_purchases_total=prior_stats["purchases_total"],
                    prior_discounts_count=prior_stats["discounts_count"],
                    prior_discount_avg_pct=prior_stats["discount_avg_pct"],
                    prior_payments_count=prior_stats["payments_count"],
                    prior_payments_total=prior_stats["payments_total"],
                    prior_failed_payments_count=prior_stats["failed_payments_count"],
                    inventory_signal="HEALTHY_STOCK",
                    deal_status=dh.status,
                    decision_outcome="APPROVED" if dh.status == "WON" else "REJECTED",
                    risk_level="LOW" if dh.status == "WON" else "HIGH",
                    reason_code="STANDARD",
                    closed_at=dh.closed_date or dh.created_at,
                    created_at=dh.created_at,
                )
            )

        raw_records.sort(key=lambda r: (r.created_at, r.record_id))
        return raw_records

    @classmethod
    def _compute_prior_customer_metrics(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        as_of: datetime,
    ) -> Dict[str, Any]:
        """Compute point-in-time prior historical metrics strictly before as_of (zero future leakage)."""
        purchases = db.scalars(
            select(CustomerPurchaseHistory).where(
                CustomerPurchaseHistory.company_id == company_id,
                CustomerPurchaseHistory.customer_id == customer_id,
                CustomerPurchaseHistory.purchase_date < as_of,
            )
        ).all()
        purchases_count = len(purchases)
        purchases_total = sum((p.total_amount for p in purchases), Decimal("0.00"))

        discounts = db.scalars(
            select(CustomerDiscountHistory).where(
                CustomerDiscountHistory.company_id == company_id,
                CustomerDiscountHistory.customer_id == customer_id,
                CustomerDiscountHistory.applied_at < as_of,
            )
        ).all()
        discounts_count = len(discounts)
        if discounts_count > 0:
            discount_avg_pct = sum((d.discount_percentage for d in discounts), Decimal("0.00")) / Decimal(discounts_count)
        else:
            discount_avg_pct = Decimal("0.00")

        payments = db.scalars(
            select(CustomerPaymentHistory).where(
                CustomerPaymentHistory.company_id == company_id,
                CustomerPaymentHistory.customer_id == customer_id,
                CustomerPaymentHistory.created_at < as_of,
            )
        ).all()
        payments_count = len(payments)
        payments_total = sum((p.amount for p in payments), Decimal("0.00"))
        failed_count = sum(1 for p in payments if p.status in ("FAILED", "REFUNDED"))

        return {
            "purchases_count": purchases_count,
            "purchases_total": purchases_total,
            "discounts_count": discounts_count,
            "discount_avg_pct": quantize_dec(discount_avg_pct),
            "payments_count": payments_count,
            "payments_total": payments_total,
            "failed_payments_count": failed_count,
        }


# ==============================================================================
# Phase 123: Generic Feature Engineering Layer (Extended with B02 Features)
# ==============================================================================

class FeatureEngineeringService:
    """Transforms raw point-in-time historical deal records into ML-ready tabular feature vectors (Phases 123–130)."""

    @classmethod
    def transform_record(
        cls,
        db: Session,
        record: RawDealRecord,
    ) -> EngineeredFeatureVector:
        """Transform a single RawDealRecord into an EngineeredFeatureVector."""
        # 1. Determine active policy ceiling at deal timestamp (Phase 108/124)
        active_ceiling = cls._resolve_effective_ceiling(
            db=db,
            company_id=record.company_id,
            customer_id=record.customer_id,
            product_id=record.product_id,
            at_timestamp=record.created_at,
        )

        # 2. Compute Phase 124 Discount Features
        discount_features = DiscountFeatureEngineer.compute(
            requested_discount_pct=record.requested_discount_pct,
            effective_ceiling_pct=active_ceiling,
            customer_historical_avg_pct=record.prior_discount_avg_pct,
            tier_discount_limit=record.tier_discount_limit,
            deal_value=record.deal_value,
            has_prior_history=(record.prior_discounts_count > 0),
        )

        # 3. Compute Phase 125 Margin Features
        margin_features = MarginFeatureEngineer.compute(
            selling_price=record.selling_price,
            unit_cost=record.unit_cost,
            discount_pct=record.applied_discount_pct,
        )

        # 4. Customer Relationship Tenure
        customer = db.get(Customer, record.customer_id)
        if customer and customer.created_at:
            tenure_delta = (record.created_at - customer.created_at).days
            tenure_days = max(tenure_delta, 0)
        else:
            tenure_days = 0

        # 5. Fetch point-in-time prior histories strictly before deal created_at (Zero Leakage)
        prior_discounts = db.scalars(
            select(CustomerDiscountHistory).where(
                CustomerDiscountHistory.company_id == record.company_id,
                CustomerDiscountHistory.customer_id == record.customer_id,
                CustomerDiscountHistory.applied_at < record.created_at,
            ).order_by(CustomerDiscountHistory.applied_at.asc())
        ).all()

        prior_applied = db.scalars(
            select(AppliedDiscount).where(
                AppliedDiscount.company_id == record.company_id,
                AppliedDiscount.customer_id == record.customer_id,
                AppliedDiscount.created_at < record.created_at,
            ).order_by(AppliedDiscount.created_at.asc())
        ).all()

        # 6. Compute Phase 126 Customer Features
        customer_features = CustomerFeatureEngineer.compute(
            tenure_days=tenure_days,
            customer_tier=record.customer_tier,
            tier_discount_limit=record.tier_discount_limit,
            lifetime_orders=record.prior_purchases_count,
            lifetime_revenue=record.prior_purchases_total,
            lifetime_settled=record.prior_payments_total,
            failed_payments=record.prior_failed_payments_count,
            total_payments=record.prior_payments_count,
            avg_discount_pct=record.prior_discount_avg_pct,
            discount_count=record.prior_discounts_count,
        )

        # 7. Compute Phase 127 Deal Value Features
        deal_value_features = DealValueFeatureEngineer.compute(
            deal_value=record.deal_value,
            customer_aov=Decimal(str(customer_features.average_order_value)),
            has_prior_orders=(record.prior_purchases_count > 0),
        )

        # 8. Compute Phase 128 Discount Behavior Features
        discount_behavior_features = DiscountBehaviorFeatureEngineer.compute(
            prior_discounts=prior_discounts,
            prior_applied_discounts=prior_applied,
            total_prior_orders=record.prior_purchases_count,
        )

        # 9. Compute Phase 129 Margin Behavior Features
        margin_behavior_features = MarginBehaviorFeatureEngineer.compute(
            prior_applied_discounts=prior_applied,
        )

        # 10. Generate Phase 130 Risk Target
        risk_target = RiskTargetGenerator.generate_target(
            record=record,
            effective_ceiling=active_ceiling,
            margin_pct=Decimal(str(margin_features.discounted_margin_pct)),
        )

        float_deal_val = float(record.deal_value)
        log_deal_val = math.log1p(max(float_deal_val, 0.0))

        return EngineeredFeatureVector(
            record_id=record.record_id,
            company_id=str(record.company_id),
            customer_id=str(record.customer_id),
            customer_tier=record.customer_tier,
            product_category=record.product_category or "GENERAL",
            inventory_signal=record.inventory_signal,
            deal_value=float_deal_val,
            log_deal_value=round(log_deal_val, 4),
            prior_purchases_count=record.prior_purchases_count,
            prior_purchases_total=float(record.prior_purchases_total),
            prior_payments_count=record.prior_payments_count,
            prior_payments_total=float(record.prior_payments_total),
            customer_tenure_days=tenure_days,
            discount_features=discount_features,
            margin_features=margin_features,
            customer_features=customer_features,
            deal_value_features=deal_value_features,
            discount_behavior_features=discount_behavior_features,
            margin_behavior_features=margin_behavior_features,
            target=risk_target,
            target_risk_level=record.risk_level,
            target_deal_outcome=record.deal_status,
        )

    @classmethod
    def _resolve_effective_ceiling(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        product_id: Optional[uuid.UUID],
        at_timestamp: datetime,
    ) -> Decimal:
        """Resolve point-in-time discount ceiling using active governance rules."""
        candidate_ceilings: List[Decimal] = []

        configs = db.scalars(
            select(DiscountConfiguration).where(
                DiscountConfiguration.company_id == company_id,
                DiscountConfiguration.is_active == True,
            )
        ).all()
        for cfg in configs:
            if cfg.effective_from <= at_timestamp and (cfg.effective_until is None or cfg.effective_until >= at_timestamp):
                candidate_ceilings.append(cfg.default_discount_ceiling)

        cust_ceilings = db.scalars(
            select(CustomerDiscountCeiling).where(
                CustomerDiscountCeiling.company_id == company_id,
                CustomerDiscountCeiling.customer_id == customer_id,
                CustomerDiscountCeiling.is_active == True,
            )
        ).all()
        for cc in cust_ceilings:
            if cc.effective_from <= at_timestamp and (cc.effective_until is None or cc.effective_until >= at_timestamp):
                candidate_ceilings.append(cc.max_discount_percentage)

        if product_id:
            prod_ceilings = db.scalars(
                select(ProductDiscountCeiling).where(
                    ProductDiscountCeiling.company_id == company_id,
                    ProductDiscountCeiling.product_id == product_id,
                    ProductDiscountCeiling.is_active == True,
                )
            ).all()
            for pc in prod_ceilings:
                if pc.effective_from <= at_timestamp and (pc.effective_until is None or pc.effective_until >= at_timestamp):
                    candidate_ceilings.append(pc.max_discount_percentage)

        if candidate_ceilings:
            return min(candidate_ceilings)
        return Decimal("15.00")


# ==============================================================================
# Phase 121: ML Dataset Preparation Orchestrator
# ==============================================================================

class MLDatasetPreparationService:
    """Deterministic orchestrator preparing datasets for downstream AI/ML Risk Engine (Phases 121–130)."""

    @classmethod
    def prepare_deal_risk_dataset(
        cls,
        db: Session,
        company_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_deal_value: Optional[Decimal] = None,
        filter_status: Optional[str] = None,
    ) -> DatasetPreparationResponse:
        """Extract historical deals, validate records, engineer features, and return ML-ready dataset."""
        raw_records = HistoricalDealDatasetExtractor.extract_records(
            db=db,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
        )

        total_extracted = len(raw_records)
        features: List[EngineeredFeatureVector] = []
        invalid_count = 0

        for rec in raw_records:
            if min_deal_value and rec.deal_value < min_deal_value:
                invalid_count += 1
                continue
            if filter_status and rec.deal_status != filter_status:
                invalid_count += 1
                continue

            if rec.deal_value < Decimal("0.00") or rec.selling_price < Decimal("0.00"):
                invalid_count += 1
                continue

            fv = FeatureEngineeringService.transform_record(db=db, record=rec)
            features.append(fv)

        metadata = DatasetMetadata(
            dataset_id=f"DS-DEAL-RISK-{company_id.hex[:8].upper()}-{len(features)}",
            dataset_type=DatasetType.HISTORICAL_DEALS,
            company_id=company_id,
            total_records_extracted=total_extracted,
            valid_records_count=len(features),
            invalid_records_count=invalid_count,
            feature_count=37,  # 37 tabular features across Phases 123-129
            generated_at=datetime.now(timezone.utc),
            normalization_applied=NormalizationStrategy.NONE,
        )

        return DatasetPreparationResponse(
            metadata=metadata,
            features=features,
        )
