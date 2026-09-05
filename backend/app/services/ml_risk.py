"""ML Risk Feature Engineering & Dataset Preparation Services (DealFlow360 B01: Phases 121–125).

Implements:
- Phase 121: ML Dataset Preparation (Data extraction, validation, missing value imputation, sanitization)
- Phase 122: Historical Deal Dataset (Point-in-time extraction from CustomerDealHistory & AppliedDiscount)
- Phase 123: Feature Engineering (Tabular feature transformation, numerical/categorical encoding, leakage safety)
- Phase 124: Discount Features (Ceiling utilization, deviation from customer baseline, risk indicators)
- Phase 125: Margin Features (Decimal-safe gross margin, post-discount compression, pressure ratios)

Strictly non-ML-training: provides the dataset & feature-engineering foundation for future Phase Group 09 models.
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
    DatasetMetadata,
    DatasetPreparationResponse,
    DatasetType,
    DiscountFeatures,
    EngineeredFeatureVector,
    MarginFeatures,
    NormalizationStrategy,
    RawDealRecord,
)
from app.services.discount_governance import DiscountPolicyEngine


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    """Safely quantize Decimal to specified decimal places."""
    fmt = Decimal("1." + "0" * places) if places > 0 else Decimal("1")
    return val.quantize(fmt, rounding=ROUND_HALF_UP)


# ==============================================================================
# Phase 125: Margin Features Engine
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
        """Compute margin features.
        
        Args:
            selling_price: Unit selling price (or total deal selling price)
            unit_cost: Unit cost (or total deal cost)
            discount_pct: Applied or requested discount percentage [0, 100]
        """
        # Sanitization & Boundaries
        safe_price = max(selling_price, Decimal("0.00"))
        safe_cost = max(unit_cost, Decimal("0.00"))
        safe_discount_pct = max(min(discount_pct, Decimal("100.00")), Decimal("0.00"))

        # Base Gross Margin
        gross_margin_amount = safe_price - safe_cost
        
        # Gross margin percentage
        if safe_price > Decimal("0.00"):
            gross_margin_pct = (gross_margin_amount / safe_price) * Decimal("100.00")
        else:
            gross_margin_pct = Decimal("0.00")

        # Discounted Selling Price
        discount_multiplier = (Decimal("100.00") - safe_discount_pct) / Decimal("100.00")
        discounted_price = quantize_dec(safe_price * discount_multiplier)

        # Margin After Discount
        discounted_margin_amount = discounted_price - safe_cost
        if discounted_price > Decimal("0.00"):
            discounted_margin_pct = (discounted_margin_amount / discounted_price) * Decimal("100.00")
        else:
            discounted_margin_pct = Decimal("0.00")

        # Margin Reduction Ratio (how much of the original margin is erased by discount)
        discount_amount = safe_price - discounted_price
        if gross_margin_amount > Decimal("0.00"):
            margin_reduction_ratio = discount_amount / gross_margin_amount
            discount_to_margin_pressure = discount_amount / gross_margin_amount
        else:
            # If original margin was zero or negative, pressure is maximum
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
# Phase 124: Discount Features Engine
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
        """Compute discount features."""
        safe_req_disc = max(min(requested_discount_pct, Decimal("100.00")), Decimal("0.00"))
        safe_ceiling = max(effective_ceiling_pct, Decimal("0.00"))
        safe_hist_avg = max(customer_historical_avg_pct, Decimal("0.00"))
        safe_tier_limit = max(tier_discount_limit, Decimal("0.00"))
        safe_deal_val = max(deal_value, Decimal("0.00"))

        # Ceiling Utilization Ratio (requested / ceiling)
        if safe_ceiling > Decimal("0.00"):
            ceiling_utilization_ratio = safe_req_disc / safe_ceiling
        else:
            ceiling_utilization_ratio = Decimal("1.00") if safe_req_disc > Decimal("0.00") else Decimal("0.00")

        is_ceiling_breached = safe_req_disc > safe_ceiling

        # Deviation from customer's historical average
        discount_deviation = safe_req_disc - safe_hist_avg

        # Tier utilization ratio
        if safe_tier_limit > Decimal("0.00"):
            tier_utilization_ratio = safe_req_disc / safe_tier_limit
        else:
            tier_utilization_ratio = Decimal("1.00") if safe_req_disc > Decimal("0.00") else Decimal("0.00")

        # Estimated absolute discount amount
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
# Phase 122: Historical Deal Dataset Extractor
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
        # 1. Fetch Company customers
        customers = db.scalars(
            select(Customer).where(Customer.company_id == company_id)
        ).all()
        customer_map = {c.id: c for c in customers}

        # 2. Fetch Customer Tiers
        tiers = db.scalars(select(CustomerTier)).all()
        tier_map = {t.id: t for t in tiers}

        # 3. Fetch Products for catalog lookups
        products = db.scalars(select(Product)).all()
        product_map = {p.id: p for p in products}

        # 4. Fetch Categories
        categories = db.scalars(select(ProductCategory)).all()
        cat_map = {c.id: c.code for c in categories}

        raw_records: List[RawDealRecord] = []
        seen_keys: Set[str] = set()

        # Query A: AppliedDiscount (Rich automated deal outcomes from Phase 120)
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

            # Compute prior purchase / discount / payment stats prior to ad.created_at (leakage-safe)
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

            deal_val = ad.selling_price  # base value
            raw_records.append(
                RawDealRecord(
                    record_id=record_id,
                    deal_reference=ad.deal_reference or f"DEAL-{ad.id.hex[:8].upper()}",
                    company_id=company_id,
                    customer_id=cust.id,
                    customer_code=cust.customer_code,
                    customer_tier=tier_code,
                    tier_discount_limit=tier_limit,
                    deal_value=deal_val,
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
                    inventory_signal="HEALTHY_STOCK",
                    deal_status="WON",
                    decision_outcome="APPROVED",
                    risk_level=ad.risk_level,
                    closed_at=ad.created_at,
                    created_at=ad.created_at,
                )
            )

        # Query B: CustomerDealHistory (Generic deal history from Phase 060)
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
                    requested_discount_pct=tier_limit,  # default to tier limit for historical deals without explicit request
                    applied_discount_pct=tier_limit,
                    product_id=None,
                    product_sku=None,
                    product_category="GENERAL",
                    unit_cost=quantize_dec(dh.deal_value * Decimal("0.70")),  # estimated benchmark cost
                    selling_price=dh.deal_value,
                    prior_purchases_count=prior_stats["purchases_count"],
                    prior_purchases_total=prior_stats["purchases_total"],
                    prior_discounts_count=prior_stats["discounts_count"],
                    prior_discount_avg_pct=prior_stats["discount_avg_pct"],
                    prior_payments_count=prior_stats["payments_count"],
                    prior_payments_total=prior_stats["payments_total"],
                    inventory_signal="HEALTHY_STOCK",
                    deal_status=dh.status,
                    decision_outcome="APPROVED" if dh.status == "WON" else "REJECTED",
                    risk_level="LOW" if dh.status == "WON" else "HIGH",
                    closed_at=dh.closed_date or dh.created_at,
                    created_at=dh.created_at,
                )
            )

        # Deterministic sort by created_at, then record_id
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
        # Prior purchases
        purchases = db.scalars(
            select(CustomerPurchaseHistory).where(
                CustomerPurchaseHistory.company_id == company_id,
                CustomerPurchaseHistory.customer_id == customer_id,
                CustomerPurchaseHistory.purchase_date < as_of,
            )
        ).all()
        purchases_count = len(purchases)
        purchases_total = sum((p.total_amount for p in purchases), Decimal("0.00"))

        # Prior discounts
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

        # Prior payments
        payments = db.scalars(
            select(CustomerPaymentHistory).where(
                CustomerPaymentHistory.company_id == company_id,
                CustomerPaymentHistory.customer_id == customer_id,
                CustomerPaymentHistory.created_at < as_of,
            )
        ).all()
        payments_count = len(payments)
        payments_total = sum((p.amount for p in payments), Decimal("0.00"))

        return {
            "purchases_count": purchases_count,
            "purchases_total": purchases_total,
            "discounts_count": discounts_count,
            "discount_avg_pct": quantize_dec(discount_avg_pct),
            "payments_count": payments_count,
            "payments_total": payments_total,
        }


# ==============================================================================
# Phase 123: Generic Feature Engineering Layer
# ==============================================================================

class FeatureEngineeringService:
    """Transforms raw point-in-time historical deal records into ML-ready tabular feature vectors (Phase 123)."""

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

        # 4. Numerical log transforms & tenure
        float_deal_val = float(record.deal_value)
        log_deal_val = math.log1p(max(float_deal_val, 0.0))

        customer = db.get(Customer, record.customer_id)
        if customer and customer.created_at:
            tenure_delta = (record.created_at - customer.created_at).days
            tenure_days = max(tenure_delta, 0)
        else:
            tenure_days = 0

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

        # Company config
        configs = db.scalars(
            select(DiscountConfiguration).where(
                DiscountConfiguration.company_id == company_id,
                DiscountConfiguration.is_active == True,
            )
        ).all()
        for cfg in configs:
            if cfg.effective_from <= at_timestamp and (cfg.effective_until is None or cfg.effective_until >= at_timestamp):
                candidate_ceilings.append(cfg.default_discount_ceiling)

        # Customer ceiling
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

        # Product ceiling
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
        return Decimal("15.00")  # Default conservative governance ceiling if unset


# ==============================================================================
# Phase 121: ML Dataset Preparation Orchestrator
# ==============================================================================

class MLDatasetPreparationService:
    """Deterministic orchestrator preparing datasets for downstream AI/ML Risk Engine (Phase 121)."""

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
        # 1. Extract raw records (Phase 122)
        raw_records = HistoricalDealDatasetExtractor.extract_records(
            db=db,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
        )

        total_extracted = len(raw_records)
        features: List[EngineeredFeatureVector] = []
        invalid_count = 0

        # 2. Validation & Transformation (Phase 121 + 123)
        for rec in raw_records:
            # Filter checks
            if min_deal_value and rec.deal_value < min_deal_value:
                invalid_count += 1
                continue
            if filter_status and rec.deal_status != filter_status:
                invalid_count += 1
                continue

            # Invalidation guards (e.g. corrupt or negative deal value)
            if rec.deal_value < Decimal("0.00") or rec.selling_price < Decimal("0.00"):
                invalid_count += 1
                continue

            # Engineer features
            fv = FeatureEngineeringService.transform_record(db=db, record=rec)
            features.append(fv)

        metadata = DatasetMetadata(
            dataset_id=f"DS-DEAL-RISK-{company_id.hex[:8].upper()}-{len(features)}",
            dataset_type=DatasetType.HISTORICAL_DEALS,
            company_id=company_id,
            total_records_extracted=total_extracted,
            valid_records_count=len(features),
            invalid_records_count=invalid_count,
            feature_count=21,  # 21 tabular numeric/categorical features in flat dict
            generated_at=datetime.now(timezone.utc),
            normalization_applied=NormalizationStrategy.NONE,
        )

        return DatasetPreparationResponse(
            metadata=metadata,
            features=features,
        )
