"""Customer Service Layer for DealFlow360 (Phases 056–060).

Handles customer lifecycle, tier management, purchase/deal history,
strict multi-tenant company isolation, permission enforcement, and audit trail logging.
"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import ApplicationError
from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.customer_purchase_history import CustomerPurchaseHistory
from app.models.customer_tier import CustomerTier
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    DealHistoryCreate,
    DiscountHistoryCreate,
    PaymentHistoryCreate,
    PurchaseHistoryCreate,
)
from app.services.authorization import AuthorizationService


class CustomerService:
    """Business logic for Customer Management Foundation."""

    @classmethod
    def get_customers(
        cls,
        db: Session,
        current_user: User,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        tier_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[Customer], int]:
        """List customers scoped to the user's company (unless Admin) with multi-field search and filters."""
        # Authorization check: read permission required
        query = select(Customer).options(joinedload(Customer.tier))

        # Tenant isolation
        if not AuthorizationService.can_access_company_resource(current_user, current_user.company_id):
            return [], 0

        # System administrators can see all or their company, regular users are bound to their company
        from app.services.rbac import RBACRoleNames, RBACService
        if not RBACService.has_role(current_user, RBACRoleNames.ADMIN):
            if current_user.company_id is None:
                return [], 0
            query = query.where(Customer.company_id == current_user.company_id)

        if is_active is not None:
            query = query.where(Customer.is_active == is_active)

        if tier_id is not None:
            query = query.where(Customer.tier_id == tier_id)

        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Customer.name).like(search_term),
                    func.lower(Customer.customer_code).like(search_term),
                    func.lower(Customer.email).like(search_term),
                    func.lower(Customer.phone).like(search_term),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_query) or 0

        # Paginate and order by created_at desc
        results = db.scalars(
            query.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
        ).unique().all()

        return list(results), total

    @classmethod
    def get_customer(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
    ) -> Customer:
        """Retrieve single customer with authorization and tenant boundary verification."""
        customer = db.scalars(
            select(Customer)
            .options(joinedload(Customer.tier))
            .where(Customer.id == customer_id)
        ).first()

        if not customer:
            raise ApplicationError(
                message="Customer not found",
                code="CUSTOMER_NOT_FOUND",
                status_code=404,
            )

        # Assert object-level access and customers:read permission
        AuthorizationService.assert_customer_access(current_user, customer, action="read")
        return customer

    @classmethod
    def create_customer(
        cls,
        db: Session,
        current_user: User,
        data: CustomerCreate,
    ) -> Customer:
        """Create a new customer within the user's company with duplicate checks."""
        # Determine target company
        company_id = current_user.company_id
        if not company_id:
            raise ApplicationError(
                message="Cannot create customer: user has no assigned company",
                code="COMPANY_REQUIRED",
                status_code=400,
            )

        # Assert company access
        AuthorizationService.assert_company_access(current_user, company_id)

        # Ensure unique customer_code within company
        existing = db.scalars(
            select(Customer).where(
                Customer.company_id == company_id,
                func.upper(Customer.customer_code) == data.customer_code.upper(),
            )
        ).first()
        if existing:
            raise ApplicationError(
                message=f"Customer with code '{data.customer_code}' already exists in your organization",
                code="DUPLICATE_CUSTOMER_CODE",
                status_code=409,
            )

        # Validate tier_id if supplied
        if data.tier_id:
            tier = db.get(CustomerTier, data.tier_id)
            if not tier or not tier.is_active:
                raise ApplicationError(
                    message="Specified CustomerTier is invalid or inactive",
                    code="INVALID_TIER",
                    status_code=400,
                )

        customer = Customer(
            company_id=company_id,
            customer_code=data.customer_code.upper(),
            name=data.name.strip(),
            email=data.email,
            phone=data.phone,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
            tier_id=data.tier_id,
            is_active=data.is_active,
        )
        db.add(customer)
        db.flush()

        # Audit log entry
        audit = AuditLog(
            user_id=current_user.id,
            company_id=company_id,
            action="CREATE",
            resource_type="customer",
            resource_id=str(customer.id),
            details=f"Created customer '{customer.name}' ({customer.customer_code})",
            context_metadata={"customer_code": customer.customer_code, "tier_id": str(customer.tier_id) if customer.tier_id else None},
        )
        db.add(audit)
        db.commit()
        db.refresh(customer)

        logger.info(f"Customer created: {customer.id} by user {current_user.id}")
        return customer

    @classmethod
    def update_customer(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
        data: CustomerUpdate,
    ) -> Customer:
        """Update existing customer attributes."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="write")

        # Validate tier_id if being modified
        if data.tier_id is not None:
            tier = db.get(CustomerTier, data.tier_id)
            if not tier or not tier.is_active:
                raise ApplicationError(
                    message="Specified CustomerTier is invalid or inactive",
                    code="INVALID_TIER",
                    status_code=400,
                )
            customer.tier_id = data.tier_id

        # Update specified fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != "tier_id" and hasattr(customer, field):
                setattr(customer, field, value)

        # Audit log entry
        audit = AuditLog(
            user_id=current_user.id,
            company_id=customer.company_id,
            action="UPDATE",
            resource_type="customer",
            resource_id=str(customer.id),
            details=f"Updated customer '{customer.name}' ({customer.customer_code})",
            context_metadata={"updated_fields": list(update_data.keys())},
        )
        db.add(audit)
        db.commit()
        db.refresh(customer)

        logger.info(f"Customer updated: {customer.id} by user {current_user.id}")
        return customer

    @classmethod
    def update_customer_tier(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
        tier_id: Optional[uuid.UUID],
    ) -> Customer:
        """Assign or reassign a customer discount tier (Phase 058)."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="write")

        old_tier_id = customer.tier_id
        if tier_id is not None:
            tier = db.get(CustomerTier, tier_id)
            if not tier or not tier.is_active:
                raise ApplicationError(
                    message="Specified CustomerTier does not exist or is inactive",
                    code="INVALID_TIER",
                    status_code=400,
                )
            customer.tier_id = tier.id
        else:
            customer.tier_id = None

        # Audit log
        audit = AuditLog(
            user_id=current_user.id,
            company_id=customer.company_id,
            action="TIER_CHANGE",
            resource_type="customer",
            resource_id=str(customer.id),
            details=f"Changed tier for customer '{customer.name}' from {old_tier_id} to {customer.tier_id}",
            context_metadata={"old_tier_id": str(old_tier_id) if old_tier_id else None, "new_tier_id": str(customer.tier_id) if customer.tier_id else None},
        )
        db.add(audit)
        db.commit()
        db.refresh(customer)

        logger.info(f"Customer {customer.id} tier updated to {customer.tier_id} by user {current_user.id}")
        return customer

    @classmethod
    def delete_customer(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
        soft_delete: bool = True,
    ) -> None:
        """Deactivate (soft delete) or remove customer account."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="delete")

        if soft_delete:
            customer.is_active = False
            audit_action = "DEACTIVATE"
            audit_details = f"Soft-deleted customer '{customer.name}' ({customer.customer_code})"
        else:
            db.delete(customer)
            audit_action = "DELETE"
            audit_details = f"Permanently deleted customer '{customer.name}' ({customer.customer_code})"

        audit = AuditLog(
            user_id=current_user.id,
            company_id=customer.company_id,
            action=audit_action,
            resource_type="customer",
            resource_id=str(customer.id),
            details=audit_details,
            context_metadata={"customer_code": customer.customer_code},
        )
        db.add(audit)
        db.commit()

        logger.info(f"Customer {customer_id} deleted (soft={soft_delete}) by user {current_user.id}")

    # -----------------------------------------------------------------------
    # Purchase History (Phase 059)
    # -----------------------------------------------------------------------

    @classmethod
    def get_purchase_history(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
    ) -> List[CustomerPurchaseHistory]:
        """Retrieve purchase history for a validated customer."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="read")

        records = db.scalars(
            select(CustomerPurchaseHistory)
            .where(
                CustomerPurchaseHistory.customer_id == customer_id,
                CustomerPurchaseHistory.company_id == customer.company_id,
            )
            .order_by(CustomerPurchaseHistory.purchase_date.desc())
        ).all()
        return list(records)

    @classmethod
    def create_purchase_history_entry(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
        data: PurchaseHistoryCreate,
    ) -> CustomerPurchaseHistory:
        """Add purchase record for customer."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="write")

        entry = CustomerPurchaseHistory(
            company_id=customer.company_id,
            customer_id=customer.id,
            order_number=data.order_number.strip(),
            purchase_date=data.purchase_date,
            total_amount=data.total_amount,
            status=data.status,
            item_count=data.item_count,
            notes=data.notes,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    # -----------------------------------------------------------------------
    # Deal History (Phase 060)
    # -----------------------------------------------------------------------

    @classmethod
    def get_deal_history(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
    ) -> List[CustomerDealHistory]:
        """Retrieve deal history for a validated customer."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="read")

        records = db.scalars(
            select(CustomerDealHistory)
            .where(
                CustomerDealHistory.customer_id == customer_id,
                CustomerDealHistory.company_id == customer.company_id,
            )
            .order_by(CustomerDealHistory.created_at.desc())
        ).all()
        return list(records)

    @classmethod
    def create_deal_history_entry(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
        data: DealHistoryCreate,
    ) -> CustomerDealHistory:
        """Add deal record for customer."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="write")

        entry = CustomerDealHistory(
            company_id=customer.company_id,
            customer_id=customer.id,
            deal_code=data.deal_code.strip(),
            title=data.title.strip(),
            deal_value=data.deal_value,
            status=data.status,
            sales_rep_name=data.sales_rep_name,
            closed_date=data.closed_date,
            notes=data.notes,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    # -----------------------------------------------------------------------
    # Discount History (Phase 061)
    # -----------------------------------------------------------------------

    @classmethod
    def get_discount_history(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
    ) -> List[CustomerDiscountHistory]:
        """Retrieve discount history for a validated customer."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="read")

        records = db.scalars(
            select(CustomerDiscountHistory)
            .where(
                CustomerDiscountHistory.customer_id == customer_id,
                CustomerDiscountHistory.company_id == customer.company_id,
            )
            .order_by(CustomerDiscountHistory.applied_at.desc())
        ).all()
        return list(records)

    @classmethod
    def create_discount_history_entry(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
        data: DiscountHistoryCreate,
    ) -> CustomerDiscountHistory:
        """Add discount history record for customer."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="write")

        entry = CustomerDiscountHistory(
            company_id=customer.company_id,
            customer_id=customer.id,
            discount_code=data.discount_code.strip().upper(),
            discount_percentage=data.discount_percentage,
            discount_amount=data.discount_amount,
            deal_reference=data.deal_reference,
            reason=data.reason,
            applied_at=data.applied_at,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    # -----------------------------------------------------------------------
    # Payment History (Phase 062)
    # -----------------------------------------------------------------------

    @classmethod
    def get_payment_history(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
    ) -> List[CustomerPaymentHistory]:
        """Retrieve payment history for a validated customer."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="read")

        records = db.scalars(
            select(CustomerPaymentHistory)
            .where(
                CustomerPaymentHistory.customer_id == customer_id,
                CustomerPaymentHistory.company_id == customer.company_id,
            )
            .order_by(CustomerPaymentHistory.payment_date.desc())
        ).all()
        return list(records)

    @classmethod
    def create_payment_history_entry(
        cls,
        db: Session,
        current_user: User,
        customer_id: uuid.UUID,
        data: PaymentHistoryCreate,
    ) -> CustomerPaymentHistory:
        """Add payment transaction record for customer."""
        customer = cls.get_customer(db, current_user, customer_id)
        AuthorizationService.assert_customer_access(current_user, customer, action="write")

        entry = CustomerPaymentHistory(
            company_id=customer.company_id,
            customer_id=customer.id,
            payment_reference=data.payment_reference.strip().upper(),
            amount=data.amount,
            status=data.status,
            payment_method=data.payment_method,
            transaction_reference=data.transaction_reference,
            payment_date=data.payment_date,
            notes=data.notes,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
