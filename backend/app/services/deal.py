import math
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ApplicationError
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.deal import DealActivity, DealActivityType, DealProduct, DealStage
from app.models.product import Product
from app.models.quotation import Quotation, QuotationSendLog, QuotationStatus, QuotationVersion
from app.models.quotation_line_item import QuotationLineItem
from app.models.user import User
from app.schemas.deal import (
    DealActivityCreate,
    DealActivityResponse,
    DealDashboardResponse,
    DealDetailResponse,
    DealForecastResponse,
    DealMarginResponse,
    DealMarginRisk,
    DealProbabilityFactor,
    DealProbabilityResponse,
    DealProductCreate,
    DealProductResponse,
    DealSummaryResponse,
    DealTimelineEventResponse,
    PipelineForecastSummary,
    StageForecastItem,
)


def quantize_dec(val: Any) -> Decimal:
    """Consistently rounds monetary amounts to 2 decimal places using ROUND_HALF_UP."""
    if val is None:
        return Decimal("0.00")
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def quantize_qty(val: Any) -> Decimal:
    """Rounds quantities to 4 decimal places using ROUND_HALF_UP."""
    if val is None:
        return Decimal("0.0000")
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    return val.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


# ==============================================================================
# Phase 208: Deal Calculation Engine
# ==============================================================================

class DealCalculationEngine:
    """Centralized monetary and quantity calculation engine for deals (Phase 208).

    Enforces strict Decimal arithmetic and ROUND_HALF_UP precision.
    """

    @classmethod
    def calculate_line_metrics(
        cls,
        quantity: Decimal,
        unit_price: Decimal,
        unit_cost: Decimal,
        discount_percent: Decimal,
        tax_rate: Decimal,
    ) -> Dict[str, Decimal]:
        """Calculates subtotal, discounts, taxable base, taxes, total, and margin for a product line."""
        qty = quantize_qty(quantity)
        price = quantize_dec(unit_price)
        cost = quantize_dec(unit_cost)
        disc_pct = quantize_dec(discount_percent)
        t_rate = quantize_dec(tax_rate)

        subtotal = quantize_dec(qty * price)
        discount_amount = quantize_dec(subtotal * (disc_pct / Decimal("100.00")))
        taxable_amount = quantize_dec(subtotal - discount_amount)
        tax_amount = quantize_dec(taxable_amount * (t_rate / Decimal("100.00")))
        total_amount = quantize_dec(taxable_amount + tax_amount)
        total_cost = quantize_dec(qty * cost)
        gross_profit = quantize_dec(taxable_amount - total_cost)

        if taxable_amount > Decimal("0.00"):
            margin_pct = quantize_dec((gross_profit / taxable_amount) * Decimal("100.00"))
        elif total_amount == Decimal("0.00") and total_cost == Decimal("0.00"):
            margin_pct = Decimal("0.00")
        else:
            margin_pct = Decimal("-100.00") if gross_profit < Decimal("0.00") else Decimal("0.00")

        return {
            "quantity": qty,
            "unit_price": price,
            "unit_cost": cost,
            "discount_percent": disc_pct,
            "tax_rate": t_rate,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "taxable_amount": taxable_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "total_cost": total_cost,
            "gross_profit": gross_profit,
            "margin_percentage": margin_pct,
        }

    @classmethod
    def recalculate_deal_totals(cls, deal: CustomerDealHistory) -> None:
        """Aggregates all deal product line items into deal header totals."""
        if not deal.products:
            # If no products, preserve existing header values or initialize zeroes
            deal.subtotal = quantize_dec(deal.deal_value) if deal.deal_value > 0 else Decimal("0.00")
            deal.taxable_amount = deal.subtotal
            deal.expected_revenue = quantize_dec(deal.deal_value * Decimal(deal.probability) / Decimal("100.00"))
            return

        tot_subtotal = Decimal("0.00")
        tot_discount = Decimal("0.00")
        tot_taxable = Decimal("0.00")
        tot_tax = Decimal("0.00")
        tot_amount = Decimal("0.00")
        tot_cost = Decimal("0.00")

        for p in deal.products:
            tot_subtotal += p.subtotal
            tot_discount += p.discount_amount
            tot_taxable += p.taxable_amount
            tot_tax += p.tax_amount
            tot_amount += p.total_amount
            tot_cost += p.total_cost

        deal.subtotal = quantize_dec(tot_subtotal)
        deal.discount_amount = quantize_dec(tot_discount)
        deal.tax_amount = quantize_dec(tot_tax)
        deal.total_cost = quantize_dec(tot_cost)
        deal.deal_value = quantize_dec(tot_amount)

        # Discount percent calculation
        if deal.subtotal > Decimal("0.00"):
            deal.discount_percent = quantize_dec((deal.discount_amount / deal.subtotal) * Decimal("100.00"))
        else:
            deal.discount_percent = Decimal("0.00")

        # Gross profit & margin percentage
        taxable_base = quantize_dec(tot_taxable)
        gross_profit = quantize_dec(taxable_base - deal.total_cost)
        deal.gross_profit = gross_profit

        if taxable_base > Decimal("0.00"):
            deal.margin_percentage = quantize_dec((gross_profit / taxable_base) * Decimal("100.00"))
        elif deal.deal_value == Decimal("0.00") and deal.total_cost == Decimal("0.00"):
            deal.margin_percentage = Decimal("0.00")
        else:
            deal.margin_percentage = Decimal("-100.00") if gross_profit < Decimal("0.00") else Decimal("0.00")

        deal.expected_revenue = quantize_dec(deal.deal_value * Decimal(deal.probability) / Decimal("100.00"))
        deal.updated_at = datetime.now(timezone.utc)


