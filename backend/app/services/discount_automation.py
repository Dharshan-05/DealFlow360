"""Discount Automation & Decision Engine Services (DealFlow360 G24: Phases 116–120).

Implements:
- Phase 116: Inventory-Aware Discount Service
- Phase 117: Deal-Value-Aware Discount Service
- Phase 118: Discount Risk Calculation Service
- Phase 119: Discount Decision Engine
- Phase 120: Automated Discount Application Service

All financial arithmetic uses strict Decimal precision and enforces company tenant isolation.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.applied_discount import AppliedDiscount
from app.models.audit_log import AuditLog
from app.models.backorder import Backorder
from app.models.customer import Customer
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.product import Product
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.discount_automation import (
    AppliedDiscountResponse,
    ApplyDiscountRequest,
    DealValueDiscountSignalResponse,
    DiscountDecisionResponse,
    DiscountRiskCalculationResponse,
    InventoryDiscountSignalResponse,
    RiskDimensionScore,
)
from app.services.atp import AvailableToPromiseService
from app.services.discount_governance import DiscountPolicyEngine
from app.services.discount_intelligence import (
    CustomerDiscountAnalysisService,
    DiscountRecommendationEngine,
    MarginProtectionEngine,
    MaximumSafeDiscountEngine,
    quantize_dec,
)
from app.services.multi_warehouse_stock import MultiWarehouseStockService


# ==============================================================================
# Phase 116: Inventory-Aware Discount Service
# ==============================================================================

class InventoryAwareDiscountService:
    """Modulates discount recommendations based on real-time stock levels, ATP,

    and backorder conditions across all company warehouses.
    """

    @classmethod
    def evaluate_inventory_signal(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        base_target_discount: Decimal,
    ) -> InventoryDiscountSignalResponse:
        now = datetime.now(timezone.utc)
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        # Aggregate multi-warehouse stock
        stock_resp = MultiWarehouseStockService.get_product_multi_warehouse_stock(
            db=db, product_id=product_id, company_id=company_id
        )
        total_physical = stock_resp.total_physical_quantity
        total_reserved = stock_resp.total_reserved_quantity
        total_atp = stock_resp.total_available_quantity

        # Count open backorders
        open_backorders = (
            db.query(Backorder)
            .filter(
                Backorder.company_id == company_id,
                Backorder.product_id == product_id,
                Backorder.status == "OPEN",
            )
            .count()
        )

        # Classify inventory signal
        base_target = Decimal(str(base_target_discount))
        if total_atp <= 0 and open_backorders > 0:
            signal = "BACKORDERED"
            factor = Decimal("0.50")
            reason = "INVENTORY_BACKORDERED"
            explanation = f"Stock is depleted with {open_backorders} open backorder(s); discount reduced by 50%."
        elif total_atp <= 0:
            signal = "OUT_OF_STOCK"
            factor = Decimal("0.00")
            reason = "INVENTORY_OUT_OF_STOCK"
            explanation = "Product has zero available-to-promise stock across all facilities; discount curtailed to 0.00%."
        elif total_atp <= 10:
            signal = "LOW_STOCK"
            factor = Decimal("0.75")
            reason = "INVENTORY_SCARCITY"
            explanation = f"Low inventory detected ({total_atp} units ATP); discount reduced to preserve scarce supply."
        elif total_atp >= 100:
            signal = "EXCESS_AVAILABLE"
            factor = Decimal("1.20")
            reason = "INVENTORY_SURPLUS"
            explanation = f"Abundant inventory ({total_atp} units ATP); discount incentivized to accelerate inventory turnover."
        else:
            signal = "HEALTHY_STOCK"
            factor = Decimal("1.00")
            reason = "INVENTORY_NORMAL"
            explanation = f"Healthy inventory baseline ({total_atp} units ATP); standard discount strategy applies."

        suggested = quantize_dec(min(Decimal("100.00"), max(Decimal("0.00"), base_target * factor)))

        return InventoryDiscountSignalResponse(
            product_id=product_id,
            total_physical_stock=total_physical,
            total_reserved_stock=total_reserved,
            total_available_to_promise=total_atp,
            open_backorders_count=open_backorders,
            inventory_signal=signal,
            adjustment_factor=factor,
            suggested_discount=suggested,
            reason_code=reason,
            explanation=explanation,
            evaluated_at=now,
        )


# ==============================================================================
# Phase 117: Deal-Value-Aware Discount Service
# ==============================================================================

class DealValueAwareDiscountService:
    """Modulates discount recommendations based on overall deal/order sizing

    using strict Decimal financial calculations.
    """

    @classmethod
    def evaluate_deal_value_signal(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        base_target_discount: Decimal,
        deal_value: Optional[Decimal] = None,
        quantity: int = 1,
        selling_price_override: Optional[Decimal] = None,
    ) -> DealValueDiscountSignalResponse:
        now = datetime.now(timezone.utc)
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        price = Decimal(str(selling_price_override)) if selling_price_override is not None else Decimal(str(product.base_price))

        if deal_value is not None and deal_value > Decimal("0.00"):
            val = Decimal(str(deal_value))
        else:
            val = price * Decimal(str(max(1, quantity)))

        val = quantize_dec(val)
        base_target = Decimal(str(base_target_discount))

        if val >= Decimal("50000.00"):
            tier = "ENTERPRISE_TIER"
            mult = Decimal("1.25")
            reason = "DEAL_VALUE_ENTERPRISE"
            explanation = f"Enterprise transaction tier (${val:,.2f}); volume incentive granted (+25% target discount)."
        elif val >= Decimal("10000.00"):
            tier = "HIGH_VALUE"
            mult = Decimal("1.15")
            reason = "DEAL_VALUE_HIGH"
            explanation = f"High-value deal sizing (${val:,.2f}); incentive granted (+15% target discount)."
        elif val >= Decimal("1000.00"):
            tier = "STANDARD_VALUE"
            mult = Decimal("1.00")
            reason = "DEAL_VALUE_STANDARD"
            explanation = f"Standard transaction value (${val:,.2f}); standard pricing applies."
        else:
            tier = "LOW_VALUE"
            mult = Decimal("0.80")
            reason = "DEAL_VALUE_LOW"
            explanation = f"Low transaction value (${val:,.2f}); discount minimized to preserve margin on small orders."

        suggested = quantize_dec(min(Decimal("100.00"), max(Decimal("0.00"), base_target * mult)))

        return DealValueDiscountSignalResponse(
            product_id=product_id,
            effective_deal_value=val,
            value_tier=tier,
            value_incentive_multiplier=mult,
            suggested_discount=suggested,
            reason_code=reason,
            explanation=explanation,
            evaluated_at=now,
        )


# ==============================================================================
# Phase 118: Discount Risk Calculation Service
# ==============================================================================

class DiscountRiskCalculationService:
    """Evaluates multi-factor risk associated with applying a requested discount."""

    @classmethod
    def calculate_risk(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        product_id: uuid.UUID,
        requested_discount: Decimal,
        actor: User,
        deal_value: Optional[Decimal] = None,
        selling_price_override: Optional[Decimal] = None,
        min_margin_percentage: Decimal = Decimal("15.00"),
    ) -> DiscountRiskCalculationResponse:
        now = datetime.now(timezone.utc)
        req_disc = quantize_dec(Decimal(str(requested_discount)))

        # 1. Safe Bound & Policy Evaluation
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
        gov_ceiling = safe_eval.governed_ceiling
        actor_limit = safe_eval.actor_authority_limit or Decimal("100.00")
        margin_ceiling = safe_eval.margin_ceiling

        # 2. Inventory Signal
        inv_eval = InventoryAwareDiscountService.evaluate_inventory_signal(
            db=db, company_id=company_id, product_id=product_id, base_target_discount=req_disc
        )

        # 3. Customer Discount Profile
        cust_eval = CustomerDiscountAnalysisService.analyze_customer(
            db=db, company_id=company_id, customer_id=customer_id
        )

        # 4. Dimension 1: Ceiling & Governance Overrun Risk (Weight 30%)
        if req_disc > gov_ceiling:
            gov_score = 100
            gov_detail = f"Requested {req_disc}% breaches authoritative policy ceiling of {gov_ceiling}%."
        elif req_disc > actor_limit:
            gov_score = 75
            gov_detail = f"Requested {req_disc}% exceeds actor authority limit of {actor_limit}%."
        elif req_disc > max_safe:
            gov_score = 50
            gov_detail = f"Requested {req_disc}% exceeds calculated maximum safe boundary of {max_safe}%."
        else:
            gov_score = 10
            gov_detail = f"Requested {req_disc}% is fully within governed limits ({gov_ceiling}%)."

        # 5. Dimension 2: Margin Erosion Risk (Weight 35%)
        if margin_ceiling <= Decimal("0.00") and req_disc > Decimal("0.00"):
            margin_score = 100
            margin_detail = "Zero margin buffer exists; any discount causes immediate financial loss."
        elif req_disc > margin_ceiling:
            margin_score = 85
            margin_detail = f"Requested {req_disc}% erodes profit margin below required {min_margin_percentage}% threshold."
        elif req_disc >= margin_ceiling * Decimal("0.90"):
            margin_score = 45
            margin_detail = f"Requested {req_disc}% consumes over 90% of allowable margin buffer."
        else:
            margin_score = 10
            margin_detail = "Sufficient margin buffer preserved post-discount."

        # 6. Dimension 3: Inventory Scarcity Risk (Weight 15%)
        if inv_eval.inventory_signal in ["OUT_OF_STOCK", "BACKORDERED"] and req_disc > Decimal("0.00"):
            inv_score = 90
            inv_detail = f"High discount on {inv_eval.inventory_signal} product."
        elif inv_eval.inventory_signal == "LOW_STOCK" and req_disc > Decimal("10.00"):
            inv_score = 60
            inv_detail = "Elevated discount on scarce inventory."
        else:
            inv_score = 10
            inv_detail = "Inventory conditions accommodate discounting."

        # 7. Dimension 4: Customer Profile & Behavior Risk (Weight 10%)
        if cust_eval.compliance_rating == "HIGH_DISCOUNT_CUSTOMER":
            cust_score = 70
            cust_detail = f"Customer averages high historical discounts ({cust_eval.history_summary.average_discount}%)."
        elif cust_eval.compliance_rating == "NO_HISTORY":
            cust_score = 35
            cust_detail = "Customer has no prior discount track record."
        else:
            cust_score = 10
            cust_detail = "Established compliant customer account."

        # 8. Dimension 5: Deal Value Exposure Risk (Weight 10%)
        val_eval = DealValueAwareDiscountService.evaluate_deal_value_signal(
            db=db, company_id=company_id, product_id=product_id, base_target_discount=req_disc, deal_value=deal_value
        )
        if val_eval.effective_deal_value >= Decimal("50000.00") and req_disc > Decimal("20.00"):
            val_score = 65
            val_detail = f"Large absolute revenue exposure (${val_eval.effective_deal_value:,.2f}) at high discount."
        else:
            val_score = 15
            val_detail = "Normal transaction revenue exposure."

        dimensions = [
            RiskDimensionScore(dimension="GOVERNANCE_OVERRUN", score=gov_score, weight=Decimal("0.30"), weighted_score=quantize_dec(Decimal(gov_score) * Decimal("0.30")), details=gov_detail),
            RiskDimensionScore(dimension="MARGIN_EROSION", score=margin_score, weight=Decimal("0.35"), weighted_score=quantize_dec(Decimal(margin_score) * Decimal("0.35")), details=margin_detail),
            RiskDimensionScore(dimension="INVENTORY_SCARCITY", score=inv_score, weight=Decimal("0.15"), weighted_score=quantize_dec(Decimal(inv_score) * Decimal("0.15")), details=inv_detail),
            RiskDimensionScore(dimension="CUSTOMER_PROFILE", score=cust_score, weight=Decimal("0.10"), weighted_score=quantize_dec(Decimal(cust_score) * Decimal("0.10")), details=cust_detail),
            RiskDimensionScore(dimension="DEAL_EXPOSURE", score=val_score, weight=Decimal("0.10"), weighted_score=quantize_dec(Decimal(val_score) * Decimal("0.10")), details=val_detail),
        ]

        total_weighted = sum(d.weighted_score for d in dimensions)
        overall_score = int(round(total_weighted))
        overall_score = max(0, min(100, overall_score))

        primary_factors = []
        if gov_score >= 50:
            primary_factors.append(gov_detail)
        if margin_score >= 50:
            primary_factors.append(margin_detail)
        if inv_score >= 50:
            primary_factors.append(inv_detail)
        if cust_score >= 50:
            primary_factors.append(cust_detail)
        if val_score >= 50:
            primary_factors.append(val_detail)

        if overall_score >= 76:
            risk_level = "CRITICAL"
        elif overall_score >= 51:
            risk_level = "HIGH"
        elif overall_score >= 26:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        is_acceptable = risk_level in ["LOW", "MEDIUM"] and req_disc <= max_safe

        summary = f"Discount Risk: {risk_level} (Score: {overall_score}/100). " + ("Complies with risk tolerances." if is_acceptable else "Elevated risk profile detected.")

        return DiscountRiskCalculationResponse(
            customer_id=customer_id,
            product_id=product_id,
            requested_discount=req_disc,
            overall_risk_score=overall_score,
            risk_level=risk_level,
            primary_risk_factors=primary_factors,
            dimensions=dimensions,
            is_acceptable_risk=is_acceptable,
            risk_summary=summary,
            evaluated_at=now,
        )


# ==============================================================================
# Phase 119: Discount Decision Engine
# ==============================================================================

class DiscountDecisionEngine:
    """Master orchestration layer evaluating all completed discount intelligence

    and governance layers to produce a deterministic decision.
    """

    @classmethod
    def evaluate_decision(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        product_id: uuid.UUID,
        requested_discount: Decimal,
        actor: User,
        deal_value: Optional[Decimal] = None,
        deal_reference: Optional[str] = None,
        selling_price_override: Optional[Decimal] = None,
        min_margin_percentage: Decimal = Decimal("15.00"),
    ) -> DiscountDecisionResponse:
        now = datetime.now(timezone.utc)
        decision_id = f"DEC-{uuid.uuid4().hex[:10].upper()}"
        req_disc = quantize_dec(Decimal(str(requested_discount)))

        # 1. Evaluate Risk (which evaluates Policy + Margin + Max Safe + Inventory + Customer)
        risk_resp = DiscountRiskCalculationService.calculate_risk(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
            product_id=product_id,
            requested_discount=req_disc,
            actor=actor,
            deal_value=deal_value,
            selling_price_override=selling_price_override,
            min_margin_percentage=min_margin_percentage,
        )

        safe_eval = MaximumSafeDiscountEngine.evaluate(
            db=db,
            company_id=company_id,
            customer_id=customer_id,
            product_id=product_id,
            actor=actor,
            selling_price_override=selling_price_override,
            min_margin_percentage=min_margin_percentage,
        )
        gov_ceiling = safe_eval.governed_ceiling
        actor_limit = safe_eval.actor_authority_limit
        margin_ceiling = safe_eval.margin_ceiling
        max_safe = safe_eval.max_safe_discount

        inv_eval = InventoryAwareDiscountService.evaluate_inventory_signal(
            db=db, company_id=company_id, product_id=product_id, base_target_discount=req_disc
        )
        val_eval = DealValueAwareDiscountService.evaluate_deal_value_signal(
            db=db, company_id=company_id, product_id=product_id, base_target_discount=req_disc, deal_value=deal_value
        )

        limiting_factors = []
        requires_escalation = False
        escalation_role = None

        # Precedence Rule Evaluation:
        # Rule 1: Rejection if requested discount breaches governed ceiling or margin is strictly depleted or risk is critical or max_safe is zero
        if req_disc > gov_ceiling:
            decision = "REJECTED"
            permitted = Decimal("0.00")
            limiting_factors.append(f"Exceeds organizational governance ceiling of {gov_ceiling}%")
            summary = f"Discount request of {req_disc}% REJECTED because it breaches the authoritative policy ceiling of {gov_ceiling}%."
        elif margin_ceiling <= Decimal("0.00") and req_disc > Decimal("0.00"):
            decision = "REJECTED"
            permitted = Decimal("0.00")
            limiting_factors.append("Product unit cost precludes any discount without negative margin")
            summary = f"Discount request of {req_disc}% REJECTED because product margins cannot support any discount."
        elif risk_resp.risk_level == "CRITICAL":
            decision = "REJECTED"
            permitted = max_safe
            limiting_factors.append("Critical risk score (breaches multiple governance and margin boundaries)")
            summary = f"Discount request of {req_disc}% REJECTED due to CRITICAL risk rating ({risk_resp.overall_risk_score}/100)."
        elif max_safe <= Decimal("0.00") and req_disc > Decimal("0.00"):
            decision = "REJECTED"
            permitted = Decimal("0.00")
            limiting_factors.append("Safe allowable discount capacity is zero")
            summary = f"Discount request of {req_disc}% REJECTED because maximum safe discount capacity is 0.00%."

        # Rule 2: Escalation Required if requested discount exceeds actor limit but is within governed ceiling
        elif actor_limit is not None and req_disc > actor_limit and req_disc <= gov_ceiling:
            decision = "ESCALATION_REQUIRED"
            permitted = max_safe
            requires_escalation = True
            escalation_role = "Sales Manager" if actor_limit <= Decimal("20.00") else "Finance"
            limiting_factors.append(f"Exceeds user authority limit of {actor_limit}% (requires {escalation_role} approval)")
            summary = (
                f"Discount request of {req_disc}% requires ESCALATION to {escalation_role}. "
                f"Requested discount exceeds actor limit ({actor_limit}%) but is within policy ceiling ({gov_ceiling}%)."
            )

        # Rule 3: Adjusted if requested discount exceeds max_safe (or gov ceiling) but can be safely clamped to positive max_safe
        elif req_disc > max_safe:
            decision = "ADJUSTED"
            permitted = max_safe
            limiting_factors.append(f"Clamped to maximum safe limit of {max_safe}% ({safe_eval.limiting_factor})")
            summary = (
                f"Discount request of {req_disc}% ADJUSTED to maximum safe limit of {max_safe}%. "
                f"Preserves minimum profit margin and complies with all governance policies."
            )

        # Rule 4: Approved
        else:
            decision = "APPROVED"
            permitted = req_disc
            summary = f"Discount request of {req_disc}% APPROVED. Complies with all policies, margins, and risk bounds."

        is_executable = decision in ["APPROVED", "ADJUSTED"] and permitted > Decimal("0.00")

        return DiscountDecisionResponse(
            decision_id=decision_id,
            customer_id=customer_id,
            product_id=product_id,
            requested_discount=req_disc,
            decision=decision,
            permitted_discount=permitted,
            effective_ceiling=gov_ceiling,
            actor_authority_limit=actor_limit,
            margin_ceiling=margin_ceiling,
            max_safe_discount=max_safe,
            inventory_signal=inv_eval.inventory_signal,
            deal_value_tier=val_eval.value_tier,
            risk_level=risk_resp.risk_level,
            limiting_factors=limiting_factors,
            is_executable=is_executable,
            requires_escalation=requires_escalation,
            escalation_role_needed=escalation_role,
            decision_summary=summary,
            evaluated_at=now,
        )


# ==============================================================================
# Phase 120: Automated Discount Application Service
# ==============================================================================

class AutomatedDiscountApplicationService:
    """Safely executes and records approved discount decisions.

    Guarantees idempotency, tenant isolation, and comprehensive audit logging.
    """

    @classmethod
    def apply_discount(
        cls,
        db: Session,
        company_id: uuid.UUID,
        payload: ApplyDiscountRequest,
        actor: User,
    ) -> AppliedDiscount:
        now = datetime.now(timezone.utc)

        # 1. Verify Customer & Product Exist in Company Scope
        customer = (
            db.query(Customer)
            .filter(Customer.id == payload.customer_id, Customer.company_id == company_id)
            .first()
        )
        if not customer:
            raise NotFoundError(f"Customer with id {payload.customer_id} not found in this company.")

        product = db.query(Product).filter(Product.id == payload.product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {payload.product_id} not found.")

        # 2. Idempotency Check: Prevent applying twice to the same deal reference + product
        existing = (
            db.query(AppliedDiscount)
            .filter(
                AppliedDiscount.company_id == company_id,
                AppliedDiscount.deal_reference == payload.deal_reference,
                AppliedDiscount.product_id == payload.product_id,
            )
            .first()
        )
        if existing:
            return existing

        # 3. Re-evaluate Decision Server-Side (Never Trust Frontend)
        decision = DiscountDecisionEngine.evaluate_decision(
            db=db,
            company_id=company_id,
            customer_id=payload.customer_id,
            product_id=payload.product_id,
            requested_discount=payload.requested_discount,
            actor=actor,
            deal_value=payload.deal_value,
            deal_reference=payload.deal_reference,
            selling_price_override=payload.selling_price_override,
            min_margin_percentage=payload.min_margin_percentage,
        )

        if decision.decision == "REJECTED":
            raise ValidationError(f"Cannot apply rejected discount: {decision.decision_summary}")
        if decision.decision == "ESCALATION_REQUIRED":
            raise ForbiddenError(f"Cannot apply discount requiring escalation: {decision.decision_summary}")

        applied_disc = decision.permitted_discount
        price = Decimal(str(payload.selling_price_override)) if payload.selling_price_override is not None else Decimal(str(product.base_price))
        cost = Decimal(str(product.cost))

        discount_multiplier = Decimal("1.0") - (applied_disc / Decimal("100.0"))
        discounted_price = quantize_dec(price * discount_multiplier)
        discount_amount = quantize_dec(price - discounted_price)

        if discounted_price > Decimal("0.00"):
            margin = quantize_dec(((discounted_price - cost) / discounted_price) * Decimal("100.0"))
        else:
            margin = Decimal("0.00")

        # 4. Record Applied Discount Entity
        record = AppliedDiscount(
            company_id=company_id,
            customer_id=payload.customer_id,
            product_id=payload.product_id,
            user_id=actor.id,
            deal_reference=payload.deal_reference,
            decision_id=decision.decision_id,
            requested_discount=payload.requested_discount,
            applied_discount=applied_disc,
            selling_price=price,
            discounted_price=discounted_price,
            unit_cost=cost,
            margin_percentage=margin,
            risk_level=decision.risk_level,
            reason_code=decision.decision,
            decision_summary=decision.decision_summary,
            context_metadata={
                "notes": payload.notes,
                "limiting_factors": decision.limiting_factors,
                "inventory_signal": decision.inventory_signal,
                "deal_value_tier": decision.deal_value_tier,
                "effective_ceiling": float(decision.effective_ceiling),
            },
            applied_at=now,
        )
        db.add(record)

        # 5. Enrich CustomerDiscountHistory (Integration with Phase 061/114/115)
        hist_entry = CustomerDiscountHistory(
            company_id=company_id,
            customer_id=payload.customer_id,
            discount_code=f"APPLIED-{decision.decision_id[:8]}",
            discount_percentage=applied_disc,
            discount_amount=discount_amount,
            deal_reference=payload.deal_reference,
            reason=payload.notes or decision.decision_summary,
            applied_at=now,
        )
        db.add(hist_entry)

        # 6. Record Audit Log
        audit = AuditLog(
            action="AUTOMATED_DISCOUNT_APPLIED",
            resource_type="applied_discount",
            resource_id=str(record.id),
            user_id=actor.id,
            company_id=company_id,
            context_metadata={
                "deal_reference": payload.deal_reference,
                "product_id": str(product.id),
                "customer_id": str(customer.id),
                "applied_discount": float(applied_disc),
                "discounted_price": float(discounted_price),
                "decision": decision.decision,
            },
        )
        db.add(audit)

        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def list_applied_discounts(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        product_id: Optional[uuid.UUID] = None,
        deal_reference: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AppliedDiscount]:
        query = db.query(AppliedDiscount).filter(AppliedDiscount.company_id == company_id)
        if customer_id:
            query = query.filter(AppliedDiscount.customer_id == customer_id)
        if product_id:
            query = query.filter(AppliedDiscount.product_id == product_id)
        if deal_reference:
            query = query.filter(AppliedDiscount.deal_reference.ilike(f"%{deal_reference}%"))

        return query.order_by(AppliedDiscount.applied_at.desc()).offset(skip).limit(limit).all()

    @classmethod
    def count_applied_discounts(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        product_id: Optional[uuid.UUID] = None,
        deal_reference: Optional[str] = None,
    ) -> int:
        query = db.query(AppliedDiscount).filter(AppliedDiscount.company_id == company_id)
        if customer_id:
            query = query.filter(AppliedDiscount.customer_id == customer_id)
        if product_id:
            query = query.filter(AppliedDiscount.product_id == product_id)
        if deal_reference:
            query = query.filter(AppliedDiscount.deal_reference.ilike(f"%{deal_reference}%"))

        return query.count()
