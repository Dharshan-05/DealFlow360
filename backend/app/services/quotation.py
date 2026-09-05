"""Quotation Domain Services (DealFlow360 B09: Phases 186–195).

Implements core domain operations:
- Phase 186: Quotation CRUD & Lifecycle Management
- Phase 187: Collision-Safe Quote Number Generation
- Phase 188: Tenant-Isolated Customer Selection & Validation
- Phase 189: Catalog Product Selection & Status Validation
- Phase 190: Positive Quantity Management
- Phase 191: Product-Derived Unit Pricing & Authorized Overrides
- Phase 192: Line & Consolidated Tax Calculation
- Phase 193: Line-Level Discount Application & Recalculation
- Phase 194: Quotation-Level Overall Discount Application
- Phase 195: Real-Time Gross Margin & Negative Margin Detection
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.product import Product
from app.models.quotation import Quotation, QuotationStatus
from app.models.quotation_line_item import QuotationLineItem
from app.models.user import User
from app.schemas.quotation import (
    QuotationCalculationRequest,
    QuotationCalculationResponse,
    QuotationCreate,
    QuotationDetailResponse,
    QuotationLineItemCreate,
    QuotationLineItemResponse,
    QuotationSummaryResponse,
    QuotationUpdate,
)

logger = logging.getLogger("dealflow360.quotations")

DECIMAL_CENTS = Decimal("0.01")
DECIMAL_QUANTITY = Decimal("0.0001")


def quantize_dec(val: Decimal, precision: Decimal = DECIMAL_CENTS) -> Decimal:
    """Strictly quantize monetary and percentage Decimals with ROUND_HALF_UP."""
    return val.quantize(precision, rounding=ROUND_HALF_UP)


# ==============================================================================
# Phase 187: Quote Number Generator
# ==============================================================================

class QuotationNumberGenerator:
    """Generates unique, company-scoped, sequential quote numbers (Phase 187)."""

    PREFIX = "QT"

    @classmethod
    def generate_number(cls, db: Session, company_id: uuid.UUID) -> str:
        """Produce collision-safe sequential quote number formatted as QT-YYYYMM-XXXX.

        Uses company-scoped sequence tracking with concurrency collision protection.
        """
        now = datetime.now(timezone.utc)
        period_str = now.strftime("%Y%m")
        prefix = f"{cls.PREFIX}-{period_str}-"

        # Find existing quote numbers with this period prefix for this company
        existing_numbers = db.scalars(
            select(Quotation.quotation_number).where(
                Quotation.company_id == company_id,
                Quotation.quotation_number.like(f"{prefix}%"),
            )
        ).all()

        max_seq = 0
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
        for num in existing_numbers:
            match = pattern.match(num)
            if match:
                try:
                    seq = int(match.group(1))
                    if seq > max_seq:
                        max_seq = seq
                except ValueError:
                    continue

        next_seq = max_seq + 1

        # Attempt up to 5 sequential candidates with existence check for collision safety
        for attempt in range(5):
            candidate = f"{prefix}{next_seq + attempt:04d}"
            exists = db.scalars(
                select(Quotation.id).where(
                    Quotation.company_id == company_id,
                    Quotation.quotation_number == candidate,
                )
            ).first()
            if not exists:
                return candidate

        # Fallback to high-entropy unique suffix if heavily congested
        return f"{prefix}{uuid.uuid4().hex[:6].upper()}"


# ==============================================================================
# Phases 190–195: Quotation Financial Calculation Engine
# ==============================================================================

class QuotationCalculationEngine:
    """Strict Decimal arithmetic calculator for prices, discounts, taxes, and margins (Phases 190–195)."""

    @classmethod
    def calculate_line_item(
        cls,
        product: Product,
        quantity: Decimal,
        unit_price_override: Optional[Decimal] = None,
        discount_percent: Decimal = Decimal("0.00"),
        tax_rate: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute line item amounts in strict Decimal arithmetic (Phases 190–193, 195)."""
        # Phase 190: Positive quantity check
        if quantity <= Decimal("0.00"):
            raise ValueError(f"Quantity must be strictly positive, got {quantity}")

        # Phase 191: Unit price derivation or authorized override
        if unit_price_override is not None and unit_price_override > Decimal("0.00"):
            unit_price = quantize_dec(unit_price_override)
        else:
            unit_price = quantize_dec(product.base_price)

        unit_cost = quantize_dec(product.cost)

        # Line gross subtotal
        subtotal = quantize_dec(quantity * unit_price)

        # Phase 193: Line discount calculation
        discount_percent = quantize_dec(discount_percent)
        if discount_percent < Decimal("0.00") or discount_percent > Decimal("100.00"):
            raise ValueError(f"Line discount percentage must be between 0 and 100, got {discount_percent}")

        discount_amount = quantize_dec(subtotal * (discount_percent / Decimal("100.00")))
        net_amount = subtotal - discount_amount

        # Phase 192: Line tax calculation
        tax_rate = quantize_dec(tax_rate)
        if tax_rate < Decimal("0.00") or tax_rate > Decimal("100.00"):
            raise ValueError(f"Tax rate must be between 0 and 100, got {tax_rate}")

        tax_amount = quantize_dec(net_amount * (tax_rate / Decimal("100.00")))
        total_amount = net_amount + tax_amount

        # Phase 195: Line cost and margin
        line_cost = quantize_dec(quantity * unit_cost)
        gross_profit = net_amount - line_cost

        if net_amount > Decimal("0.00"):
            margin_percentage = quantize_dec((gross_profit / net_amount) * Decimal("100.00"))
        else:
            margin_percentage = Decimal("-100.00") if line_cost > Decimal("0.00") else Decimal("0.00")

        return {
            "product_id": product.id,
            "product_sku": product.sku,
            "product_name": product.name,
            "quantity": quantity,
            "unit_price": unit_price,
            "unit_cost": unit_cost,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "subtotal": subtotal,
            "net_amount": net_amount,
            "total_amount": total_amount,
            "line_cost": line_cost,
            "gross_profit": gross_profit,
            "margin_percentage": margin_percentage,
            "notes": notes,
        }

    @classmethod
    def calculate_quotation_totals(
        cls,
        line_results: List[Dict[str, Any]],
        overall_discount_percent: Decimal = Decimal("0.00"),
    ) -> Dict[str, Any]:
        """Consolidate header totals, overall discount, tax, and margins (Phases 192, 194, 195)."""
        overall_discount_percent = quantize_dec(overall_discount_percent)
        if overall_discount_percent < Decimal("0.00") or overall_discount_percent > Decimal("100.00"):
            raise ValueError(f"Overall discount percent must be between 0 and 100, got {overall_discount_percent}")

        subtotal = Decimal("0.00")
        line_discount_total = Decimal("0.00")
        total_line_net = Decimal("0.00")
        total_cost = Decimal("0.00")

        for line in line_results:
            subtotal += line["subtotal"]
            line_discount_total += line["discount_amount"]
            total_line_net += line["net_amount"]
            total_cost += line["line_cost"]

        # Phase 194: Overall discount applied to net lines subtotal
        overall_discount_amount = quantize_dec(total_line_net * (overall_discount_percent / Decimal("100.00")))
        total_discount = line_discount_total + overall_discount_amount

        # Net taxable base after overall discount
        taxable_amount = total_line_net - overall_discount_amount

        # Phase 192: Calculate consolidated tax adjusting for overall discount proportion
        if total_line_net > Decimal("0.00"):
            taxable_ratio = taxable_amount / total_line_net
        else:
            taxable_ratio = Decimal("0.00")

        tax_amount = Decimal("0.00")
        for line in line_results:
            # Scale line tax by taxable ratio if overall discount applied
            adj_line_tax = quantize_dec(line["tax_amount"] * taxable_ratio)
            tax_amount += adj_line_tax

        total_amount = taxable_amount + tax_amount

        # Phase 195: Real-time quotation margin calculation
        # Net revenue = taxable_amount (pre-tax revenue after all discounts)
        gross_profit = taxable_amount - total_cost

        if taxable_amount > Decimal("0.00"):
            margin_percentage = quantize_dec((gross_profit / taxable_amount) * Decimal("100.00"))
        else:
            margin_percentage = Decimal("-100.00") if total_cost > Decimal("0.00") else Decimal("0.00")

        is_negative_margin = gross_profit < Decimal("0.00")

        return {
            "subtotal": subtotal,
            "line_discount_total": line_discount_total,
            "overall_discount_percent": overall_discount_percent,
            "overall_discount_amount": overall_discount_amount,
            "total_discount": total_discount,
            "taxable_amount": taxable_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "total_cost": total_cost,
            "gross_profit": gross_profit,
            "margin_percentage": margin_percentage,
            "is_negative_margin": is_negative_margin,
        }