# ==============================================================================
# Phase 209: Deal Margin Service
# ==============================================================================

class DealMarginService:
    """Centralized deal margin calculation and profit risk evaluation (Phase 209)."""

    @classmethod
    def evaluate_margin(cls, deal: CustomerDealHistory) -> DealMarginResponse:
        """Calculates exact gross margin, discounted margin, and risk classification."""
        revenue = deal.subtotal - deal.discount_amount  # Taxable base selling price
        if revenue < Decimal("0.00"):
            revenue = Decimal("0.00")

        cost = deal.total_cost
        profit = deal.gross_profit
        is_negative = profit < Decimal("0.00") or (revenue < cost and cost > Decimal("0.00"))

        # Gross margin percentage
        if revenue > Decimal("0.00"):
            gross_margin_pct = quantize_dec((profit / revenue) * Decimal("100.00"))
        else:
            gross_margin_pct = Decimal("-100.00") if cost > Decimal("0.00") else Decimal("0.00")

        # Discounted margin relative to list subtotal
        if deal.subtotal > Decimal("0.00"):
            discounted_margin_pct = quantize_dec((profit / deal.subtotal) * Decimal("100.00"))
        else:
            discounted_margin_pct = gross_margin_pct

        # Determine risk classification
        if is_negative or gross_margin_pct < Decimal("5.00"):
            margin_risk = DealMarginRisk.CRITICAL
        elif gross_margin_pct < Decimal("15.00"):
            margin_risk = DealMarginRisk.THIN
        elif gross_margin_pct < Decimal("25.00"):
            margin_risk = DealMarginRisk.MODERATE
        else:
            margin_risk = DealMarginRisk.HEALTHY

        return DealMarginResponse(
            deal_id=deal.id,
            deal_code=deal.deal_code,
            total_revenue=revenue,
            total_cost=cost,
            gross_profit=profit,
            gross_margin_percentage=gross_margin_pct,
            discounted_margin_percentage=discounted_margin_pct,
            margin_risk=margin_risk,
            is_negative_margin=is_negative,
        )


# ==============================================================================
# Phase 211: Deal Probability Service
# ==============================================================================

class DealProbabilityService:
    """Deterministic deal win probability engine (Phase 211).

    Scores deals from 0% to 100% using business signals: sales stage, customer profile,
    quotation acceptance, margin health, and sales activity recency.
    """

    STAGE_BASE_WEIGHTS = {
        DealStage.NEW.value: 10,
        DealStage.QUALIFIED.value: 25,
        DealStage.PROPOSAL.value: 50,
        DealStage.NEGOTIATION.value: 75,
        DealStage.CLOSED_WON.value: 100,
        DealStage.CLOSED_LOST.value: 0,
    }

    @classmethod
    def calculate_probability(
        cls,
        db: Session,
        deal: CustomerDealHistory,
    ) -> Tuple[int, List[DealProbabilityFactor], str]:
        """Calculates deterministic win probability [0, 100] with factor breakdown."""
        stage = deal.stage

        # Terminal stages have fixed deterministic probability
        if stage == DealStage.CLOSED_WON.value:
            factors = [DealProbabilityFactor(factor="STAGE_WON", impact_pct=100, description="Deal successfully closed and won.")]
            return 100, factors, "Deal is WON with guaranteed 100% closure."

        if stage == DealStage.CLOSED_LOST.value:
            factors = [DealProbabilityFactor(factor="STAGE_LOST", impact_pct=0, description="Deal marked closed-lost.")]
            return 0, factors, "Deal is LOST with 0% win probability."

        base_prob = cls.STAGE_BASE_WEIGHTS.get(stage, 25)
        factors = [
            DealProbabilityFactor(
                factor=f"STAGE_BASELINE_{stage}",
                impact_pct=base_prob,
                description=f"Baseline probability for {stage} pipeline stage.",
            )
        ]
        score = base_prob

        # 1. Quotation Linkage Signal
        if deal.quotation_id:
            quote = db.execute(select(Quotation).where(Quotation.id == deal.quotation_id)).scalar_one_or_none()
            if quote:
                if quote.status == QuotationStatus.ACCEPTED.value:
                    score += 15
                    factors.append(DealProbabilityFactor(factor="QUOTE_ACCEPTED", impact_pct=15, description="Commercial quotation counter-signed and accepted."))
                elif quote.status == QuotationStatus.APPROVED.value:
                    score += 10
                    factors.append(DealProbabilityFactor(factor="QUOTE_APPROVED", impact_pct=10, description="Quotation internally approved and ready for signing."))
                elif quote.status in (QuotationStatus.SENT.value, QuotationStatus.VIEWED.value):
                    score += 5
                    factors.append(DealProbabilityFactor(factor="QUOTE_ACTIVE", impact_pct=5, description="Quotation dispatched and viewed by client."))
                elif quote.status == QuotationStatus.REJECTED.value:
                    score -= 20
                    factors.append(DealProbabilityFactor(factor="QUOTE_REJECTED", impact_pct=-20, description="Quotation declined by client."))

        # 2. Customer Relationship & Tier Signal
        customer = db.execute(select(Customer).where(Customer.id == deal.customer_id)).scalar_one_or_none()
        if customer and customer.tier:
            t_name = customer.tier.name.upper()
            if "PLATINUM" in t_name or "ENTERPRISE" in t_name:
                score += 10
                factors.append(DealProbabilityFactor(factor="CUSTOMER_TIER_PLATINUM", impact_pct=10, description="Strategic enterprise tier account with high conversion velocity."))
            elif "GOLD" in t_name:
                score += 5
                factors.append(DealProbabilityFactor(factor="CUSTOMER_TIER_GOLD", impact_pct=5, description="Established gold tier account."))

        # 3. Margin & Deal Quality Signal
        margin = deal.margin_percentage
        if margin >= Decimal("30.00"):
            score += 5
            factors.append(DealProbabilityFactor(factor="MARGIN_HEALTHY", impact_pct=5, description="High commercial margin (>30%) provides negotiation flexibility."))
        elif margin < Decimal("10.00") and margin > Decimal("0.00"):
            score -= 5
            factors.append(DealProbabilityFactor(factor="MARGIN_THIN", impact_pct=-5, description="Thin margin (<10%) increases deal attrition risk."))
        elif margin <= Decimal("0.00"):
            score -= 15
            factors.append(DealProbabilityFactor(factor="MARGIN_NEGATIVE", impact_pct=-15, description="Negative profitability compromises commercial feasibility."))

        # 4. Activity Recency Signal
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        recent_count = db.execute(
            select(func.count(DealActivity.id))
            .where(DealActivity.deal_id == deal.id, DealActivity.created_at >= recent_cutoff)
        ).scalar() or 0

        if recent_count >= 2:
            score += 5
            factors.append(DealProbabilityFactor(factor="ACTIVITY_RECENT", impact_pct=5, description="Active sales engagement in the last 14 days."))
        elif recent_count == 0 and stage in (DealStage.PROPOSAL.value, DealStage.NEGOTIATION.value):
            stale_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            stale = deal.updated_at < stale_cutoff if deal.updated_at else False
            if stale:
                score -= 10
                factors.append(DealProbabilityFactor(factor="ACTIVITY_STALE", impact_pct=-10, description="No deal activity logged in over 30 days."))

        # Clamp strictly between 0 and 100
        final_probability = max(0, min(100, score))
        explanation = f"Calculated probability of {final_probability}% based on stage {stage} and {len(factors)} commercial signals."
        return final_probability, factors, explanation


