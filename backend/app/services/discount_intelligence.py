"""Discount Intelligence Engine & Analysis Services (DealFlow360 G23: Phases 111–115).

Implements deterministic discount intelligence:
- Phase 111: Recommended Discount Engine
- Phase 112: Maximum Safe Discount
- Phase 113: Margin Protection Engine
- Phase 114: Historical Discount Analysis
- Phase 115: Customer Discount Analysis

All calculations use strict Decimal precision and enforce multi-tenant company isolation.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.models.customer import Customer
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.product import Product
from app.models.user import User
from app.schemas.discount_intelligence import (
    CustomerDiscountAnalysisResponse,
    DiscountRecommendationRequest,
    DiscountRecommendationResponse,
    HistoricalDiscountAnalysisResponse,
    HistoricalDiscountSummary,
    MarginProtectionRequest,
    MarginProtectionResponse,
    MaximumSafeDiscountRequest,
    MaximumSafeDiscountResponse,
)
from app.services.discount_governance import DiscountPolicyEngine


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    """Helper to quantize Decimals cleanly to 2 decimal places."""
    fmt = Decimal("1." + "0" * places) if places > 0 else Decimal("1")
    return val.quantize(fmt, rounding=ROUND_HALF_UP)


# ==============================================================================
# Phase 113: Margin Protection Engine
# ==============================================================================

class MarginProtectionEngine:
    """Calculates gross margin erosion and computes the maximum discount allowed

    without breaching the required minimum profit margin.
    Uses strict Decimal arithmetic and handles all mathematical edge cases.
    """

    @classmethod
    def evaluate(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        selling_price_override: Optional[Decimal] = None,
        min_margin_percentage: Decimal = Decimal("15.00"),
    ) -> MarginProtectionResponse:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        price = Decimal(str(selling_price_override)) if selling_price_override is not None else Decimal(str(product.base_price))
        cost = Decimal(str(product.cost))
        min_margin = Decimal(str(min_margin_percentage))

        # Edge case 1: Selling price <= 0
        if price <= Decimal("0.00"):
            return MarginProtectionResponse(
                product_id=product_id,
                selling_price=Decimal("0.00"),
                unit_cost=cost,
                current_margin_percentage=Decimal("0.00"),
                protected_margin_percentage=min_margin,
                max_discount_from_margin=Decimal("0.00"),
                is_margin_preserved=False,
                reason_code="ZERO_OR_NEGATIVE_PRICE",
                reason_description="Selling price is zero or negative. No discount allowed.",
            )

        # Edge case 2: Cost >= Selling price (Current margin <= 0)
        if cost >= price:
            current_margin = quantize_dec(((price - cost) / price) * Decimal("100"))
            return MarginProtectionResponse(
                product_id=product_id,
                selling_price=quantize_dec(price),
                unit_cost=quantize_dec(cost),
                current_margin_percentage=current_margin,
                protected_margin_percentage=quantize_dec(min_margin),
                max_discount_from_margin=Decimal("0.00"),
                is_margin_preserved=False,
                reason_code="COST_EXCEEDS_PRICE",
                reason_description="Unit cost meets or exceeds base selling price. Margin is zero or negative; no discount permissible.",
            )

        current_margin = quantize_dec(((price - cost) / price) * Decimal("100"))

        # Edge case 3: Minimum required margin >= 100%
        if min_margin >= Decimal("100.00"):
            return MarginProtectionResponse(
                product_id=product_id,
                selling_price=quantize_dec(price),
                unit_cost=quantize_dec(cost),
                current_margin_percentage=current_margin,
                protected_margin_percentage=quantize_dec(min_margin),
                max_discount_from_margin=Decimal("0.00"),
                is_margin_preserved=False,
                reason_code="UNREALISTIC_MARGIN_REQUIREMENT",
                reason_description="Required minimum margin is 100% or higher. No discount permissible.",
            )

        # Formula derivation:
        # Discounted Price P' = P * (1 - d/100)
        # Margin M' = (P' - C) / P' >= min_margin / 100
        # 1 - C/P' >= min_margin / 100  =>  C/P' <= 1 - min_margin/100
        # P' >= C / (1 - min_margin/100)
        # P * (1 - d/100) >= C / (1 - min_margin/100)
        # 1 - d/100 >= C / (P * (1 - min_margin/100))
        # d/100 <= 1 - C / (P * (1 - min_margin/100))
        margin_factor = Decimal("1.0") - (min_margin / Decimal("100.0"))
        denom = price * margin_factor

        if denom <= Decimal("0.00"):
            max_discount = Decimal("0.00")
        else:
            calc_d = (Decimal("1.0") - (cost / denom)) * Decimal("100.0")
            max_discount = max(Decimal("0.00"), min(Decimal("100.00"), calc_d))

        max_discount = quantize_dec(max_discount)

        if max_discount <= Decimal("0.00"):
            return MarginProtectionResponse(
                product_id=product_id,
                selling_price=quantize_dec(price),
                unit_cost=quantize_dec(cost),
                current_margin_percentage=current_margin,
                protected_margin_percentage=quantize_dec(min_margin),
                max_discount_from_margin=Decimal("0.00"),
                is_margin_preserved=current_margin >= min_margin,
                reason_code="INSUFFICIENT_MARGIN_BUFFER",
                reason_description="Current profit margin is at or below required threshold; zero discount capacity without eroding margin.",
            )

        return MarginProtectionResponse(
            product_id=product_id,
            selling_price=quantize_dec(price),
            unit_cost=quantize_dec(cost),
            current_margin_percentage=current_margin,
            protected_margin_percentage=quantize_dec(min_margin),
            max_discount_from_margin=max_discount,
            is_margin_preserved=True,
            reason_code="SAFE_MARGIN",
            reason_description=f"Discount of up to {max_discount}% maintains minimum profit margin of {min_margin}%.",
        )


# ==============================================================================
# Phase 114: Historical Discount Analysis Service
# ==============================================================================

class DiscountHistoryAnalysisService:
    """Aggregates and analyzes historical discount performance for a company,

    customer, and/or product across historical transaction records.
    Strictly isolated by company_id.
    """

    @classmethod
    def analyze_history(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        product_id: Optional[uuid.UUID] = None,
    ) -> HistoricalDiscountAnalysisResponse:
        query = db.query(CustomerDiscountHistory).filter(CustomerDiscountHistory.company_id == company_id)

        if customer_id is not None:
            # Verify customer exists in company
            cust = db.query(Customer).filter(Customer.id == customer_id, Customer.company_id == company_id).first()
            if not cust:
                raise NotFoundError(f"Customer with id {customer_id} not found in this company.")
            query = query.filter(CustomerDiscountHistory.customer_id == customer_id)

        records = query.order_by(CustomerDiscountHistory.applied_at.desc()).all()
        sample_size = len(records)

        now = datetime.now(timezone.utc)

        if sample_size == 0:
            summary = HistoricalDiscountSummary(
                sample_size=0,
                average_discount=None,
                min_discount=None,
                max_discount=None,
                latest_discount=None,
                latest_applied_at=None,
                total_discount_amount=Decimal("0.00"),
            )
            return HistoricalDiscountAnalysisResponse(
                company_id=company_id,
                customer_id=customer_id,
                product_id=product_id,
                summary=summary,
                has_history=False,
                evaluated_at=now,
            )

        discounts = [Decimal(str(r.discount_percentage)) for r in records]
        amounts = [Decimal(str(r.discount_amount)) for r in records]

        avg_discount = quantize_dec(sum(discounts) / Decimal(str(sample_size)))
        min_disc = quantize_dec(min(discounts))
        max_disc = quantize_dec(max(discounts))
        latest_disc = quantize_dec(discounts[0])
        latest_date = records[0].applied_at
        total_amt = quantize_dec(sum(amounts))

        summary = HistoricalDiscountSummary(
            sample_size=sample_size,
            average_discount=avg_discount,
            min_discount=min_disc,
            max_discount=max_disc,
            latest_discount=latest_disc,
            latest_applied_at=latest_date,
            total_discount_amount=total_amt,
        )

        return HistoricalDiscountAnalysisResponse(
            company_id=company_id,
            customer_id=customer_id,
            product_id=product_id,
            summary=summary,
            has_history=True,
            evaluated_at=now,
        )


# ==============================================================================
# Phase 115: Customer Discount Analysis Service
# ==============================================================================

class CustomerDiscountAnalysisService:
    """Analyzes customer-specific discount history in the context of active

    governance ceilings and relationship profile.
    """

    @classmethod
    def analyze_customer(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> CustomerDiscountAnalysisResponse:
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id, Customer.company_id == company_id)
            .first()
        )
        if not customer:
            raise NotFoundError(f"Customer with id {customer_id} not found in this company.")

        # Historical discount performance
        hist_analysis = DiscountHistoryAnalysisService.analyze_history(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
        )
        summary = hist_analysis.summary

        # Active Customer Ceiling
        now = datetime.now(timezone.utc)
        active_ceiling_row = (
            db.query(CustomerDiscountCeiling)
            .filter(
                CustomerDiscountCeiling.company_id == company_id,
                CustomerDiscountCeiling.customer_id == customer_id,
                CustomerDiscountCeiling.is_active == True,
                CustomerDiscountCeiling.effective_from <= now,
            )
            .order_by(CustomerDiscountCeiling.created_at.desc())
            .first()
        )
        active_ceiling = (
            quantize_dec(Decimal(str(active_ceiling_row.max_discount_percentage)))
            if active_ceiling_row
            else None
        )

        # Compliance / Risk assessment
        if summary.sample_size == 0:
            compliance_rating = "NO_HISTORY"
            insight = "New customer or account with no recorded historical discount transactions."
        elif active_ceiling is not None and summary.average_discount and summary.average_discount >= active_ceiling * Decimal("0.85"):
            compliance_rating = "HIGH_DISCOUNT_CUSTOMER"
            insight = f"Customer averages {summary.average_discount}% discount, closely approaching active ceiling of {active_ceiling}%."
        else:
            compliance_rating = "COMPLIANT"
            avg_str = f"{summary.average_discount}%" if summary.average_discount is not None else "0%"
            insight = f"Customer historical average discount is {avg_str} with {summary.sample_size} recorded deals."

        tier_name = customer.tier.name if customer.tier else None

        return CustomerDiscountAnalysisResponse(
            customer_id=customer.id,
            customer_name=customer.name,
            customer_code=customer.customer_code,
            tier_name=tier_name,
            active_customer_ceiling=active_ceiling,
            history_summary=summary,
            compliance_rating=compliance_rating,
            insight_summary=insight,
            evaluated_at=now,
        )


# ==============================================================================
# Phase 112: Maximum Safe Discount Engine
# ==============================================================================

class MaximumSafeDiscountEngine:
    """Intersects governance ceilings, margin protection, and actor limits

    to deterministically establish the highest permissible and safe discount.
    """

    @classmethod
    def evaluate(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        product_id: uuid.UUID,
        actor: User,
        selling_price_override: Optional[Decimal] = None,
        min_margin_percentage: Decimal = Decimal("15.00"),
    ) -> MaximumSafeDiscountResponse:
        now = datetime.now(timezone.utc)

        # 1. Evaluate Governance Ceilings via G22 Policy Engine
        # We test with a dummy 0% proposed discount to obtain the authoritative effective_ceiling and actor_authority_limit
        policy_eval = DiscountPolicyEngine.evaluate(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
            product_id=product_id,
            proposed_discount=Decimal("0.00"),
            actor=actor,
        )
        governed_ceiling = quantize_dec(Decimal(str(policy_eval.effective_ceiling)))
        actor_limit = (
            quantize_dec(Decimal(str(policy_eval.actor_authority_limit)))
            if policy_eval.actor_authority_limit is not None
            else None
        )

        # 2. Evaluate Margin Ceiling via Phase 113 Margin Protection Engine
        margin_eval = MarginProtectionEngine.evaluate(
            db=db,
            company_id=company_id,
            product_id=product_id,
            selling_price_override=selling_price_override,
            min_margin_percentage=min_margin_percentage,
        )
        margin_ceiling = margin_eval.max_discount_from_margin

        # 3. Intersect bounds: min(governed_ceiling, margin_ceiling, actor_limit)
        bounds = [governed_ceiling, margin_ceiling]
        if actor_limit is not None:
            bounds.append(actor_limit)

        max_safe = min(bounds)
        max_safe = max(Decimal("0.00"), min(Decimal("100.00"), max_safe))
        max_safe = quantize_dec(max_safe)

        # 4. Determine primary limiting factor
        if max_safe == margin_ceiling and margin_ceiling < governed_ceiling:
            limiting_factor = "MARGIN_LIMIT"
        elif actor_limit is not None and max_safe == actor_limit and actor_limit < governed_ceiling:
            limiting_factor = "ACTOR_AUTHORITY"
        elif max_safe == governed_ceiling:
            limiting_factor = "GOVERNANCE_CEILING"
        else:
            limiting_factor = "NONE"

        breakdown = {
            "governed_ceiling": float(governed_ceiling),
            "margin_ceiling": float(margin_ceiling),
            "actor_authority_limit": float(actor_limit) if actor_limit is not None else None,
            "current_product_margin": float(margin_eval.current_margin_percentage),
            "protected_margin_required": float(margin_eval.protected_margin_percentage),
            "margin_reason": margin_eval.reason_code,
            "governance_policies": policy_eval.evaluated_policies,
        }

        return MaximumSafeDiscountResponse(
            customer_id=customer_id,
            product_id=product_id,
            max_safe_discount=max_safe,
            governed_ceiling=governed_ceiling,
            margin_ceiling=margin_ceiling,
            actor_authority_limit=actor_limit,
            limiting_factor=limiting_factor,
            evaluation_breakdown=breakdown,
            evaluated_at=now,
        )


# ==============================================================================
# Phase 111: Recommended Discount Engine
# ==============================================================================

class DiscountRecommendationEngine:
    """Generates an optimal, explainable, and fully compliant discount recommendation

    based on customer behavioral history, product economics, and governance ceilings.
    """

    @classmethod
    def recommend(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        product_id: uuid.UUID,
        actor: User,
        selling_price_override: Optional[Decimal] = None,
        min_margin_percentage: Decimal = Decimal("15.00"),
        benchmark_discount: Optional[Decimal] = None,
    ) -> DiscountRecommendationResponse:
        now = datetime.now(timezone.utc)

        # 1. Compute Maximum Safe Discount (Phases 112 & 113)
        safe_eval = MaximumSafeDiscountEngine.evaluate(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
            product_id=product_id,
            actor=actor,
            selling_price_override=selling_price_override,
            min_margin_percentage=min_margin_percentage,
        )
        max_safe = safe_eval.max_safe_discount

        # 2. Analyze Customer Discount History (Phases 114 & 115)
        hist_analysis = DiscountHistoryAnalysisService.analyze_history(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
        )
        customer_avg = hist_analysis.summary.average_discount

        # 3. Formulate Baseline Target
        if customer_avg is not None and hist_analysis.summary.sample_size > 0:
            target_discount = customer_avg
            target_source = "HISTORICAL_AVERAGE"
        elif benchmark_discount is not None:
            target_discount = Decimal(str(benchmark_discount))
            target_source = "USER_BENCHMARK"
        else:
            # Conservative default for accounts with no history: half of max safe or default 5%
            target_discount = min(Decimal("5.00"), max_safe * Decimal("0.50"))
            target_source = "CONSERVATIVE_DEFAULT"

        # 4. Clamp target to max_safe discount
        if max_safe <= Decimal("0.00"):
            recommended = Decimal("0.00")
            if safe_eval.limiting_factor == "MARGIN_LIMIT":
                reason_code = "MARGIN_CONSTRAINED"
                reason_summary = "Product unit cost/margin requirements strictly preclude any discount."
            else:
                reason_code = "CEILING_CONSTRAINED"
                reason_summary = "Governance policies or actor authority limit preclude granting any discount."
        elif target_discount > max_safe:
            recommended = max_safe
            reason_code = "MAX_SAFE_CLAMPED"
            reason_summary = (
                f"Recommended discount clamped to maximum safe limit of {max_safe}% "
                f"(restricted by {safe_eval.limiting_factor}). Target was {target_discount}% ({target_source})."
            )
        else:
            recommended = target_discount
            if target_source == "HISTORICAL_AVERAGE":
                reason_code = "HISTORICAL_ALIGNMENT"
                reason_summary = f"Recommended {recommended}% aligned with customer's historical average discount."
            elif target_source == "USER_BENCHMARK":
                reason_code = "DEFAULT_BENCHMARK"
                reason_summary = f"Recommended {recommended}% based on requested benchmark discount."
            else:
                reason_code = "DEFAULT_BENCHMARK"
                reason_summary = f"Recommended {recommended}% as conservative baseline for account without discount history."

        recommended = quantize_dec(recommended)

        details = {
            "target_discount": float(quantize_dec(target_discount)),
            "target_source": target_source,
            "max_safe_discount": float(max_safe),
            "limiting_factor": safe_eval.limiting_factor,
            "breakdown": safe_eval.evaluation_breakdown,
            "sample_size": hist_analysis.summary.sample_size,
        }

        return DiscountRecommendationResponse(
            customer_id=customer_id,
            product_id=product_id,
            recommended_discount=recommended,
            max_safe_discount=max_safe,
            governed_ceiling=safe_eval.governed_ceiling,
            margin_ceiling=safe_eval.margin_ceiling,
            customer_historical_avg=customer_avg,
            reason_code=reason_code,
            reason_summary=reason_summary,
            evaluation_details=details,
            evaluated_at=now,
        )
