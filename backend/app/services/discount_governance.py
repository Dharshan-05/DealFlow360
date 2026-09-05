"""Discount Governance Services (Phases 101–105).

Provides centralized business logic, validation, duplicate active checking,
and audit logging for:
- Phase 101: Discount Configuration
- Phase 102: Customer Discount Ceiling
- Phase 103: Category Discount Ceiling
- Phase 104: Product Discount Ceiling
- Phase 105: Sales Rep Authority Limit
"""
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.category_discount_ceiling import CategoryDiscountCeiling
from app.models.customer import Customer
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.discount_configuration import DiscountConfiguration
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_discount_ceiling import ProductDiscountCeiling
from app.models.sales_rep_authority_limit import SalesRepAuthorityLimit
from app.models.user import User
from app.schemas.discount_governance import (
    CategoryDiscountCeilingCreate,
    CategoryDiscountCeilingListResponse,
    CategoryDiscountCeilingResponse,
    CategoryDiscountCeilingUpdate,
    CustomerDiscountCeilingCreate,
    CustomerDiscountCeilingListResponse,
    CustomerDiscountCeilingResponse,
    CustomerDiscountCeilingUpdate,
    DiscountConfigurationCreate,
    DiscountConfigurationListResponse,
    DiscountConfigurationResponse,
    DiscountConfigurationUpdate,
    ProductDiscountCeilingCreate,
    ProductDiscountCeilingListResponse,
    ProductDiscountCeilingResponse,
    ProductDiscountCeilingUpdate,
    SalesRepAuthorityLimitCreate,
    SalesRepAuthorityLimitListResponse,
    SalesRepAuthorityLimitResponse,
    SalesRepAuthorityLimitUpdate,
)


# ==============================================================================
# Phase 101: Discount Configuration Service
# ==============================================================================