# ==============================================================================
# Phase 210: Deal Stage Management Service
# ==============================================================================

class DealStageManagementService:
    """Centralized lifecycle stage machine for commercial deals (Phase 210)."""

    ALLOWED_TRANSITIONS = {
        DealStage.NEW.value: [DealStage.QUALIFIED.value, DealStage.CLOSED_LOST.value],
        DealStage.QUALIFIED.value: [DealStage.PROPOSAL.value, DealStage.NEW.value, DealStage.CLOSED_LOST.value],
        DealStage.PROPOSAL.value: [DealStage.NEGOTIATION.value, DealStage.QUALIFIED.value, DealStage.CLOSED_LOST.value],
        DealStage.NEGOTIATION.value: [DealStage.CLOSED_WON.value, DealStage.PROPOSAL.value, DealStage.CLOSED_LOST.value],
        DealStage.CLOSED_WON.value: [],   # Terminal state
        DealStage.CLOSED_LOST.value: [DealStage.NEW.value],  # Reopen to new only
    }

    @classmethod
    def update_stage(
        cls,
        db: Session,
        deal: CustomerDealHistory,
        target_stage: DealStage,
        actor: User,
        reason: Optional[str] = None,
    ) -> CustomerDealHistory:
        """Transitions deal stage, enforces valid paths, logs audit, and updates probability."""
        current_stage = deal.stage
        new_stage = target_stage.value

        if current_stage == new_stage:
            return deal  # Idempotent

        # Terminal state guard
        if current_stage == DealStage.CLOSED_WON.value:
            raise ApplicationError("Cannot transition a CLOSED_WON deal. It is in an immutable terminal state.", status_code=400)

        # Validate allowed progression
        allowed = cls.ALLOWED_TRANSITIONS.get(current_stage, [])
        if new_stage not in allowed:
            raise ApplicationError(
                f"Invalid deal stage transition from '{current_stage}' to '{new_stage}'. Allowed transitions: {allowed}",
                status_code=400,
            )

        now = datetime.now(timezone.utc)
        prev_stage = current_stage
        deal.stage = new_stage
        deal.updated_at = now

        # Handle terminal outcomes
        if new_stage == DealStage.CLOSED_WON.value:
            deal.status = "WON"
            deal.closed_date = now
            deal.probability = 100
        elif new_stage == DealStage.CLOSED_LOST.value:
            deal.status = "LOST"
            deal.closed_date = now
            deal.probability = 0
        else:
            deal.status = "OPEN"
            # Recalculate deterministic probability
            prob, _, _ = DealProbabilityService.calculate_probability(db, deal)
            deal.probability = prob

        # Recalculate expected revenue
        deal.expected_revenue = quantize_dec(deal.deal_value * Decimal(deal.probability) / Decimal("100.00"))

        # Log Deal Activity (Phase 213)
        activity_title = f"Stage changed to {new_stage}"
        activity_desc = reason or f"Deal progressed from {prev_stage} to {new_stage}."
        act = DealActivity(
            deal_id=deal.id,
            company_id=deal.company_id,
            actor_id=actor.id,
            activity_type=DealActivityType.STAGE_CHANGE.value,
            title=activity_title,
            description=activity_desc,
            activity_metadata={
                "previous_stage": prev_stage,
                "new_stage": new_stage,
                "probability": deal.probability,
            },
        )
        db.add(act)

        # System Audit Log
        audit = AuditLog(
            user_id=actor.id,
            company_id=deal.company_id,
            action=f"DEAL_STAGE_CHANGED_{new_stage}",
            resource_type="deal",
            resource_id=str(deal.id),
            details=f"Deal {deal.deal_code} stage changed from {prev_stage} to {new_stage}.",
            context_metadata={
                "deal_code": deal.deal_code,
                "previous_stage": prev_stage,
                "new_stage": new_stage,
                "reason": reason,
            },
        )
        db.add(audit)
        db.flush()
        return deal


