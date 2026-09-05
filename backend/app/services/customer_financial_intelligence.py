"""Customer Financial Intelligence Service (Phases 063–065).

Provides deterministic, explainable calculations for:
- Phase 063: Customer LTV (Lifetime Value)
- Phase 064: Customer Discount Sensitivity
- Phase 065: Customer Risk Profile

Strictly non-ML, deterministic algorithms operating on verified historical customer data.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.customer_purchase_history import CustomerPurchaseHistory
from app.models.user import User
from app.schemas.customer import (
    CustomerFinancialIntelligenceResponse,
    CustomerLtvResponse,
    CustomerRiskProfileResponse,
    DiscountSensitivityResponse,
)
from app.services.authorization import AuthorizationService


class CustomerFinancialIntelligenceService:
    """Dedicated analytical calculation service for customer-level financial metrics."""

    @classmethod
    def calculate_ltv(
        cls,
        db: Session,
        customer: Customer,
    ) -> CustomerLtvResponse:
        """Phase 063: Deterministic Customer Lifetime Value (LTV) calculation.

        Inputs:
        - Completed/Valid purchase orders (customer_purchase_history)
        - Settled payments (customer_payment_history)

        Formula:
        - Sum of realized purchase orders
        - Average Order Value (AOV) = Total Purchase Amount / Order Count
        - Handles 0 orders, 1 order, and multiple orders safely with 0-division guards.
        """
        purchases = db.scalars(
            select(CustomerPurchaseHistory)
            .where(
                CustomerPurchaseHistory.customer_id == customer.id,
                CustomerPurchaseHistory.company_id == customer.company_id,
            )
            .order_by(CustomerPurchaseHistory.purchase_date.asc())
        ).all()

        payments = db.scalars(
            select(CustomerPaymentHistory)
            .where(
                CustomerPaymentHistory.customer_id == customer.id,
                CustomerPaymentHistory.company_id == customer.company_id,
            )
        ).all()

        total_orders_count = len(purchases)
        total_purchases_amount = Decimal("0.00")
        first_purchase_date = None
        latest_purchase_date = None

        if purchases:
            first_purchase_date = purchases[0].purchase_date
            latest_purchase_date = purchases[-1].purchase_date
            for p in purchases:
                # Include completed or processing orders in purchase value
                if p.status in ("COMPLETED", "PROCESSING"):
                    total_purchases_amount += Decimal(str(p.total_amount))

        total_settled_payments = Decimal("0.00")
        for pay in payments:
            if pay.status == "COMPLETED":
                total_settled_payments += Decimal(str(pay.amount))

        # AOV calculation with zero-division safeguard
        if total_orders_count > 0:
            average_order_value = (total_purchases_amount / Decimal(total_orders_count)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            average_order_value = Decimal("0.00")

        # Realized LTV is the total purchase value realized
        ltv_amount = total_purchases_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return CustomerLtvResponse(
            customer_id=customer.id,
            ltv_amount=ltv_amount,
            total_purchases_count=total_orders_count,
            total_purchases_amount=total_purchases_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_settled_payments_amount=total_settled_payments.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            average_order_value=average_order_value,
            first_purchase_date=first_purchase_date,
            latest_purchase_date=latest_purchase_date,
            calculated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def calculate_discount_sensitivity(
        cls,
        db: Session,
        customer: Customer,
    ) -> DiscountSensitivityResponse:
        """Phase 064: Deterministic Customer Discount Sensitivity indication.

        Analyzes historical discount records and purchase activity to evaluate
        how heavily the client relies on discounts to execute transactions.

        Classification levels:
        - INSUFFICIENT_DATA: No purchases or discount records logged.
        - HIGH: Average discount > 12% OR discount frequency > 50%
        - MODERATE: Average discount 5%-12% OR discount frequency 20%-50%
        - LOW: Average discount < 5% AND discount frequency < 20%
        """
        purchases = db.scalars(
            select(CustomerPurchaseHistory)
            .where(
                CustomerPurchaseHistory.customer_id == customer.id,
                CustomerPurchaseHistory.company_id == customer.company_id,
            )
        ).all()

        discounts = db.scalars(
            select(CustomerDiscountHistory)
            .where(
                CustomerDiscountHistory.customer_id == customer.id,
                CustomerDiscountHistory.company_id == customer.company_id,
            )
        ).all()

        total_orders = len(purchases)
        total_discounts_count = len(discounts)

        # Insufficient data guard
        if total_orders == 0 and total_discounts_count == 0:
            return DiscountSensitivityResponse(
                customer_id=customer.id,
                score=0,
                level="INSUFFICIENT_DATA",
                average_discount_percent=Decimal("0.00"),
                discount_frequency_percent=Decimal("0.00"),
                total_orders_evaluated=0,
                discounted_orders_count=0,
                explanation="No transactions or discount records available for evaluation.",
                evaluated_at=datetime.now(timezone.utc),
            )

        # Calculate average discount percentage
        if total_discounts_count > 0:
            sum_discount_pct = sum(Decimal(str(d.discount_percentage)) for d in discounts)
            avg_discount_pct = (sum_discount_pct / Decimal(total_discounts_count)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            avg_discount_pct = Decimal("0.00")

        # Frequency ratio relative to total orders
        if total_orders > 0:
            # Cap discounted orders count to total orders for frequency ratio
            discounted_orders = min(total_discounts_count, total_orders)
            frequency_pct = (
                (Decimal(discounted_orders) / Decimal(total_orders)) * Decimal("100.00")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            discounted_orders = total_discounts_count
            frequency_pct = Decimal("100.00") if total_discounts_count > 0 else Decimal("0.00")

        # Classification logic
        if avg_discount_pct > Decimal("12.00") or frequency_pct > Decimal("50.00"):
            level = "HIGH"
            # Score 70 - 100
            score = min(100, int(Decimal("60") + (avg_discount_pct * Decimal("2.0"))))
            explanation = (
                f"High price sensitivity: Client transactions frequently require significant discounts "
                f"(average {avg_discount_pct}% across {frequency_pct}% of orders)."
            )
        elif avg_discount_pct >= Decimal("5.00") or frequency_pct >= Decimal("20.00"):
            level = "MODERATE"
            # Score 35 - 69
            score = max(35, min(69, int(Decimal("30") + (avg_discount_pct * Decimal("3.0")))))
            explanation = (
                f"Moderate price sensitivity: Occasional discounting requested "
                f"(average {avg_discount_pct}%, discount frequency {frequency_pct}%)."
            )
        else:
            level = "LOW"
            # Score 0 - 34
            score = max(0, min(34, int(avg_discount_pct * Decimal("4.0"))))
            explanation = (
                f"Low price sensitivity: Standard pricing accepted with negligible discount reliance "
                f"(average {avg_discount_pct}%)."
            )

        return DiscountSensitivityResponse(
            customer_id=customer.id,
            score=score,
            level=level,
            average_discount_percent=avg_discount_pct,
            discount_frequency_percent=frequency_pct,
            total_orders_evaluated=total_orders,
            discounted_orders_count=discounted_orders,
            explanation=explanation,
            evaluated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def calculate_risk_profile(
        cls,
        db: Session,
        customer: Customer,
    ) -> CustomerRiskProfileResponse:
        """Phase 065: Deterministic Customer Risk Profile assessment.

        Synthesizes payment history, account status, and discount volatility into
        an explainable risk score (0-100) and category (LOW, MEDIUM, HIGH).

        Risk Factors & Scoring Weights:
        1. Payment Reliability (up to 50 points):
           - Failed or delayed payment ratio: failed_payments / total_payments.
        2. Account Status (20 points):
           - Inactive account: +20 points.
        3. High Discount Dependence (up to 15 points):
           - From Phase 064 sensitivity evaluation.
        4. Credit / Tier Standing (up to 15 points):
           - No tier assigned or low volume: neutral/moderate baseline.

        Classification:
        - LOW: 0 - 29 points
        - MEDIUM: 30 - 59 points
        - HIGH: 60 - 100 points
        """
        payments = db.scalars(
            select(CustomerPaymentHistory)
            .where(
                CustomerPaymentHistory.customer_id == customer.id,
                CustomerPaymentHistory.company_id == customer.company_id,
            )
        ).all()

        total_payments = len(payments)
        failed_payments = [p for p in payments if p.status in ("FAILED", "REFUNDED")]
        failed_count = len(failed_payments)

        score = 0
        primary_factors: List[str] = []

        # 1. Payment reliability evaluation
        if total_payments > 0:
            failed_ratio = (
                (Decimal(failed_count) / Decimal(total_payments)) * Decimal("100.00")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            if failed_ratio >= Decimal("40.00"):
                score += 50
                primary_factors.append(f"Critical payment default rate ({failed_ratio}% of {total_payments} transactions failed)")
            elif failed_ratio >= Decimal("20.00"):
                score += 30
                primary_factors.append(f"Elevated payment delinquency ({failed_ratio}% failure rate)")
            elif failed_ratio > Decimal("0.00"):
                score += 15
                primary_factors.append(f"Minor payment failures recorded ({failed_count} incident)")
            else:
                primary_factors.append("Flawless payment track record (100% settlement rate)")
        else:
            failed_ratio = Decimal("0.00")
            score += 10
            primary_factors.append("New account with zero historical payment records")

        payment_reliability_score = max(0, 100 - int(score))

        # 2. Account status evaluation
        if not customer.is_active:
            score += 25
            primary_factors.append("Account is currently marked as Inactive/Suspended")
        else:
            primary_factors.append("Account is Active in good standing")

        # 3. Discount volatility evaluation
        sensitivity = cls.calculate_discount_sensitivity(db, customer)
        if sensitivity.level == "HIGH":
            score += 15
            primary_factors.append("Excessive discount dependency presents margin vulnerability")
        elif sensitivity.level == "MODERATE":
            score += 5

        # Bound score between 0 and 100
        final_score = max(0, min(100, score))

        # Classification mapping
        if final_score >= 60:
            risk_level = "HIGH"
            explanation = "Elevated risk profile driven by payment default history, suspended status, or high margin volatility."
        elif final_score >= 30:
            risk_level = "MEDIUM"
            explanation = "Moderate risk profile with acceptable credit history but limited volume or occasional payment variance."
        else:
            risk_level = "LOW"
            explanation = "Low financial risk with verified payment reliability and stable commercial engagement."

        return CustomerRiskProfileResponse(
            customer_id=customer.id,
            score=final_score,
            risk_level=risk_level,
            failed_payment_ratio=failed_ratio,
            payment_reliability_score=payment_reliability_score,
            account_status="ACTIVE" if customer.is_active else "INACTIVE",
            primary_factors=primary_factors,
            explanation=explanation,
            evaluated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def get_financial_intelligence(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
    ) -> CustomerFinancialIntelligenceResponse:
        """Consolidated entrypoint returning LTV, Discount Sensitivity, and Risk Profile."""
        from app.services.customer import CustomerService

        customer = CustomerService.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="read")

        ltv = cls.calculate_ltv(db, customer)
        sensitivity = cls.calculate_discount_sensitivity(db, customer)
        risk = cls.calculate_risk_profile(db, customer)

        return CustomerFinancialIntelligenceResponse(
            customer_id=customer.id,
            ltv=ltv,
            discount_sensitivity=sensitivity,
            risk_profile=risk,
        )