# ==============================================================================
# Phase 186: Quotation CRUD & Orchestration Service
# ==============================================================================

class QuotationService:
    """Quotation Lifecycle, CRUD, and business rule orchestration (Phase 186–195)."""

    @classmethod
    def _verify_tenant(cls, current_user: User) -> uuid.UUID:
        if not current_user.company_id:
            raise ApplicationError(
                "Authenticated user must belong to an active organization",
                code="FORBIDDEN_ORG_REQUIRED",
                status_code=403,
            )
        return current_user.company_id

    @classmethod
    def _verify_customer(cls, db: Session, company_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
        """Phase 188: Verify customer exists and strictly belongs to authenticated company."""
        customer = db.scalars(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.company_id == company_id,
            )
        ).one_or_none()

        if not customer:
            raise ApplicationError(
                f"Customer {customer_id} not found in current organization",
                code="CUSTOMER_NOT_FOUND",
                status_code=404,
            )
        return customer

    @classmethod
    def _verify_product(cls, db: Session, product_id: uuid.UUID) -> Product:
        """Phase 189: Verify product exists and is active for sales."""
        product = db.get(Product, product_id)
        if not product:
            raise ApplicationError(
                f"Product {product_id} does not exist",
                code="PRODUCT_NOT_FOUND",
                status_code=404,
            )
        if not product.is_active:
            raise ApplicationError(
                f"Product {product_id} ({product.name}) is inactive and cannot be quoted",
                code="PRODUCT_INACTIVE",
                status_code=400,
            )
        return product

    @classmethod
    def create_quotation(
        cls,
        db: Session,
        current_user: User,
        payload: QuotationCreate,
    ) -> QuotationDetailResponse:
        """Create a new commercial quotation with line items and real-time margins (Phases 186–195)."""
        company_id = cls._verify_tenant(current_user)

        # Phase 188: Validate customer ownership
        customer = cls._verify_customer(db, company_id, payload.customer_id)

        # Process and calculate line items (Phases 189–193, 195)
        calculated_lines: List[Dict[str, Any]] = []
        for idx, line_input in enumerate(payload.line_items, start=1):
            product = cls._verify_product(db, line_input.product_id)
            try:
                line_calc = QuotationCalculationEngine.calculate_line_item(
                    product=product,
                    quantity=line_input.quantity,
                    unit_price_override=line_input.unit_price,
                    discount_percent=line_input.discount_percent,
                    tax_rate=line_input.tax_rate,
                    notes=line_input.notes,
                )
                line_calc["line_number"] = idx
                calculated_lines.append(line_calc)
            except ValueError as val_err:
                raise ApplicationError(str(val_err), code="VALIDATION_ERROR", status_code=400)

        # Consolidate header totals and overall discounts (Phases 192, 194, 195)
        try:
            totals = QuotationCalculationEngine.calculate_quotation_totals(
                line_results=calculated_lines,
                overall_discount_percent=payload.overall_discount_percent,
            )
        except ValueError as val_err:
            raise ApplicationError(str(val_err), code="VALIDATION_ERROR", status_code=400)

        # Phase 187: Deterministic unique quote number generation
        quote_number = QuotationNumberGenerator.generate_number(db, company_id)

        # Persist Quotation Header
        quotation = Quotation(
            company_id=company_id,
            customer_id=customer.id,
            user_id=current_user.id,
            quotation_number=quote_number,
            status=QuotationStatus.DRAFT.value,
            subtotal=totals["subtotal"],
            line_discount_total=totals["line_discount_total"],
            overall_discount_percent=totals["overall_discount_percent"],
            overall_discount_amount=totals["overall_discount_amount"],
            total_discount=totals["total_discount"],
            taxable_amount=totals["taxable_amount"],
            tax_amount=totals["tax_amount"],
            total_amount=totals["total_amount"],
            total_cost=totals["total_cost"],
            gross_profit=totals["gross_profit"],
            margin_percentage=totals["margin_percentage"],
            is_negative_margin=totals["is_negative_margin"],
            valid_until=payload.valid_until,
            notes=payload.notes,
            terms_conditions=payload.terms_conditions,
        )
        db.add(quotation)
        db.flush()

        # Persist Quotation Line Items
        for line_data in calculated_lines:
            line_item = QuotationLineItem(
                quotation_id=quotation.id,
                product_id=line_data["product_id"],
                line_number=line_data["line_number"],
                quantity=line_data["quantity"],
                unit_price=line_data["unit_price"],
                unit_cost=line_data["unit_cost"],
                discount_percent=line_data["discount_percent"],
                discount_amount=line_data["discount_amount"],
                tax_rate=line_data["tax_rate"],
                tax_amount=line_data["tax_amount"],
                subtotal=line_data["subtotal"],
                net_amount=line_data["net_amount"],
                total_amount=line_data["total_amount"],
                line_cost=line_data["line_cost"],
                gross_profit=line_data["gross_profit"],
                margin_percentage=line_data["margin_percentage"],
                notes=line_data["notes"],
            )
            db.add(line_item)

        # Audit Logging
        db.add(
            AuditLog(
                company_id=company_id,
                user_id=current_user.id,
                action="CREATE",
                resource_type="quotation",
                resource_id=str(quotation.id),
                context_metadata={
                    "quotation_number": quotation.quotation_number,
                    "customer_id": str(customer.id),
                    "total_amount": str(quotation.total_amount),
                    "gross_profit": str(quotation.gross_profit),
                    "margin_percentage": str(quotation.margin_percentage),
                },
            )
        )

        db.commit()
        db.refresh(quotation)
        logger.info(f"Quotation {quotation.quotation_number} created by user {current_user.id}")
        return cls._to_detail_dto(quotation)

    @classmethod
    def get_quotation(
        cls,
        db: Session,
        current_user: User,
        quotation_id: uuid.UUID,
    ) -> QuotationDetailResponse:
        """Retrieve quotation detail by ID with strict tenant isolation (Phase 186)."""
        company_id = cls._verify_tenant(current_user)

        quotation = db.scalars(
            select(Quotation).where(
                Quotation.id == quotation_id,
                Quotation.company_id == company_id,
            )
        ).one_or_none()

        if not quotation:
            raise ApplicationError(
                f"Quotation {quotation_id} not found in current organization",
                code="QUOTATION_NOT_FOUND",
                status_code=404,
            )
        return cls._to_detail_dto(quotation)

    @classmethod
    def list_quotations(
        cls,
        db: Session,
        current_user: User,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        search: Optional[str] = None,
        customer_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[QuotationSummaryResponse], int]:
        """Paginated list of quotations with tenant isolation and filtering (Phase 186)."""
        company_id = cls._verify_tenant(current_user)

        query = select(Quotation).where(Quotation.company_id == company_id)

        if status:
            query = query.where(Quotation.status == status.upper())

        if customer_id:
            query = query.where(Quotation.customer_id == customer_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.join(Quotation.customer).where(
                (Quotation.quotation_number.ilike(search_pattern))
                | (Customer.name.ilike(search_pattern))
                | (Customer.customer_code.ilike(search_pattern))
            )

        total_stmt = select(func.count()).select_from(query.subquery())
        total = db.scalar(total_stmt) or 0

        items = db.scalars(
            query.order_by(desc(Quotation.created_at)).offset(skip).limit(limit)
        ).all()

        dtos = [cls._to_summary_dto(q) for q in items]
        return dtos, total

    @classmethod
    def update_quotation(
        cls,
        db: Session,
        current_user: User,
        quotation_id: uuid.UUID,
        payload: QuotationUpdate,
    ) -> QuotationDetailResponse:
        """Update draft quotation metadata and line items (Phase 186–195)."""
        company_id = cls._verify_tenant(current_user)

        quotation = db.scalars(
            select(Quotation).where(
                Quotation.id == quotation_id,
                Quotation.company_id == company_id,
            )
        ).one_or_none()

        if not quotation:
            raise ApplicationError(
                f"Quotation {quotation_id} not found in current organization",
                code="QUOTATION_NOT_FOUND",
                status_code=404,
            )

        # Editable check
        if quotation.status not in (QuotationStatus.DRAFT.value, QuotationStatus.REJECTED.value):
            raise ApplicationError(
                f"Quotation in '{quotation.status}' status cannot be modified. Only DRAFT or REJECTED quotes are editable.",
                code="QUOTATION_LOCKED",
                status_code=400,
            )

        # Customer update check
        if payload.customer_id is not None and payload.customer_id != quotation.customer_id:
            cls._verify_customer(db, company_id, payload.customer_id)
            quotation.customer_id = payload.customer_id

        if payload.valid_until is not None:
            quotation.valid_until = payload.valid_until
        if payload.notes is not None:
            quotation.notes = payload.notes
        if payload.terms_conditions is not None:
            quotation.terms_conditions = payload.terms_conditions

        # Line items update
        if payload.line_items is not None:
            # Delete old line items
            for old_item in list(quotation.line_items):
                db.delete(old_item)
            db.flush()

            # Process new line items
            calculated_lines: List[Dict[str, Any]] = []
            for idx, line_input in enumerate(payload.line_items, start=1):
                product = cls._verify_product(db, line_input.product_id)
                try:
                    line_calc = QuotationCalculationEngine.calculate_line_item(
                        product=product,
                        quantity=line_input.quantity,
                        unit_price_override=line_input.unit_price,
                        discount_percent=line_input.discount_percent,
                        tax_rate=line_input.tax_rate,
                        notes=line_input.notes,
                    )
                    line_calc["line_number"] = idx
                    calculated_lines.append(line_calc)
                except ValueError as val_err:
                    raise ApplicationError(str(val_err), code="VALIDATION_ERROR", status_code=400)

            ov_disc = payload.overall_discount_percent if payload.overall_discount_percent is not None else quotation.overall_discount_percent
            totals = QuotationCalculationEngine.calculate_quotation_totals(
                line_results=calculated_lines,
                overall_discount_percent=ov_disc,
            )

            for line_data in calculated_lines:
                line_item = QuotationLineItem(
                    quotation_id=quotation.id,
                    product_id=line_data["product_id"],
                    line_number=line_data["line_number"],
                    quantity=line_data["quantity"],
                    unit_price=line_data["unit_price"],
                    unit_cost=line_data["unit_cost"],
                    discount_percent=line_data["discount_percent"],
                    discount_amount=line_data["discount_amount"],
                    tax_rate=line_data["tax_rate"],
                    tax_amount=line_data["tax_amount"],
                    subtotal=line_data["subtotal"],
                    net_amount=line_data["net_amount"],
                    total_amount=line_data["total_amount"],
                    line_cost=line_data["line_cost"],
                    gross_profit=line_data["gross_profit"],
                    margin_percentage=line_data["margin_percentage"],
                    notes=line_data["notes"],
                )
                db.add(line_item)

            quotation.subtotal = totals["subtotal"]
            quotation.line_discount_total = totals["line_discount_total"]
            quotation.overall_discount_percent = totals["overall_discount_percent"]
            quotation.overall_discount_amount = totals["overall_discount_amount"]
            quotation.total_discount = totals["total_discount"]
            quotation.taxable_amount = totals["taxable_amount"]
            quotation.tax_amount = totals["tax_amount"]
            quotation.total_amount = totals["total_amount"]
            quotation.total_cost = totals["total_cost"]
            quotation.gross_profit = totals["gross_profit"]
            quotation.margin_percentage = totals["margin_percentage"]
            quotation.is_negative_margin = totals["is_negative_margin"]

        elif payload.overall_discount_percent is not None:
            # Recompute totals with updated overall discount on existing line items
            existing_lines_calc = []
            for li in quotation.line_items:
                existing_lines_calc.append({
                    "subtotal": li.subtotal,
                    "discount_amount": li.discount_amount,
                    "net_amount": li.net_amount,
                    "tax_amount": li.tax_amount,
                    "line_cost": li.line_cost,
                })
            totals = QuotationCalculationEngine.calculate_quotation_totals(
                line_results=existing_lines_calc,
                overall_discount_percent=payload.overall_discount_percent,
            )
            quotation.overall_discount_percent = totals["overall_discount_percent"]
            quotation.overall_discount_amount = totals["overall_discount_amount"]
            quotation.total_discount = totals["total_discount"]
            quotation.taxable_amount = totals["taxable_amount"]
            quotation.tax_amount = totals["tax_amount"]
            quotation.total_amount = totals["total_amount"]
            quotation.gross_profit = totals["gross_profit"]
            quotation.margin_percentage = totals["margin_percentage"]
            quotation.is_negative_margin = totals["is_negative_margin"]

        # Audit Log
        db.add(
            AuditLog(
                company_id=company_id,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="quotation",
                resource_id=str(quotation.id),
                context_metadata={
                    "quotation_number": quotation.quotation_number,
                    "total_amount": str(quotation.total_amount),
                    "gross_profit": str(quotation.gross_profit),
                },
            )
        )

        db.commit()
        db.refresh(quotation)
        logger.info(f"Quotation {quotation.quotation_number} updated by user {current_user.id}")
        return cls._to_detail_dto(quotation)

    @classmethod
    def cancel_quotation(
        cls,
        db: Session,
        current_user: User,
        quotation_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> QuotationDetailResponse:
        """Cancel an active or draft quotation (Phase 186)."""
        company_id = cls._verify_tenant(current_user)

        quotation = db.scalars(
            select(Quotation).where(
                Quotation.id == quotation_id,
                Quotation.company_id == company_id,
            )
        ).one_or_none()

        if not quotation:
            raise ApplicationError(
                f"Quotation {quotation_id} not found in current organization",
                code="QUOTATION_NOT_FOUND",
                status_code=404,
            )

        if quotation.status == QuotationStatus.CANCELLED.value:
            return cls._to_detail_dto(quotation)

        old_status = quotation.status
        quotation.status = QuotationStatus.CANCELLED.value

        db.add(
            AuditLog(
                company_id=company_id,
                user_id=current_user.id,
                action="CANCEL",
                resource_type="quotation",
                resource_id=str(quotation.id),
                context_metadata={
                    "quotation_number": quotation.quotation_number,
                    "old_status": old_status,
                    "reason": reason,
                },
            )
        )

        db.commit()
        db.refresh(quotation)
        logger.info(f"Quotation {quotation.quotation_number} cancelled by {current_user.id}")
        return cls._to_detail_dto(quotation)

    @classmethod
    def delete_quotation(
        cls,
        db: Session,
        current_user: User,
        quotation_id: uuid.UUID,
    ) -> None:
        """Delete quotation if in DRAFT or CANCELLED status (Phase 186)."""
        company_id = cls._verify_tenant(current_user)

        quotation = db.scalars(
            select(Quotation).where(
                Quotation.id == quotation_id,
                Quotation.company_id == company_id,
            )
        ).one_or_none()

        if not quotation:
            raise ApplicationError(
                f"Quotation {quotation_id} not found in current organization",
                code="QUOTATION_NOT_FOUND",
                status_code=404,
            )

        if quotation.status not in (QuotationStatus.DRAFT.value, QuotationStatus.CANCELLED.value):
            raise ApplicationError(
                f"Cannot delete quotation in '{quotation.status}' status. Only DRAFT or CANCELLED quotations can be deleted.",
                code="CANNOT_DELETE_ACTIVE_QUOTATION",
                status_code=400,
            )

        q_num = quotation.quotation_number
        db.add(
            AuditLog(
                company_id=company_id,
                user_id=current_user.id,
                action="DELETE",
                resource_type="quotation",
                resource_id=str(quotation.id),
                context_metadata={"quotation_number": q_num},
            )
        )

        db.delete(quotation)
        db.commit()
        logger.info(f"Quotation {q_num} deleted by {current_user.id}")

    @classmethod
    def calculate_transient(
        cls,
        db: Session,
        current_user: User,
        payload: QuotationCalculationRequest,
    ) -> QuotationCalculationResponse:
        """Perform dry-run calculations for prices, taxes, and margins without persistence (Phases 190–195)."""
        cls._verify_tenant(current_user)

        calculated_lines: List[Dict[str, Any]] = []
        for idx, line_input in enumerate(payload.line_items, start=1):
            product = cls._verify_product(db, line_input.product_id)
            try:
                line_calc = QuotationCalculationEngine.calculate_line_item(
                    product=product,
                    quantity=line_input.quantity,
                    unit_price_override=line_input.unit_price,
                    discount_percent=line_input.discount_percent,
                    tax_rate=line_input.tax_rate,
                    notes=line_input.notes,
                )
                line_calc["line_number"] = idx
                calculated_lines.append(line_calc)
            except ValueError as val_err:
                raise ApplicationError(str(val_err), code="VALIDATION_ERROR", status_code=400)

        try:
            totals = QuotationCalculationEngine.calculate_quotation_totals(
                line_results=calculated_lines,
                overall_discount_percent=payload.overall_discount_percent,
            )
        except ValueError as val_err:
            raise ApplicationError(str(val_err), code="VALIDATION_ERROR", status_code=400)

        now = datetime.now(timezone.utc)
        response_lines: List[QuotationLineItemResponse] = []
        for line in calculated_lines:
            response_lines.append(
                QuotationLineItemResponse(
                    id=uuid.uuid4(),
                    quotation_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                    product_id=line["product_id"],
                    line_number=line["line_number"],
                    quantity=line["quantity"],
                    unit_price=line["unit_price"],
                    unit_cost=line["unit_cost"],
                    discount_percent=line["discount_percent"],
                    discount_amount=line["discount_amount"],
                    tax_rate=line["tax_rate"],
                    tax_amount=line["tax_amount"],
                    subtotal=line["subtotal"],
                    net_amount=line["net_amount"],
                    total_amount=line["total_amount"],
                    line_cost=line["line_cost"],
                    gross_profit=line["gross_profit"],
                    margin_percentage=line["margin_percentage"],
                    notes=line["notes"],
                    created_at=now,
                    updated_at=now,
                    product_sku=line["product_sku"],
                    product_name=line["product_name"],
                )
            )

        return QuotationCalculationResponse(
            subtotal=totals["subtotal"],
            line_discount_total=totals["line_discount_total"],
            overall_discount_percent=totals["overall_discount_percent"],
            overall_discount_amount=totals["overall_discount_amount"],
            total_discount=totals["total_discount"],
            taxable_amount=totals["taxable_amount"],
            tax_amount=totals["tax_amount"],
            total_amount=totals["total_amount"],
            total_cost=totals["total_cost"],
            gross_profit=totals["gross_profit"],
            margin_percentage=totals["margin_percentage"],
            is_negative_margin=totals["is_negative_margin"],
            lines=response_lines,
        )

    # --------------------------------------------------------------------------
    # Helper DTO Converters
    # --------------------------------------------------------------------------

    @classmethod
    def _to_summary_dto(cls, q: Quotation) -> QuotationSummaryResponse:
        cust_name = q.customer.name if q.customer else None
        cust_code = q.customer.customer_code if q.customer else None
        author_name = f"{q.user.first_name} {q.user.last_name}" if q.user else None

        return QuotationSummaryResponse(
            id=q.id,
            company_id=q.company_id,
            customer_id=q.customer_id,
            customer_name=cust_name,
            customer_code=cust_code,
            user_id=q.user_id,
            author_name=author_name,
            quotation_number=q.quotation_number,
            status=q.status,
            subtotal=q.subtotal,
            total_discount=q.total_discount,
            tax_amount=q.tax_amount,
            total_amount=q.total_amount,
            gross_profit=q.gross_profit,
            margin_percentage=q.margin_percentage,
            is_negative_margin=q.is_negative_margin,
            line_items_count=len(q.line_items),
            valid_until=q.valid_until,
            created_at=q.created_at,
            updated_at=q.updated_at,
        )

    @classmethod
    def _to_detail_dto(cls, q: Quotation) -> QuotationDetailResponse:
        cust_name = q.customer.name if q.customer else None
        cust_code = q.customer.customer_code if q.customer else None
        author_name = f"{q.user.first_name} {q.user.last_name}" if q.user else None

        line_dtos: List[QuotationLineItemResponse] = []
        for li in q.line_items:
            line_dtos.append(
                QuotationLineItemResponse(
                    id=li.id,
                    quotation_id=li.quotation_id,
                    product_id=li.product_id,
                    line_number=li.line_number,
                    quantity=li.quantity,
                    unit_price=li.unit_price,
                    unit_cost=li.unit_cost,
                    discount_percent=li.discount_percent,
                    discount_amount=li.discount_amount,
                    tax_rate=li.tax_rate,
                    tax_amount=li.tax_amount,
                    subtotal=li.subtotal,
                    net_amount=li.net_amount,
                    total_amount=li.total_amount,
                    line_cost=li.line_cost,
                    gross_profit=li.gross_profit,
                    margin_percentage=li.margin_percentage,
                    notes=li.notes,
                    created_at=li.created_at,
                    updated_at=li.updated_at,
                    product_sku=li.product.sku if li.product else None,
                    product_name=li.product.name if li.product else None,
                )
            )

        return QuotationDetailResponse(
            id=q.id,
            company_id=q.company_id,
            customer_id=q.customer_id,
            customer_name=cust_name,
            customer_code=cust_code,
            user_id=q.user_id,
            author_name=author_name,
            quotation_number=q.quotation_number,
            status=q.status,
            subtotal=q.subtotal,
            total_discount=q.total_discount,
            tax_amount=q.tax_amount,
            total_amount=q.total_amount,
            gross_profit=q.gross_profit,
            margin_percentage=q.margin_percentage,
            is_negative_margin=q.is_negative_margin,
            line_items_count=len(q.line_items),
            valid_until=q.valid_until,
            created_at=q.created_at,
            updated_at=q.updated_at,
            notes=q.notes,
            terms_conditions=q.terms_conditions,
            line_discount_total=q.line_discount_total,
            overall_discount_percent=q.overall_discount_percent,
            overall_discount_amount=q.overall_discount_amount,
            taxable_amount=q.taxable_amount,
            total_cost=q.total_cost,
            line_items=line_dtos,
        )