class DiscountConfigurationService:
    @classmethod
    def create(
        cls,
        db: Session,
        company_id: uuid.UUID,
        payload: DiscountConfigurationCreate,
        current_user: Optional[User] = None,
    ) -> DiscountConfiguration:
        if payload.default_discount_ceiling < 0 or payload.default_discount_ceiling > 100:
            raise ValidationError("Default discount ceiling must be between 0 and 100 percent.")
        if payload.effective_until and payload.effective_until < payload.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        config = DiscountConfiguration(
            company_id=company_id,
            name=payload.name,
            description=payload.description,
            default_discount_ceiling=payload.default_discount_ceiling,
            is_active=payload.is_active,
            effective_from=payload.effective_from,
            effective_until=payload.effective_until,
            created_by_id=current_user.id if current_user else None,
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        if current_user:
            audit = AuditLog(
                action="DISCOUNT_CONFIGURATION_CREATED",
                resource_type="discount_configuration",
                resource_id=str(config.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "name": config.name,
                    "default_discount_ceiling": float(config.default_discount_ceiling),
                    "is_active": config.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return config

    @classmethod
    def get(cls, db: Session, config_id: uuid.UUID, company_id: uuid.UUID) -> DiscountConfiguration:
        config = (
            db.query(DiscountConfiguration)
            .filter(DiscountConfiguration.id == config_id, DiscountConfiguration.company_id == company_id)
            .first()
        )
        if not config:
            raise NotFoundError(f"Discount configuration with id {config_id} not found.")
        return config

    @classmethod
    def list(
        cls,
        db: Session,
        company_id: uuid.UUID,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> DiscountConfigurationListResponse:
        query = db.query(DiscountConfiguration).filter(DiscountConfiguration.company_id == company_id)
        if is_active is not None:
            query = query.filter(DiscountConfiguration.is_active == is_active)

        total = query.count()
        items = query.order_by(DiscountConfiguration.created_at.desc()).offset(skip).limit(limit).all()

        return DiscountConfigurationListResponse(
            items=[DiscountConfigurationResponse.model_validate(item) for item in items],
            total=total,
        )

    @classmethod
    def update(
        cls,
        db: Session,
        config_id: uuid.UUID,
        company_id: uuid.UUID,
        payload: DiscountConfigurationUpdate,
        current_user: Optional[User] = None,
    ) -> DiscountConfiguration:
        config = cls.get(db, config_id, company_id)

        if payload.name is not None:
            config.name = payload.name
        if payload.description is not None:
            config.description = payload.description
        if payload.default_discount_ceiling is not None:
            if payload.default_discount_ceiling < 0 or payload.default_discount_ceiling > 100:
                raise ValidationError("Default discount ceiling must be between 0 and 100 percent.")
            config.default_discount_ceiling = payload.default_discount_ceiling
        if payload.is_active is not None:
            config.is_active = payload.is_active
        if payload.effective_from is not None:
            config.effective_from = payload.effective_from
        if payload.effective_until is not None:
            config.effective_until = payload.effective_until

        if config.effective_until and config.effective_until < config.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        db.commit()
        db.refresh(config)

        if current_user:
            audit = AuditLog(
                action="DISCOUNT_CONFIGURATION_UPDATED",
                resource_type="discount_configuration",
                resource_id=str(config.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "name": config.name,
                    "default_discount_ceiling": float(config.default_discount_ceiling),
                    "is_active": config.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return config

    @classmethod
    def deactivate(
        cls,
        db: Session,
        config_id: uuid.UUID,
        company_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> DiscountConfiguration:
        config = cls.get(db, config_id, company_id)
        config.is_active = False
        db.commit()
        db.refresh(config)

        if current_user:
            audit = AuditLog(
                action="DISCOUNT_CONFIGURATION_DEACTIVATED",
                resource_type="discount_configuration",
                resource_id=str(config.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "name": config.name,
                    "is_active": False,
                },
            )
            db.add(audit)
            db.commit()

        return config


# ==============================================================================
# Phase 102: Customer Discount Ceiling Service
# ==============================================================================

class CustomerDiscountCeilingService:
    @classmethod
    def create(
        cls,
        db: Session,
        company_id: uuid.UUID,
        payload: CustomerDiscountCeilingCreate,
        current_user: Optional[User] = None,
    ) -> CustomerDiscountCeiling:
        if payload.max_discount_percentage < 0 or payload.max_discount_percentage > 100:
            raise ValidationError("Maximum discount percentage must be between 0 and 100 percent.")
        if payload.effective_until and payload.effective_until < payload.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        # Ensure customer exists and belongs to company
        customer = (
            db.query(Customer)
            .filter(Customer.id == payload.customer_id, Customer.company_id == company_id)
            .first()
        )
        if not customer:
            raise NotFoundError(f"Customer with id {payload.customer_id} not found in this company.")

        # Prevent duplicate active ceiling records
        if payload.is_active:
            active_existing = (
                db.query(CustomerDiscountCeiling)
                .filter(
                    CustomerDiscountCeiling.company_id == company_id,
                    CustomerDiscountCeiling.customer_id == payload.customer_id,
                    CustomerDiscountCeiling.is_active == True,
                )
                .first()
            )
            if active_existing:
                raise ConflictError(
                    f"An active discount ceiling already exists for customer '{customer.name}'. "
                    "Deactivate or update the existing ceiling before creating a new active record."
                )

        ceiling = CustomerDiscountCeiling(
            company_id=company_id,
            customer_id=payload.customer_id,
            max_discount_percentage=payload.max_discount_percentage,
            is_active=payload.is_active,
            effective_from=payload.effective_from,
            effective_until=payload.effective_until,
            created_by_id=current_user.id if current_user else None,
        )
        db.add(ceiling)
        db.commit()
        db.refresh(ceiling)

        if current_user:
            audit = AuditLog(
                action="CUSTOMER_DISCOUNT_CEILING_CREATED",
                resource_type="customer_discount_ceiling",
                resource_id=str(ceiling.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "customer_id": str(customer.id),
                    "customer_name": customer.name,
                    "max_discount_percentage": float(ceiling.max_discount_percentage),
                    "is_active": ceiling.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return ceiling

    @classmethod
    def get(cls, db: Session, ceiling_id: uuid.UUID, company_id: uuid.UUID) -> CustomerDiscountCeiling:
        ceiling = (
            db.query(CustomerDiscountCeiling)
            .filter(CustomerDiscountCeiling.id == ceiling_id, CustomerDiscountCeiling.company_id == company_id)
            .first()
        )
        if not ceiling:
            raise NotFoundError(f"Customer discount ceiling with id {ceiling_id} not found.")
        return ceiling

    @classmethod
    def list(
        cls,
        db: Session,
        company_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> CustomerDiscountCeilingListResponse:
        query = db.query(CustomerDiscountCeiling).filter(CustomerDiscountCeiling.company_id == company_id)
        if customer_id:
            query = query.filter(CustomerDiscountCeiling.customer_id == customer_id)
        if is_active is not None:
            query = query.filter(CustomerDiscountCeiling.is_active == is_active)

        total = query.count()
        items = query.order_by(CustomerDiscountCeiling.created_at.desc()).offset(skip).limit(limit).all()

        return CustomerDiscountCeilingListResponse(
            items=[CustomerDiscountCeilingResponse.model_validate(item) for item in items],
            total=total,
        )

    @classmethod
    def update(
        cls,
        db: Session,
        ceiling_id: uuid.UUID,
        company_id: uuid.UUID,
        payload: CustomerDiscountCeilingUpdate,
        current_user: Optional[User] = None,
    ) -> CustomerDiscountCeiling:
        ceiling = cls.get(db, ceiling_id, company_id)

        if payload.max_discount_percentage is not None:
            if payload.max_discount_percentage < 0 or payload.max_discount_percentage > 100:
                raise ValidationError("Maximum discount percentage must be between 0 and 100 percent.")
            ceiling.max_discount_percentage = payload.max_discount_percentage

        if payload.is_active is not None and payload.is_active != ceiling.is_active:
            if payload.is_active:
                # Activating: ensure no other active ceiling exists for this customer
                active_existing = (
                    db.query(CustomerDiscountCeiling)
                    .filter(
                        CustomerDiscountCeiling.company_id == company_id,
                        CustomerDiscountCeiling.customer_id == ceiling.customer_id,
                        CustomerDiscountCeiling.is_active == True,
                        CustomerDiscountCeiling.id != ceiling.id,
                    )
                    .first()
                )
                if active_existing:
                    raise ConflictError(
                        "Cannot activate ceiling: another active discount ceiling already exists for this customer."
                    )
            ceiling.is_active = payload.is_active

        if payload.effective_from is not None:
            ceiling.effective_from = payload.effective_from
        if payload.effective_until is not None:
            ceiling.effective_until = payload.effective_until

        if ceiling.effective_until and ceiling.effective_until < ceiling.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        db.commit()
        db.refresh(ceiling)

        if current_user:
            audit = AuditLog(
                action="CUSTOMER_DISCOUNT_CEILING_UPDATED",
                resource_type="customer_discount_ceiling",
                resource_id=str(ceiling.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "customer_id": str(ceiling.customer_id),
                    "max_discount_percentage": float(ceiling.max_discount_percentage),
                    "is_active": ceiling.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return ceiling

    @classmethod
    def deactivate(
        cls,
        db: Session,
        ceiling_id: uuid.UUID,
        company_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> CustomerDiscountCeiling:
        ceiling = cls.get(db, ceiling_id, company_id)
        ceiling.is_active = False
        db.commit()
        db.refresh(ceiling)

        if current_user:
            audit = AuditLog(
                action="CUSTOMER_DISCOUNT_CEILING_DEACTIVATED",
                resource_type="customer_discount_ceiling",
                resource_id=str(ceiling.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "customer_id": str(ceiling.customer_id),
                    "is_active": False,
                },
            )
            db.add(audit)
            db.commit()

        return ceiling


# ==============================================================================
# Phase 103: Category Discount Ceiling Service
# ==============================================================================

class CategoryDiscountCeilingService:
    @classmethod
    def create(
        cls,
        db: Session,
        company_id: uuid.UUID,
        payload: CategoryDiscountCeilingCreate,
        current_user: Optional[User] = None,
    ) -> CategoryDiscountCeiling:
        if payload.max_discount_percentage < 0 or payload.max_discount_percentage > 100:
            raise ValidationError("Maximum discount percentage must be between 0 and 100 percent.")
        if payload.effective_until and payload.effective_until < payload.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        # Ensure category exists
        category = db.query(ProductCategory).filter(ProductCategory.id == payload.category_id).first()
        if not category:
            raise NotFoundError(f"Product category with id {payload.category_id} not found.")

        # Prevent duplicate active ceiling records
        if payload.is_active:
            active_existing = (
                db.query(CategoryDiscountCeiling)
                .filter(
                    CategoryDiscountCeiling.company_id == company_id,
                    CategoryDiscountCeiling.category_id == payload.category_id,
                    CategoryDiscountCeiling.is_active == True,
                )
                .first()
            )
            if active_existing:
                raise ConflictError(
                    f"An active discount ceiling already exists for category '{category.name}'. "
                    "Deactivate or update the existing ceiling before creating a new active record."
                )

        ceiling = CategoryDiscountCeiling(
            company_id=company_id,
            category_id=payload.category_id,
            max_discount_percentage=payload.max_discount_percentage,
            is_active=payload.is_active,
            effective_from=payload.effective_from,
            effective_until=payload.effective_until,
            created_by_id=current_user.id if current_user else None,
        )
        db.add(ceiling)
        db.commit()
        db.refresh(ceiling)

        if current_user:
            audit = AuditLog(
                action="CATEGORY_DISCOUNT_CEILING_CREATED",
                resource_type="category_discount_ceiling",
                resource_id=str(ceiling.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "category_id": str(category.id),
                    "category_name": category.name,
                    "max_discount_percentage": float(ceiling.max_discount_percentage),
                    "is_active": ceiling.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return ceiling

    @classmethod
    def get(cls, db: Session, ceiling_id: uuid.UUID, company_id: uuid.UUID) -> CategoryDiscountCeiling:
        ceiling = (
            db.query(CategoryDiscountCeiling)
            .filter(CategoryDiscountCeiling.id == ceiling_id, CategoryDiscountCeiling.company_id == company_id)
            .first()
        )
        if not ceiling:
            raise NotFoundError(f"Category discount ceiling with id {ceiling_id} not found.")
        return ceiling

    @classmethod
    def list(
        cls,
        db: Session,
        company_id: uuid.UUID,
        category_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> CategoryDiscountCeilingListResponse:
        query = db.query(CategoryDiscountCeiling).filter(CategoryDiscountCeiling.company_id == company_id)
        if category_id:
            query = query.filter(CategoryDiscountCeiling.category_id == category_id)
        if is_active is not None:
            query = query.filter(CategoryDiscountCeiling.is_active == is_active)

        total = query.count()
        items = query.order_by(CategoryDiscountCeiling.created_at.desc()).offset(skip).limit(limit).all()

        return CategoryDiscountCeilingListResponse(
            items=[CategoryDiscountCeilingResponse.model_validate(item) for item in items],
            total=total,
        )

    @classmethod
    def update(
        cls,
        db: Session,
        ceiling_id: uuid.UUID,
        company_id: uuid.UUID,
        payload: CategoryDiscountCeilingUpdate,
        current_user: Optional[User] = None,
    ) -> CategoryDiscountCeiling:
        ceiling = cls.get(db, ceiling_id, company_id)

        if payload.max_discount_percentage is not None:
            if payload.max_discount_percentage < 0 or payload.max_discount_percentage > 100:
                raise ValidationError("Maximum discount percentage must be between 0 and 100 percent.")
            ceiling.max_discount_percentage = payload.max_discount_percentage

        if payload.is_active is not None and payload.is_active != ceiling.is_active:
            if payload.is_active:
                active_existing = (
                    db.query(CategoryDiscountCeiling)
                    .filter(
                        CategoryDiscountCeiling.company_id == company_id,
                        CategoryDiscountCeiling.category_id == ceiling.category_id,
                        CategoryDiscountCeiling.is_active == True,
                        CategoryDiscountCeiling.id != ceiling.id,
                    )
                    .first()
                )
                if active_existing:
                    raise ConflictError(
                        "Cannot activate ceiling: another active discount ceiling already exists for this category."
                    )
            ceiling.is_active = payload.is_active

        if payload.effective_from is not None:
            ceiling.effective_from = payload.effective_from
        if payload.effective_until is not None:
            ceiling.effective_until = payload.effective_until

        if ceiling.effective_until and ceiling.effective_until < ceiling.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        db.commit()
        db.refresh(ceiling)

        if current_user:
            audit = AuditLog(
                action="CATEGORY_DISCOUNT_CEILING_UPDATED",
                resource_type="category_discount_ceiling",
                resource_id=str(ceiling.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "category_id": str(ceiling.category_id),
                    "max_discount_percentage": float(ceiling.max_discount_percentage),
                    "is_active": ceiling.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return ceiling

    @classmethod
    def deactivate(
        cls,
        db: Session,
        ceiling_id: uuid.UUID,
        company_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> CategoryDiscountCeiling:
        ceiling = cls.get(db, ceiling_id, company_id)
        ceiling.is_active = False
        db.commit()
        db.refresh(ceiling)

        if current_user:
            audit = AuditLog(
                action="CATEGORY_DISCOUNT_CEILING_DEACTIVATED",
                resource_type="category_discount_ceiling",
                resource_id=str(ceiling.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "category_id": str(ceiling.category_id),
                    "is_active": False,
                },
            )
            db.add(audit)
            db.commit()

        return ceiling


# ==============================================================================
# Phase 104: Product Discount Ceiling Service
# ==============================================================================

class ProductDiscountCeilingService:
    @classmethod
    def create(
        cls,
        db: Session,
        company_id: uuid.UUID,
        payload: ProductDiscountCeilingCreate,
        current_user: Optional[User] = None,
    ) -> ProductDiscountCeiling:
        if payload.max_discount_percentage < 0 or payload.max_discount_percentage > 100:
            raise ValidationError("Maximum discount percentage must be between 0 and 100 percent.")
        if payload.effective_until and payload.effective_until < payload.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        # Ensure product exists
        product = db.query(Product).filter(Product.id == payload.product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {payload.product_id} not found.")

        # Prevent duplicate active ceiling records
        if payload.is_active:
            active_existing = (
                db.query(ProductDiscountCeiling)
                .filter(
                    ProductDiscountCeiling.company_id == company_id,
                    ProductDiscountCeiling.product_id == payload.product_id,
                    ProductDiscountCeiling.is_active == True,
                )
                .first()
            )
            if active_existing:
                raise ConflictError(
                    f"An active discount ceiling already exists for product '{product.sku}'. "
                    "Deactivate or update the existing ceiling before creating a new active record."
                )

        ceiling = ProductDiscountCeiling(
            company_id=company_id,
            product_id=payload.product_id,
            max_discount_percentage=payload.max_discount_percentage,
            is_active=payload.is_active,
            effective_from=payload.effective_from,
            effective_until=payload.effective_until,
            created_by_id=current_user.id if current_user else None,
        )
        db.add(ceiling)
        db.commit()
        db.refresh(ceiling)

        if current_user:
            audit = AuditLog(
                action="PRODUCT_DISCOUNT_CEILING_CREATED",
                resource_type="product_discount_ceiling",
                resource_id=str(ceiling.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "product_id": str(product.id),
                    "product_sku": product.sku,
                    "max_discount_percentage": float(ceiling.max_discount_percentage),
                    "is_active": ceiling.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return ceiling

    @classmethod
    def get(cls, db: Session, ceiling_id: uuid.UUID, company_id: uuid.UUID) -> ProductDiscountCeiling:
        ceiling = (
            db.query(ProductDiscountCeiling)
            .filter(ProductDiscountCeiling.id == ceiling_id, ProductDiscountCeiling.company_id == company_id)
            .first()
        )
        if not ceiling:
            raise NotFoundError(f"Product discount ceiling with id {ceiling_id} not found.")
        return ceiling

    @classmethod
    def list(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> ProductDiscountCeilingListResponse:
        query = db.query(ProductDiscountCeiling).filter(ProductDiscountCeiling.company_id == company_id)
        if product_id:
            query = query.filter(ProductDiscountCeiling.product_id == product_id)
        if is_active is not None:
            query = query.filter(ProductDiscountCeiling.is_active == is_active)

        total = query.count()
        items = query.order_by(ProductDiscountCeiling.created_at.desc()).offset(skip).limit(limit).all()

        return ProductDiscountCeilingListResponse(
            items=[ProductDiscountCeilingResponse.model_validate(item) for item in items],
            total=total,
        )

    @classmethod
    def update(
        cls,
        db: Session,
        ceiling_id: uuid.UUID,
        company_id: uuid.UUID,
        payload: ProductDiscountCeilingUpdate,
        current_user: Optional[User] = None,
    ) -> ProductDiscountCeiling:
        ceiling = cls.get(db, ceiling_id, company_id)

        if payload.max_discount_percentage is not None:
            if payload.max_discount_percentage < 0 or payload.max_discount_percentage > 100:
                raise ValidationError("Maximum discount percentage must be between 0 and 100 percent.")
            ceiling.max_discount_percentage = payload.max_discount_percentage

        if payload.is_active is not None and payload.is_active != ceiling.is_active:
            if payload.is_active:
                active_existing = (
                    db.query(ProductDiscountCeiling)
                    .filter(
                        ProductDiscountCeiling.company_id == company_id,
                        ProductDiscountCeiling.product_id == ceiling.product_id,
                        ProductDiscountCeiling.is_active == True,
                        ProductDiscountCeiling.id != ceiling.id,
                    )
                    .first()
                )
                if active_existing:
                    raise ConflictError(
                        "Cannot activate ceiling: another active discount ceiling already exists for this product."
                    )
            ceiling.is_active = payload.is_active

        if payload.effective_from is not None:
            ceiling.effective_from = payload.effective_from
        if payload.effective_until is not None:
            ceiling.effective_until = payload.effective_until

        if ceiling.effective_until and ceiling.effective_until < ceiling.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        db.commit()
        db.refresh(ceiling)

        if current_user:
            audit = AuditLog(
                action="PRODUCT_DISCOUNT_CEILING_UPDATED",
                resource_type="product_discount_ceiling",
                resource_id=str(ceiling.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "product_id": str(ceiling.product_id),
                    "max_discount_percentage": float(ceiling.max_discount_percentage),
                    "is_active": ceiling.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return ceiling

    @classmethod
    def deactivate(
        cls,
        db: Session,
        ceiling_id: uuid.UUID,
        company_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> ProductDiscountCeiling:
        ceiling = cls.get(db, ceiling_id, company_id)
        ceiling.is_active = False
        db.commit()
        db.refresh(ceiling)

        if current_user:
            audit = AuditLog(
                action="PRODUCT_DISCOUNT_CEILING_DEACTIVATED",
                resource_type="product_discount_ceiling",
                resource_id=str(ceiling.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "product_id": str(ceiling.product_id),
                    "is_active": False,
                },
            )
            db.add(audit)
            db.commit()

        return ceiling


# ==============================================================================
# Phase 105: Sales Rep Authority Limit Service
# ==============================================================================

class SalesRepAuthorityLimitService:
    @classmethod
    def create(
        cls,
        db: Session,
        company_id: uuid.UUID,
        payload: SalesRepAuthorityLimitCreate,
        current_user: Optional[User] = None,
    ) -> SalesRepAuthorityLimit:
        if payload.max_authorized_discount < 0 or payload.max_authorized_discount > 100:
            raise ValidationError("Maximum authorized discount must be between 0 and 100 percent.")
        if payload.effective_until and payload.effective_until < payload.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        # Ensure target user exists and belongs to company
        target_user = (
            db.query(User)
            .filter(User.id == payload.user_id, User.company_id == company_id)
            .first()
        )
        if not target_user:
            raise NotFoundError(f"User with id {payload.user_id} not found in this company.")

        # Prevent duplicate active authority records
        if payload.is_active:
            active_existing = (
                db.query(SalesRepAuthorityLimit)
                .filter(
                    SalesRepAuthorityLimit.company_id == company_id,
                    SalesRepAuthorityLimit.user_id == payload.user_id,
                    SalesRepAuthorityLimit.is_active == True,
                )
                .first()
            )
            if active_existing:
                raise ConflictError(
                    f"An active authority limit already exists for user '{target_user.email}'. "
                    "Deactivate or update the existing authority limit before creating a new active record."
                )

        limit_record = SalesRepAuthorityLimit(
            company_id=company_id,
            user_id=payload.user_id,
            max_authorized_discount=payload.max_authorized_discount,
            is_active=payload.is_active,
            effective_from=payload.effective_from,
            effective_until=payload.effective_until,
            created_by_id=current_user.id if current_user else None,
        )
        db.add(limit_record)
        db.commit()
        db.refresh(limit_record)

        if current_user:
            audit = AuditLog(
                action="SALES_REP_AUTHORITY_LIMIT_CREATED",
                resource_type="sales_rep_authority_limit",
                resource_id=str(limit_record.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "target_user_id": str(target_user.id),
                    "target_user_email": target_user.email,
                    "max_authorized_discount": float(limit_record.max_authorized_discount),
                    "is_active": limit_record.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return limit_record

    @classmethod
    def get(cls, db: Session, limit_id: uuid.UUID, company_id: uuid.UUID) -> SalesRepAuthorityLimit:
        limit_record = (
            db.query(SalesRepAuthorityLimit)
            .filter(SalesRepAuthorityLimit.id == limit_id, SalesRepAuthorityLimit.company_id == company_id)
            .first()
        )
        if not limit_record:
            raise NotFoundError(f"Sales Rep authority limit with id {limit_id} not found.")
        return limit_record

    @classmethod
    def list(
        cls,
        db: Session,
        company_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> SalesRepAuthorityLimitListResponse:
        query = db.query(SalesRepAuthorityLimit).filter(SalesRepAuthorityLimit.company_id == company_id)
        if user_id:
            query = query.filter(SalesRepAuthorityLimit.user_id == user_id)
        if is_active is not None:
            query = query.filter(SalesRepAuthorityLimit.is_active == is_active)

        total = query.count()
        items = query.order_by(SalesRepAuthorityLimit.created_at.desc()).offset(skip).limit(limit).all()

        return SalesRepAuthorityLimitListResponse(
            items=[SalesRepAuthorityLimitResponse.model_validate(item) for item in items],
            total=total,
        )

    @classmethod
    def update(
        cls,
        db: Session,
        limit_id: uuid.UUID,
        company_id: uuid.UUID,
        payload: SalesRepAuthorityLimitUpdate,
        current_user: Optional[User] = None,
    ) -> SalesRepAuthorityLimit:
        limit_record = cls.get(db, limit_id, company_id)

        if payload.max_authorized_discount is not None:
            if payload.max_authorized_discount < 0 or payload.max_authorized_discount > 100:
                raise ValidationError("Maximum authorized discount must be between 0 and 100 percent.")
            limit_record.max_authorized_discount = payload.max_authorized_discount

        if payload.is_active is not None and payload.is_active != limit_record.is_active:
            if payload.is_active:
                active_existing = (
                    db.query(SalesRepAuthorityLimit)
                    .filter(
                        SalesRepAuthorityLimit.company_id == company_id,
                        SalesRepAuthorityLimit.user_id == limit_record.user_id,
                        SalesRepAuthorityLimit.is_active == True,
                        SalesRepAuthorityLimit.id != limit_record.id,
                    )
                    .first()
                )
                if active_existing:
                    raise ConflictError(
                        "Cannot activate authority limit: another active authority limit already exists for this user."
                    )
            limit_record.is_active = payload.is_active

        if payload.effective_from is not None:
            limit_record.effective_from = payload.effective_from
        if payload.effective_until is not None:
            limit_record.effective_until = payload.effective_until

        if limit_record.effective_until and limit_record.effective_until < limit_record.effective_from:
            raise ValidationError("effective_until cannot precede effective_from.")

        db.commit()
        db.refresh(limit_record)

        if current_user:
            audit = AuditLog(
                action="SALES_REP_AUTHORITY_LIMIT_UPDATED",
                resource_type="sales_rep_authority_limit",
                resource_id=str(limit_record.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "target_user_id": str(limit_record.user_id),
                    "max_authorized_discount": float(limit_record.max_authorized_discount),
                    "is_active": limit_record.is_active,
                },
            )
            db.add(audit)
            db.commit()

        return limit_record

    @classmethod
    def deactivate(
        cls,
        db: Session,
        limit_id: uuid.UUID,
        company_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> SalesRepAuthorityLimit:
        limit_record = cls.get(db, limit_id, company_id)
        limit_record.is_active = False
        db.commit()
        db.refresh(limit_record)

        if current_user:
            audit = AuditLog(
                action="SALES_REP_AUTHORITY_LIMIT_DEACTIVATED",
                resource_type="sales_rep_authority_limit",
                resource_id=str(limit_record.id),
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "target_user_id": str(limit_record.user_id),
                    "is_active": False,
                },
            )
            db.add(audit)
            db.commit()

        return limit_record