# ==============================================================================
# Phase 207: Deal Product Service
# ==============================================================================

class DealProductService:
    """Manages explicit product line items linked to commercial deals (Phase 207)."""

    @classmethod
    def add_product_to_deal(
        cls,
        db: Session,
        company_id: uuid.UUID,
        deal_id: uuid.UUID,
        payload: DealProductCreate,
        actor: User,
    ) -> DealProduct:
        """Links a product to a deal, performs Decimal calculation, and recalculates totals."""
        deal = db.execute(
            select(CustomerDealHistory)
            .where(CustomerDealHistory.id == deal_id, CustomerDealHistory.company_id == company_id)
            .options(selectinload(CustomerDealHistory.products))
        ).scalar_one_or_none()

        if not deal:
            raise ApplicationError(f"Deal {deal_id} not found in company scope.", status_code=404)

        if deal.stage in (DealStage.CLOSED_WON.value, DealStage.CLOSED_LOST.value):
            raise ApplicationError(f"Cannot modify products on a closed deal in stage '{deal.stage}'.", status_code=400)

        # Verify product exists in tenant scope
        product = db.execute(
            select(Product).where(Product.id == payload.product_id)
        ).scalar_one_or_none()

        if not product:
            raise ApplicationError(f"Product {payload.product_id} does not exist.", status_code=404)

        if not product.is_active:
            raise ApplicationError(f"Cannot add inactive product '{product.name}' to deal.", status_code=400)

        # Duplicate product linking prevention
        existing = db.execute(
            select(DealProduct).where(DealProduct.deal_id == deal_id, DealProduct.product_id == payload.product_id)
        ).scalar_one_or_none()

        if existing:
            raise ApplicationError(f"Product '{product.name}' is already linked to this deal. Modify quantity instead.", status_code=400)

        # Resolve unit price, cost, discounts, taxes
        unit_price = payload.unit_price if payload.unit_price is not None else product.base_price
        unit_cost = product.cost
        disc_pct = payload.discount_percent if payload.discount_percent is not None else Decimal("0.00")
        tax_rate = payload.tax_rate if payload.tax_rate is not None else product.tax_rate

        metrics = DealCalculationEngine.calculate_line_metrics(
            quantity=payload.quantity,
            unit_price=unit_price,
            unit_cost=unit_cost,
            discount_percent=disc_pct,
            tax_rate=tax_rate,
        )

        dp = DealProduct(
            deal_id=deal.id,
            company_id=company_id,
            product_id=product.id,
            quantity=metrics["quantity"],
            unit_price=metrics["unit_price"],
            unit_cost=metrics["unit_cost"],
            discount_percent=metrics["discount_percent"],
            tax_rate=metrics["tax_rate"],
            subtotal=metrics["subtotal"],
            discount_amount=metrics["discount_amount"],
            taxable_amount=metrics["taxable_amount"],
            tax_amount=metrics["tax_amount"],
            total_amount=metrics["total_amount"],
            total_cost=metrics["total_cost"],
            gross_profit=metrics["gross_profit"],
            margin_percentage=metrics["margin_percentage"],
            notes=payload.notes,
        )
        db.add(dp)
        db.flush()

        # Recalculate deal header totals
        db.refresh(deal)
        DealCalculationEngine.recalculate_deal_totals(deal)

        # Log activity
        act = DealActivity(
            deal_id=deal.id,
            company_id=company_id,
            actor_id=actor.id,
            activity_type=DealActivityType.NOTE.value,
            title=f"Added Product: {product.name}",
            description=f"Added {dp.quantity:.2f} units of '{product.name}' at ${dp.unit_price:.2f}/unit (Total: ${dp.total_amount:.2f}).",
            activity_metadata={"product_id": str(product.id), "total_amount": str(dp.total_amount)},
        )
        db.add(act)
        db.flush()
        return dp


# ==============================================================================
# Phase 212: Deal Forecasting Service
# ==============================================================================

class DealForecastingService:
    """Weighted revenue and pipeline forecasting service (Phase 212)."""

    @classmethod
    def get_deal_forecast(cls, deal: CustomerDealHistory) -> DealForecastResponse:
        """Calculates individual deal expected revenue and weighted pipeline contribution."""
        weighted = quantize_dec(deal.deal_value * Decimal(deal.probability) / Decimal("100.00"))
        return DealForecastResponse(
            deal_id=deal.id,
            deal_code=deal.deal_code,
            deal_value=deal.deal_value,
            probability=deal.probability,
            weighted_value=weighted,
            stage=deal.stage,
            status=deal.status,
        )

    @classmethod
    def get_pipeline_forecast(cls, db: Session, company_id: uuid.UUID) -> PipelineForecastSummary:
        """Aggregates company pipeline revenue, weighted pipeline, and stage breakdowns."""
        deals = db.execute(
            select(CustomerDealHistory).where(CustomerDealHistory.company_id == company_id)
        ).scalars().all()

        stage_map: Dict[str, Dict[str, Any]] = {
            s.value: {"stage": s.value, "count": 0, "total": Decimal("0.00"), "weighted": Decimal("0.00")}
            for s in DealStage
        }

        tot_deals = len(deals)
        open_deals = 0
        won_deals = 0
        lost_deals = 0
        pipeline_val = Decimal("0.00")
        weighted_pipeline_val = Decimal("0.00")
        won_revenue = Decimal("0.00")
        lost_val = Decimal("0.00")

        for d in deals:
            stg = d.stage if d.stage in stage_map else DealStage.NEW.value
            val = quantize_dec(d.deal_value)
            prob = d.probability
            w_val = quantize_dec(val * Decimal(prob) / Decimal("100.00"))

            stage_map[stg]["count"] += 1
            stage_map[stg]["total"] += val
            stage_map[stg]["weighted"] += w_val

            if stg == DealStage.CLOSED_WON.value:
                won_deals += 1
                won_revenue += val
            elif stg == DealStage.CLOSED_LOST.value:
                lost_deals += 1
                lost_val += val
            else:
                open_deals += 1
                pipeline_val += val
                weighted_pipeline_val += w_val

        expected_revenue = quantize_dec(weighted_pipeline_val + won_revenue)

        stage_items = [
            StageForecastItem(
                stage=s["stage"],
                deal_count=s["count"],
                total_value=quantize_dec(s["total"]),
                weighted_value=quantize_dec(s["weighted"]),
            )
            for s in stage_map.values()
        ]

        return PipelineForecastSummary(
            total_deals_count=tot_deals,
            open_deals_count=open_deals,
            won_deals_count=won_deals,
            lost_deals_count=lost_deals,
            pipeline_value=quantize_dec(pipeline_val),
            weighted_pipeline_value=quantize_dec(weighted_pipeline_val),
            expected_revenue=expected_revenue,
            won_revenue=quantize_dec(won_revenue),
            lost_value=quantize_dec(lost_val),
            stages=stage_items,
        )


# ==============================================================================
# Phase 213: Deal Activity Service
# ==============================================================================

class DealActivityService:
    """Manages append-only activity tracking for commercial deals (Phase 213)."""

    @classmethod
    def record_activity(
        cls,
        db: Session,
        company_id: uuid.UUID,
        deal_id: uuid.UUID,
        payload: DealActivityCreate,
        actor: User,
    ) -> DealActivity:
        """Records an explicit sales interaction or note against a deal."""
        deal = db.execute(
            select(CustomerDealHistory).where(CustomerDealHistory.id == deal_id, CustomerDealHistory.company_id == company_id)
        ).scalar_one_or_none()

        if not deal:
            raise ApplicationError(f"Deal {deal_id} not found in company scope.", status_code=404)

        act = DealActivity(
            deal_id=deal.id,
            company_id=company_id,
            actor_id=actor.id,
            activity_type=payload.activity_type.value,
            title=payload.title,
            description=payload.description,
            activity_metadata=payload.activity_metadata,
        )
        db.add(act)
        db.flush()
        return act

    @classmethod
    def list_activities(
        cls,
        db: Session,
        company_id: uuid.UUID,
        deal_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DealActivity]:
        """Lists activities for a deal in reverse chronological order."""
        return db.execute(
            select(DealActivity)
            .where(DealActivity.deal_id == deal_id, DealActivity.company_id == company_id)
            .order_by(DealActivity.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()


# ==============================================================================
# Phase 214: Deal Timeline Service
# ==============================================================================

class DealTimelineService:
    """Unifies deal, quotation, approval, and activity events into a chronological stream (Phase 214)."""

    @classmethod
    def get_timeline(
        cls,
        db: Session,
        company_id: uuid.UUID,
        deal_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DealTimelineEventResponse]:
        """Aggregates and sorts all deal-related events into a chronological timeline."""
        deal = db.execute(
            select(CustomerDealHistory)
            .where(CustomerDealHistory.id == deal_id, CustomerDealHistory.company_id == company_id)
            .options(
                selectinload(CustomerDealHistory.activities),
                selectinload(CustomerDealHistory.quotation),
            )
        ).scalar_one_or_none()

        if not deal:
            raise ApplicationError(f"Deal {deal_id} not found in company scope.", status_code=404)

        events: List[DealTimelineEventResponse] = []

        # 1. Deal Creation Event
        events.append(
            DealTimelineEventResponse(
                event_id=f"deal-create-{deal.id}",
                source="DEAL",
                event_type="DEAL_CREATED",
                title=f"Deal Created: {deal.title}",
                description=f"Initial deal value ${deal.deal_value:.2f} in stage {deal.stage}.",
                actor_name=deal.sales_rep_name,
                timestamp=deal.created_at,
                metadata={"deal_code": deal.deal_code, "deal_value": str(deal.deal_value)},
            )
        )

        # 2. Deal Activities
        for act in deal.activities:
            actor_name = f"{act.actor.first_name} {act.actor.last_name}".strip() if act.actor else "System"
            events.append(
                DealTimelineEventResponse(
                    event_id=f"activity-{act.id}",
                    source="ACTIVITY",
                    event_type=act.activity_type,
                    title=act.title,
                    description=act.description,
                    actor_name=actor_name,
                    timestamp=act.created_at,
                    metadata=act.activity_metadata,
                )
            )

        # 3. Quotation Lineage Events (if originated from or linked to quotation)
        if deal.quotation_id and deal.quotation:
            quote = deal.quotation
            events.append(
                DealTimelineEventResponse(
                    event_id=f"quote-create-{quote.id}",
                    source="QUOTATION",
                    event_type="QUOTATION_CREATED",
                    title=f"Originated from Quotation {quote.quotation_number}",
                    description=f"Quotation v{quote.version_number} with gross subtotal ${quote.subtotal:.2f}.",
                    actor_name=f"{quote.user.first_name} {quote.user.last_name}".strip() if quote.user else "Sales Rep",
                    timestamp=quote.created_at,
                    metadata={"quotation_number": quote.quotation_number, "status": quote.status},
                )
            )

            # Send logs
            for s_log in quote.send_logs:
                events.append(
                    DealTimelineEventResponse(
                        event_id=f"quote-send-{s_log.id}",
                        source="QUOTATION",
                        event_type="QUOTE_SENT",
                        title=f"Quote Emailed to {s_log.recipient_email}",
                        description=f"Quotation proposal emailed with status '{s_log.delivery_status}'.",
                        actor_name=s_log.sender.email if s_log.sender else "System",
                        timestamp=s_log.sent_at,
                        metadata={"delivery_status": s_log.delivery_status},
                    )
                )
                if s_log.viewed_at:
                    events.append(
                        DealTimelineEventResponse(
                            event_id=f"quote-view-{s_log.id}",
                            source="QUOTATION",
                            event_type="QUOTE_VIEWED",
                            title=f"Quote Viewed by {s_log.recipient_email}",
                            description=f"Client opened quotation proposal online.",
                            actor_name="Client",
                            timestamp=s_log.viewed_at,
                            metadata={"tracking_token": s_log.tracking_token},
                        )
                    )

            # Acceptance
            if quote.accepted_at:
                events.append(
                    DealTimelineEventResponse(
                        event_id=f"quote-accept-{quote.id}",
                        source="QUOTATION",
                        event_type="QUOTE_ACCEPTED",
                        title=f"Quotation Accepted",
                        description=quote.acceptance_notes or "Quotation formally accepted by customer.",
                        actor_name=quote.accepted_by.email if quote.accepted_by else "Customer",
                        timestamp=quote.accepted_at,
                        metadata={"accepted_notes": quote.acceptance_notes},
                    )
                )

        # Sort chronologically descending
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[offset : offset + limit]


# ==============================================================================
# Phase 206: Deal Creation from Quote Service
# ==============================================================================

class DealCreationService:
    """Atomic transactional conversion of commercial quotations into deals (Phase 206)."""

    @classmethod
    def create_from_quote(
        cls,
        db: Session,
        company_id: uuid.UUID,
        quotation_id: uuid.UUID,
        actor: User,
        title_override: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> CustomerDealHistory:
        """Validates acceptance and transactional conversion of quote into CustomerDealHistory and DealProducts."""
        # 1. Fetch quotation
        quotation = db.execute(
            select(Quotation)
            .where(Quotation.id == quotation_id, Quotation.company_id == company_id)
            .options(
                selectinload(Quotation.line_items).selectinload(QuotationLineItem.product),
                selectinload(Quotation.customer),
                selectinload(Quotation.converted_deal),
            )
        ).scalar_one_or_none()

        if not quotation:
            raise ApplicationError(f"Quotation {quotation_id} not found in company scope.", status_code=404)

        # 2. Idempotency: Return existing converted deal if already converted
        if quotation.status == QuotationStatus.CONVERTED.value:
            if quotation.converted_deal:
                return quotation.converted_deal
            # If pointer missing, search by quotation_id
            existing_deal = db.execute(
                select(CustomerDealHistory).where(CustomerDealHistory.quotation_id == quotation.id)
            ).scalar_one_or_none()
            if existing_deal:
                return existing_deal

        # 3. Status Guard: Must be ACCEPTED
        if quotation.status != QuotationStatus.ACCEPTED.value:
            raise ApplicationError(
                f"Quotation must be in ACCEPTED status to convert to a deal. Current status is '{quotation.status}'.",
                status_code=400,
            )

        # Expiration guard
        now = datetime.now(timezone.utc)
        if quotation.valid_until and quotation.valid_until < now:
            quotation.status = QuotationStatus.EXPIRED.value
            db.flush()
            raise ApplicationError(f"Quotation {quotation.quotation_number} has expired and cannot be converted.", status_code=400)

        # 4. Formulate Deal Header
        deal_code = f"DEAL-{quotation.quotation_number}"
        title = title_override or f"Commercial Deal - {quotation.quotation_number}"
        sales_rep = f"{actor.first_name} {actor.last_name}".strip() if (actor.first_name or actor.last_name) else actor.email

        deal = CustomerDealHistory(
            company_id=company_id,
            customer_id=quotation.customer_id,
            deal_code=deal_code,
            title=title,
            deal_value=quotation.total_amount,
            status="WON",
            stage=DealStage.CLOSED_WON.value,
            sales_rep_name=sales_rep,
            owner_id=actor.id,
            quotation_id=quotation.id,
            quotation_version=quotation.version_number,
            subtotal=quotation.subtotal,
            discount_amount=quotation.total_discount,
            discount_percent=quotation.overall_discount_percent,
            tax_amount=quotation.tax_amount,
            total_cost=quotation.total_cost,
            gross_profit=quotation.gross_profit,
            margin_percentage=quotation.margin_percentage,
            probability=100,
            expected_revenue=quotation.total_amount,
            closed_date=now,
            notes=notes or f"Converted from Quotation {quotation.quotation_number} (v{quotation.version_number}).",
        )
        db.add(deal)
        db.flush()

        # 5. Populate DealProduct line items (Phase 207)
        for li in quotation.line_items:
            unit_c = li.product.cost if li.product else Decimal("0.00")
            metrics = DealCalculationEngine.calculate_line_metrics(
                quantity=li.quantity,
                unit_price=li.unit_price,
                unit_cost=unit_c,
                discount_percent=li.discount_percent,
                tax_rate=li.tax_rate,
            )
            dp = DealProduct(
                deal_id=deal.id,
                company_id=company_id,
                product_id=li.product_id,
                quotation_line_item_id=li.id,
                quantity=metrics["quantity"],
                unit_price=metrics["unit_price"],
                unit_cost=metrics["unit_cost"],
                discount_percent=metrics["discount_percent"],
                tax_rate=metrics["tax_rate"],
                subtotal=metrics["subtotal"],
                discount_amount=metrics["discount_amount"],
                taxable_amount=metrics["taxable_amount"],
                tax_amount=metrics["tax_amount"],
                total_amount=metrics["total_amount"],
                total_cost=metrics["total_cost"],
                gross_profit=metrics["gross_profit"],
                margin_percentage=metrics["margin_percentage"],
                notes=li.notes,
            )
            db.add(dp)

        # 6. Update Quotation state
        quotation.converted_deal_id = deal.id
        quotation.converted_at = now
        quotation.status = QuotationStatus.CONVERTED.value
        quotation.updated_at = now

        # 7. Record Conversion Activity & Audit Log
        act = DealActivity(
            deal_id=deal.id,
            company_id=company_id,
            actor_id=actor.id,
            activity_type=DealActivityType.STAGE_CHANGE.value,
            title="Deal Won & Converted from Quote",
            description=f"Successfully converted accepted quotation {quotation.quotation_number} to deal {deal.deal_code}.",
            activity_metadata={
                "quotation_number": quotation.quotation_number,
                "version": quotation.version_number,
                "total_amount": str(deal.deal_value),
            },
        )
        db.add(act)

        audit = AuditLog(
            user_id=actor.id,
            company_id=company_id,
            action="DEAL_CONVERTED_FROM_QUOTE",
            resource_type="deal",
            resource_id=str(deal.id),
            details=f"Quotation {quotation.quotation_number} converted into Deal {deal.deal_code}.",
            context_metadata={
                "deal_code": deal.deal_code,
                "quotation_number": quotation.quotation_number,
                "deal_value": str(deal.deal_value),
            },
        )
        db.add(audit)
        db.flush()
        return deal


# ==============================================================================
# Phase 215: Deal Dashboard Service
# ==============================================================================

class DealDashboardService:
    """High-performance KPI and pipeline aggregation engine for deals (Phase 215)."""

    @classmethod
    def get_dashboard_summary(cls, db: Session, company_id: uuid.UUID) -> DealDashboardResponse:
        """Calculates executive deal metrics, win rate, stage breakdown, and recent activity."""
        # Query deals in company scope
        deals = db.execute(
            select(CustomerDealHistory)
            .where(CustomerDealHistory.company_id == company_id)
            .options(selectinload(CustomerDealHistory.customer))
            .order_by(CustomerDealHistory.deal_value.desc())
        ).scalars().all()

        tot_deals = len(deals)
        open_deals = 0
        won_deals = 0
        lost_deals = 0
        pipeline_val = Decimal("0.00")
        weighted_pipeline_val = Decimal("0.00")
        won_val = Decimal("0.00")
        total_val = Decimal("0.00")

        stage_dist: Dict[str, Dict[str, Any]] = {
            s.value: {"stage": s.value, "count": 0, "total": Decimal("0.00"), "weighted": Decimal("0.00")}
            for s in DealStage
        }

        for d in deals:
            stg = d.stage if d.stage in stage_dist else DealStage.NEW.value
            val = quantize_dec(d.deal_value)
            prob = d.probability
            w_val = quantize_dec(val * Decimal(prob) / Decimal("100.00"))

            total_val += val
            stage_dist[stg]["count"] += 1
            stage_dist[stg]["total"] += val
            stage_dist[stg]["weighted"] += w_val

            if stg == DealStage.CLOSED_WON.value:
                won_deals += 1
                won_val += val
            elif stg == DealStage.CLOSED_LOST.value:
                lost_deals += 1
            else:
                open_deals += 1
                pipeline_val += val
                weighted_pipeline_val += w_val

        # Win Rate: won / (won + lost)
        closed_total = won_deals + lost_deals
        win_rate = round((won_deals / closed_total * 100.0), 2) if closed_total > 0 else 0.0
        avg_val = quantize_dec(total_val / Decimal(tot_deals)) if tot_deals > 0 else Decimal("0.00")
        expected_revenue = quantize_dec(weighted_pipeline_val + won_val)

        # Recent activities
        recent_acts = db.execute(
            select(DealActivity)
            .where(DealActivity.company_id == company_id)
            .order_by(DealActivity.created_at.desc())
            .limit(10)
        ).scalars().all()

        top_deal_dtos: List[DealSummaryResponse] = []
        for d in deals[:10]:
            top_deal_dtos.append(
                DealSummaryResponse(
                    id=d.id,
                    company_id=d.company_id,
                    customer_id=d.customer_id,
                    customer_name=d.customer.name if d.customer else None,
                    deal_code=d.deal_code,
                    title=d.title,
                    deal_value=d.deal_value,
                    status=d.status,
                    stage=d.stage,
                    sales_rep_name=d.sales_rep_name,
                    owner_id=d.owner_id,
                    quotation_id=d.quotation_id,
                    quotation_version=d.quotation_version,
                    probability=d.probability,
                    expected_revenue=d.expected_revenue,
                    gross_profit=d.gross_profit,
                    margin_percentage=d.margin_percentage,
                    closed_date=d.closed_date,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                )
            )

        stage_items = [
            StageForecastItem(
                stage=s["stage"],
                deal_count=s["count"],
                total_value=quantize_dec(s["total"]),
                weighted_value=quantize_dec(s["weighted"]),
            )
            for s in stage_dist.values()
        ]

        recent_act_dtos = [
            DealActivityResponse(
                id=a.id,
                deal_id=a.deal_id,
                activity_type=a.activity_type,
                title=a.title,
                description=a.description,
                actor_id=a.actor_id,
                actor_name=a.actor.email if a.actor else None,
                activity_metadata=a.activity_metadata,
                created_at=a.created_at,
            )
            for a in recent_acts
        ]

        return DealDashboardResponse(
            total_deals=tot_deals,
            open_deals=open_deals,
            won_deals=won_deals,
            lost_deals=lost_deals,
            pipeline_value=quantize_dec(pipeline_val),
            weighted_pipeline=quantize_dec(weighted_pipeline_val),
            expected_revenue=expected_revenue,
            average_deal_value=avg_val,
            win_rate=win_rate,
            deals_by_stage=stage_items,
            recent_activities=recent_act_dtos,
            top_deals=top_deal_dtos,
        )


# ==============================================================================
# Deal Orchestration Service
# ==============================================================================

class DealService:
    """Orchestration service for deal query, retrieval, and recalculation."""

    @classmethod
    def to_deal_summary(cls, d: CustomerDealHistory) -> DealSummaryResponse:
        return DealSummaryResponse(
            id=d.id,
            company_id=d.company_id,
            customer_id=d.customer_id,
            customer_name=d.customer.name if d.customer else None,
            deal_code=d.deal_code,
            title=d.title,
            deal_value=d.deal_value,
            status=d.status,
            stage=d.stage,
            sales_rep_name=d.sales_rep_name,
            owner_id=d.owner_id,
            quotation_id=d.quotation_id,
            quotation_number=d.quotation.quotation_number if d.quotation else None,
            quotation_version=d.quotation_version,
            probability=d.probability,
            expected_revenue=d.expected_revenue,
            gross_profit=d.gross_profit,
            margin_percentage=d.margin_percentage,
            closed_date=d.closed_date,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )

    @classmethod
    def to_deal_detail(cls, d: CustomerDealHistory) -> DealDetailResponse:
        summary = cls.to_deal_summary(d)
        prod_dtos = [
            DealProductResponse(
                id=p.id,
                deal_id=p.deal_id,
                product_id=p.product_id,
                product_name=p.product.name if p.product else None,
                product_sku=p.product.sku if p.product else None,
                quotation_line_item_id=p.quotation_line_item_id,
                quantity=p.quantity,
                unit_price=p.unit_price,
                unit_cost=p.unit_cost,
                discount_percent=p.discount_percent,
                tax_rate=p.tax_rate,
                subtotal=p.subtotal,
                discount_amount=p.discount_amount,
                taxable_amount=p.taxable_amount,
                tax_amount=p.tax_amount,
                total_amount=p.total_amount,
                total_cost=p.total_cost,
                gross_profit=p.gross_profit,
                margin_percentage=p.margin_percentage,
                notes=p.notes,
                created_at=p.created_at,
            )
            for p in d.products
        ]
        recent_acts = [
            DealActivityResponse(
                id=a.id,
                deal_id=a.deal_id,
                activity_type=a.activity_type,
                title=a.title,
                description=a.description,
                actor_id=a.actor_id,
                actor_name=f"{a.actor.first_name} {a.actor.last_name}".strip() if a.actor else "System",
                activity_metadata=a.activity_metadata,
                created_at=a.created_at,
            )
            for a in d.activities[:10]
        ]
        return DealDetailResponse(
            **summary.model_dump(),
            subtotal=d.subtotal,
            discount_amount=d.discount_amount,
            discount_percent=d.discount_percent,
            tax_amount=d.tax_amount,
            total_cost=d.total_cost,
            notes=d.notes,
            products=prod_dtos,
            recent_activities=recent_acts,
        )

    @classmethod
    def list_deals(
        cls,
        db: Session,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        stage: Optional[str] = None,
        status: Optional[str] = None,
        customer_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[DealSummaryResponse], int]:
        query = (
            select(CustomerDealHistory)
            .where(CustomerDealHistory.company_id == company_id)
            .options(
                selectinload(CustomerDealHistory.customer),
                selectinload(CustomerDealHistory.quotation),
            )
        )
        if stage:
            query = query.where(CustomerDealHistory.stage == stage)
        if status:
            query = query.where(CustomerDealHistory.status == status)
        if customer_id:
            query = query.where(CustomerDealHistory.customer_id == customer_id)
        if search:
            s_term = f"%{search}%"
            query = query.where(
                (CustomerDealHistory.deal_code.ilike(s_term))
                | (CustomerDealHistory.title.ilike(s_term))
            )

        total_stmt = select(func.count()).select_from(query.subquery())
        total = db.execute(total_stmt).scalar() or 0

        deals = (
            db.execute(
                query.order_by(CustomerDealHistory.created_at.desc())
                .limit(limit)
                .offset(skip)
            )
            .scalars()
            .all()
        )

        return [cls.to_deal_summary(d) for d in deals], total

    @classmethod
    def get_deal_by_id(
        cls,
        db: Session,
        company_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> CustomerDealHistory:
        deal = db.execute(
            select(CustomerDealHistory)
            .where(
                CustomerDealHistory.id == deal_id,
                CustomerDealHistory.company_id == company_id,
            )
            .options(
                selectinload(CustomerDealHistory.customer),
                selectinload(CustomerDealHistory.quotation),
                selectinload(CustomerDealHistory.products).selectinload(DealProduct.product),
                selectinload(CustomerDealHistory.activities).selectinload(DealActivity.actor),
            )
        ).scalar_one_or_none()
        if not deal:
            raise ApplicationError(
                f"Deal {deal_id} not found in company scope.", status_code=404
            )
        return deal

    @classmethod
    def recalculate_and_save(
        cls,
        db: Session,
        company_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> CustomerDealHistory:
        deal = cls.get_deal_by_id(db, company_id, deal_id)
        DealCalculationEngine.recalculate_deal_totals(deal)
        prob, _, _ = DealProbabilityService.calculate_probability(db, deal)
        deal.probability = prob
        deal.expected_revenue = quantize_dec(
            deal.deal_value * Decimal(prob) / Decimal("100.00")
        )
        db.flush()
        return deal

